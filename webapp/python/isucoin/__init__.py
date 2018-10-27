from __future__ import annotations

import os, sys

sys.path.append(os.path.dirname(__file__) + "/vendor")

import datetime
import json
import time
import flask

from . import model
from isucoin.db import *


app = flask.Flask(__name__)
app.secret_key = "tonymoris"



def _json_default(v):
    if isinstance(v, datetime.datetime):
        return v.strftime("%Y-%m-%dT%H:%M:%S+09:00")

    to_json = getattr(v, "to_json")
    if to_json:
        return to_json()

    raise TypeError(f"Unknown type for json_dumps. {v!r} (type: {type(v)})")


def json_dumps(data, **kwargs):
    return json.dumps(data, default=_json_default, **kwargs)


def jsonify(*args, **kwargs):
    if args and kwargs:
        raise TypeError("jsonify() behavior undefined when passed both args and kwargs")
    if len(args) == 1:
        data = args[0]
    else:
        data = args or kwargs

    return app.response_class(
        json_dumps(data, indent=None, separators=(",", ":")).encode(),
        mimetype="application/json; charset=utf-8",
    )


def error_json(code: int, msg):
    resp = jsonify(code=code, err=str(msg))
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.status_code = code
    return resp


@app.errorhandler(Exception)
def errohandler(err):
    app.logger.exception("FAIL")
    return error_json(500, err)


@app.before_request
def before_request():
    user_id = flask.session.get("user_id")
    if user_id is None:
        flask.g.current_user = None
        return

    user = model.get_user_by_id(get_dbconn(), user_id)
    if user is None:
        flask.session.clear()
        return error_json(404, "セッションが切断されました")

    flask.g.current_user = user



@app.route("/")
def index():
    return app.send_static_file("index.html")


@app.route("/initialize", methods=("POST",))
def initialize():
    with transaction() as db:
        model.init_benchmark(db)

        for k in ("bank_endpoint", "bank_appid", "log_endpoint", "log_appid"):
            v = flask.request.form.get(k)
            model.set_setting(db, k, v)
    time.sleep(3)
    return jsonify({})


@app.route("/signup", methods=("POST",))
def signup():
    req = flask.request
    name = req.form["name"]
    bank_id = req.form["bank_id"]
    password = req.form["password"]

    if not (name and bank_id and password):
        return error_json(400, "all parameters are required")

    try:
        with transaction() as db:
            model.signup(db, name, bank_id, password)
    except model.BankUserNotFound as e:
        return error_json(404, e.msg)
    except model.BankUserConflict as e:
        return error_json(409, e.msg)

    return jsonify({})


@app.route("/signin", methods=("POST",))
def signin():
    req = flask.request
    bank_id = req.form["bank_id"]
    password = req.form["password"]

    if not (bank_id and password):
        return error_json(400, "all parameters are required")

    db = get_dbconn()
    try:
        user = model.login(db, bank_id, password)
    except model.UserNotFound as e:
        # TODO: 失敗が多いときに403を返すBanの仕様に対応
        return error_json(404, e.msg)

    flask.session["user_id"] = user.id
    return jsonify(id=user.id, name=user.name)


@app.route("/signout", methods=("POST",))
def signout():
    flask.session.clear()
    return jsonify({})


@app.route("/info")
def info():
    res = {}
    db = get_dbconn()
    cursor = flask.request.args.get("cursor")
    last_trade_id = 0
    lt = None

    if cursor:
        try:
            last_trade_id = int(cursor)
        except ValueError as e:
            app.logger.exception(f"failed to parse cursor ({cursor!r})")
        if last_trade_id > 0:
            trade = model.get_trade_by_id(db, last_trade_id)
            if trade:
                lt = trade.created_at

    latest_trade = model.get_latest_trade(db)
    res["cursor"] = latest_trade.id

    user = flask.g.current_user
    if user:
        res["traded_orders"] = model.get_orders_by_userid_and_lasttradeid(db, user.id, last_trade_id)

    from_t = base_time - datetime.timedelta(seconds=300)
    if lt and lt > from_t:
        from_t = lt.replace(microsecond=0)
    res["chart_by_sec"] = model.get_candlestic_data(db, from_t, type='sec')

    from_t = base_time - datetime.timedelta(minutes=300)
    if lt and lt > from_t:
        from_t = lt.replace(second=0, microsecond=0)
    res["chart_by_min"] = model.get_candlestic_data(db, from_t, type='min')

    from_t = base_time - datetime.timedelta(hours=48)
    if lt and lt > from_t:
        from_t = lt.replace(minute=0, second=0, microsecond=0)
    res["chart_by_hour"] = model.get_candlestic_data(db, from_t, type='hour')

    lowest_sell_order = model.get_lowest_sell_order(db)
    if lowest_sell_order:
        res["lowest_sell_price"] = lowest_sell_order.price

    highest_buy_order = model.get_highest_buy_order(db)
    if highest_buy_order:
        res["highest_buy_price"] = highest_buy_order.price

    # TODO: trueにするとシェアボタンが有効になるが、アクセスが増えてヤバイので一旦falseにしておく
    res["enable_share"] = True

    resp = jsonify(res)
    return resp


@app.route("/orders")
def orders():
    user = flask.g.current_user
    if user is None:
        return error_json(401, "Not authenticated")

    db = get_dbconn()
    orders = model.get_orders_by_userid(db, user.id)
    return jsonify(orders)


@app.route("/orders", methods=("POST",))
def add_order():
    user = flask.g.current_user
    if user is None:
        return error_json(401, "Not authenticated")

    amount = int(flask.request.form["amount"])
    price = int(flask.request.form["price"])
    type = flask.request.form["type"]

    try:
        with transaction() as db:
            order = model.add_order(db, type, user.id, amount, price)
    except model.CreditInsufficient as e:
        return error_json(400, e.msg)

    db = get_dbconn()
    trade_chance = model.has_trade_chance_by_order(db, order.id)
    if trade_chance:
        try:
            model.run_trade(db)
        except Exception:  # トレードに失敗してもエラーにはしない
            app.logger.exception("run_trade failed")

    return jsonify(id=order.id)


@app.route("/order/<int:order_id>", methods=("DELETE",))
def delete_order(order_id):
    user = flask.g.current_user
    if user is None:
        return error_json(401, "Not authenticated")

    try:
        with transaction() as db:
            model.delete_order(db, user.id, order_id, "canceled")
    except (model.OrderNotFound, model.OrderAlreadyClosed) as e:
        error_json(404, e.msg)

    return jsonify(id=order_id)
