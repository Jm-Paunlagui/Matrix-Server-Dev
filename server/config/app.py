from flask import Flask
from flask_bcrypt import Bcrypt
from flask_cors import CORS
import os

from keras.models import load_model

# Create the Flask app and load the config file
app = Flask(__name__)

# Enable CORS for all domains on all routes (for development purposes)
CORS(app, supports_credentials=True)
bcrypt = Bcrypt(app)


# @desc: This is the main route of the application.
def run():
    app.run(host='0.0.0.0', debug=False, port=os.environ.get('PORT', 8080))


# @desc: The add_url_rule() method is used to add a new rule to the list of URL rules.
def add_url_rule(param, view_func, methods):
    return app.add_url_rule(param, view_func=view_func, methods=methods)


# @desc: This method pushes the application context to the top of the stack.
app.app_context().push()
