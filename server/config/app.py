from flask import Flask, session

from flask_bcrypt import Bcrypt
from flask_cors import CORS
import os
import redis

from keras.models import load_model

# Create the Flask app and load the config file
app = Flask(__name__)

SESSION_TYPE = "redis"
SESSION_PERMANENT = False
SESSION_USE_SIGNER = True
SESSION_REDIS = redis.from_url("redis://127.0.0.1:6379")
app.secret_key = "f9a0b8d7c6a5b4e3d2c1f8g7h6j5k4l3m2n1o0p9q8r7s6t5u4v3w2x1y0z9a8b7c6d5e4f3g2h1i0j9k8l7m6n5o4p3q2r1" \
                 "s0t9u8v7w6x5y4z3a2b1c0d9e8f7g6h5i4j3k2l1m0n9o8p7q6r5s4t3u2v1w0x9y8z7a1b2c3d4e5f6g7h8j9k0l1m2n3o4" \
                 "p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0z1a2b3c4d5e6f7g8h9i0j1k2" \
                 "l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0" \
                 "h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8" \
                 "d9e0f1g2h3i"
app.config.from_object(__name__)

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
