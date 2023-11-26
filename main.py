from bottle import route, run, jinja2_view as view, app, request
from pg8000.dbapi import connect


class DatabaseMiddleware:
    def __init__(self, application):
        self.application = application

    def __call__(self, environ, response):
        environ["bottle.request.ext.database"] = connect(
            database="irga", user="tools", password="tools"
        )
        return self.application(environ, response)


tools = DatabaseMiddleware(app())


@route("/")
@view("index.html")
def index():
    cursor = request.database.cursor()
    cursor.execute("SELECT * FROM toolbox.tool")
    return {"tools": cursor.fetchall()}


run(app=tools, host="localhost", port=8080, reloader=True, debug=True)
