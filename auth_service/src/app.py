import os

from flask import Flask

from .database import init_database
from .routes import auth_routes


app: Flask = Flask(__name__)
init_database()
app.register_blueprint(auth_routes)


@app.get("/hello")
def hello() -> str:
    return "hello world"

if __name__ == "__main__":
    port: int = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)
