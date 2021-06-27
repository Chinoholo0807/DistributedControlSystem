from flask import Flask, config
import config
from flask_cors import CORS

app = Flask(__name__)
app.config.from_object(config)
CORS(app, resources=r'/*')
