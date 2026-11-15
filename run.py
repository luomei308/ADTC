import os

from ADTC import app


def runserver():
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", 1237))
    app.run(host=host, port=port)


if __name__ == "__main__":
    runserver()
