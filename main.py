from bottle import run, jinja2_view as view, Bottle, request, HTTPResponse, Jinja2Template
from pg8000.dbapi import connect
from pg8000.exceptions import DatabaseError
from beaker.middleware import SessionMiddleware
import os

DIR = os.path.dirname(os.path.abspath(__file__))

SESSION_CONFIG = {
    "session.type": "file",
    "session.cookie_expires": 300,
    "session.data_dir": f"{DIR}/sessions",
    "session.auto": True,
}


app = Bottle()


@app.hook("before_request")
def authenticate():
    if request.path == "/":
        return

    session = request.environ.get("beaker.session")
    assert session is not None

    user = session.get("user", None)
    password = session.get("password", None)

    if session.get("login", None) is not None and request.auth:
        user, password = request.auth

    try:
        database = connect(database="irga", user=user or "", password=password or "")
    except DatabaseError:
        session.invalidate()
        session["login"] = True

        raise HTTPResponse(
            status=401, headers={"WWW-Authenticate": "Basic realm=tools"}
        )

    session["login"] = True
    session["user"] = user
    session["password"] = password
    request.environ["database"] = database


def current_user():
    session = request.environ.get("beaker.session")
    return session.get("user")


Jinja2Template.defaults = {
    "current_user": current_user
}


@app.route("/")
@view("index.html")
def dashboard():
    pass


@app.route("/login")
def login():
    raise HTTPResponse(status=302, headers={"Location": "/"})


@app.route("/logout")
def logout():
    session = request.environ.get("beaker.session")
    session.delete()
    raise HTTPResponse(status=302, headers={"Location": "/"})


@app.route("/list")
@view("list.html")
def list_tools():
    cursor = request.environ["database"].cursor()
    cursor.execute("SELECT * FROM toolbox.tool")
    return {"tools": cursor.fetchall()}


app = SessionMiddleware(app, SESSION_CONFIG)

run(app, port=8080, reloader=True, debug=True)
