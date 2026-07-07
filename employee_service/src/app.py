import os

from flask import Flask

from .routes import auth_routes

app: Flask = Flask(__name__)
app.register_blueprint(auth_routes)

if __name__ == "__main__":
    port: int = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)
