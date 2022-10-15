from app import app
from flask_jwt_extended import JWTManager

# @desc: Initialize the secret key for the JWT token
app.config['SECRET_KEY'] = "f9a0b8d7c6a5b4e3d2c1f8g7h6j5k4l3m2n1o0p9q8r7s6t5u4v3w2x1y0z9a8b7c6d5e4f3g2h1i0j9k8l7m6n5" \
                           "o4p3q2r1s0t9u8v7w6x5y4z3a2b1c0d9e8f7g6h5i4j3k2l1m0n9o8p7q6r5s4t3u2v1w0x9y8z7a1b2c3d4e5f6" \
                           "g7h8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0" \
                           "z1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4" \
                           "r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8" \
                           "j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i"

# @desc: Initialize the Flask-JWT-Extended extension and set the token location to cookies
jwt = JWTManager(app)
