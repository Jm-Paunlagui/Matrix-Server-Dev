from flask import Flask

from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_mail import Mail
from authlib.jose import JsonWebSignature
import os
import redis
import mysql.connector

from keras.models import load_model

# Create the Flask app and load the config file
app = Flask(__name__)

# @desc: The redis configuration
SESSION_TYPE = "redis"
SESSION_PERMANENT = False
SESSION_USE_SIGNER = True
SESSION_REDIS = redis.from_url("redis://127.0.0.1:6379")

# @desc: Email configuration
# @TODO: set env variables for email and password
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config["MAIL_USE_SSL"] = True
app.config["MAIL_USE_TLS"] = False
app.config["MAIL_PORT"] = 465
app.config["MAIL_USERNAME"] = os.environ.get("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD")

# @desc: The flask mail instance
mail = Mail(app)

# @desc: Secret key of the application
app.secret_key = os.environ.get("SECRET_KEY")

# @desc: Config from object
app.config.from_object(__name__)

# Cross-Origin Resource Sharing configuration for the Flask app to allow requests from the client
CORS(app, supports_credentials=True,
     methods="GET,POST,PUT,DELETE,OPTIONS", origins=os.environ.get("DEV_URL"))

# @desc: The bcrypt instance
bcrypt = Bcrypt(app)

# @desc: The authlib JsonWebSignature instance
jws = JsonWebSignature()

# @desc: MySQL database connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="matrix"
)


# @desc: This is the main route of the application.
def run():
    app.run(host='0.0.0.0', debug=False, port=os.environ.get('PORT', 8080))


# @desc: The add_url_rule() method is used to add a new rule to the list of URL rules.
def add_url_rule(param, view_func, methods):
    return app.add_url_rule(param, view_func=view_func, methods=methods)


# @desc: This method pushes the application context to the top of the stack.
app.app_context().push()
