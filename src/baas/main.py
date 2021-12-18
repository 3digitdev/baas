import base64
import bcrypt
import os
import sys
import time
import uvicorn

from datetime import datetime
from http import HTTPStatus
from pony.orm import OperationalError
from pony.orm.core import ObjectNotFound, db_session
from sanic import Sanic, json, Request
from sanic.response import empty
from uuid import uuid4

from .models import Bool, User, db

db_config = {
    "provider": "mysql",
    "user": os.environ["SQL_USER"],
    "passwd": os.environ["SQL_PASSWORD"],
    "host": os.environ["SQL_HOST"],
    "db": os.environ["SQL_DB"],
}

app = Sanic("BaaS API")
attempts = 0
connected = False
while attempts < 5:
    try:
        db.bind(**db_config)
        connected = True
        break
    except OperationalError as e:
        print(e)
        attempts += 1
        time.sleep(2)
if not connected:
    print("ERROR:  Unable to connect to DB after 10s")
    sys.exit(1)
db.generate_mapping(create_tables=True)
# Setup event for auto-clearing users based on inactivity
db.execute(
    "CREATE EVENT IF NOT EXISTS expire_user "
    "ON SCHEDULE EVERY 1 DAY COMMENT "
    "'Each day, clears out Users that have not been accessed in 1 month' "
    "DO DELETE FROM user WHERE user.last_accessed < DATE_SUB(NOW(), INTERVAL 1 MONTH);"
)
app.ctx.db = db


def bool_param(request: Request, param: str) -> bool:
    """Helper function for boolean flag query params"""
    return request.args.get(param, "false").lower() == "true"


@app.on_request
def auth(request: Request):
    if "users" in request.path:
        return
    header_error = json(
        {"error": "Invalid Authorization Header"}, status=HTTPStatus.UNAUTHORIZED
    )
    head = request.headers.get("Authorization", "")
    if "Basic " not in head:
        return header_error
    key, secret = base64.b64decode(head.split(" ", 1)[1]).decode("utf-8").split(":", 1)
    try:
        with db_session:
            user = User.get(key=key)
            if not bcrypt.checkpw(secret.encode("utf-8"), user.secret):
                return header_error
            # update last access date to track for expiration
            # note that this only happens if they successfully authenticated!
            user.last_accessed = datetime.now()
            app.ctx.user = user.id
    except (ObjectNotFound, ValueError):
        return header_error


@app.post("/users")
def create_user(request: Request):
    """
    SQL Event:
    CREATE EVENT expire_user
        ON SCHEDULE EVERY 1 DAY
        COMMENT 'Each day, clears out Users that have not been accessed in 1 month'
        DO
            DELETE FROM user WHERE user.last_used < DATE_SUB(NOW(), INTERVAL 1 MONTH);
    """
    if "secret" not in request.json:
        return json(
            {"error": "must provide a secret like {'secret': 'hunter2'}"},
            status=HTTPStatus.BAD_REQUEST,
        )
    salt = bcrypt.gensalt()
    with db_session:
        user = User(
            key=str(uuid4()),
            secret=bcrypt.hashpw(request.json["secret"].encode("utf-8"), salt),
        )
    return json(
        {
            "key": user.key,
            "warning": "IF YOU LOSE THIS KEY, YOU WILL BE UNABLE TO RECOVER YOUR ACCOUNT.",
        }
    )


@app.get("/bools")
def list_bools(request: Request):
    with db_session:
        bools = [b.as_json() for b in User[app.ctx.user].bools]
    return json({"bools": bools})


@app.post("/bools")
def create_bool(request: Request):
    invalid_body_msg = (
        "Request body must be in the format {'name': 'foo', 'value': true}"
    )
    if "name" not in request.json or "value" not in request.json:
        return json({"error": invalid_body_msg}, status=HTTPStatus.BAD_REQUEST)
    name = request.json["name"]
    value = request.json["value"]
    if not isinstance(name, str) or not isinstance(value, bool):
        return json({"error": invalid_body_msg}, status=HTTPStatus.BAD_REQUEST)
    with db_session:
        boolean = Bool(name=name, value=value, owner=app.ctx.user)
    if bool_param(request, "simple"):
        return json(boolean.as_json(True))
    return json({"bool": boolean.as_json()})


@app.get("/bools/<bool_id:int>")
def get_bool(request: Request, bool_id: int):
    try:
        with db_session:
            boolean = Bool[bool_id]
            if boolean not in User[app.ctx.user].bools:
                raise AttributeError
        if bool_param(request, "simple"):
            return json(boolean.as_json(True))
        return json({"bool": boolean.as_json()})
    except (ObjectNotFound, AttributeError):
        return json(
            {"error": f"Could not find boolean with ID '{bool_id}'"},
            status=HTTPStatus.NOT_FOUND,
        )


@app.post("/bools/<bool_id:int>")
def toggle_bool(request: Request, bool_id: int):
    try:
        with db_session:
            boolean = Bool[bool_id]
            if boolean not in User[app.ctx.user].bools:
                raise AttributeError
            boolean.set(value=(not boolean.value))
        if bool_param(request, "simple"):
            return json(boolean.as_json(True))
        return json({"bool": boolean.as_json()})
    except (ObjectNotFound, AttributeError):
        return json(
            {"error": f"Could not find boolean with ID '{bool_id}'"},
            status=HTTPStatus.NOT_FOUND,
        )


@app.delete("/bools/<bool_id:int>")
@db_session
def delete_bool(request: Request, bool_id: int):
    try:
        boolean = Bool[bool_id]
        if boolean not in User[app.ctx.user].bools:
            raise AttributeError
        Bool[bool_id].delete()
    except (ObjectNotFound, AttributeError):
        pass
    return empty(status=HTTPStatus.NO_CONTENT)


def start():
    uvicorn.run("baas.main:app", host="0.0.0.0", port=os.environ["PORT"], workers=4)
