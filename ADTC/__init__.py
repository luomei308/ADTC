from flask import Flask
from flask_restful import Api

app = Flask(__name__)

api = Api(app)

app.config.from_object('ADTC.settings')

app.url_map.strict_slashes = False

import ADTC.core
import ADTC.controllers
import ADTC.ajax

