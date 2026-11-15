from flask import render_template

from ADTC import app


@app.route("/")
def index():
    return render_template("index.html")
