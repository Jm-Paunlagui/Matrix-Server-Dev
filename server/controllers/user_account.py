from flask import jsonify, request
from server.config.app import app
import server.controllers.helpers.input_validation as iv
import server.controllers.helpers.user_database_queries as dq
import mysql.connector
from datetime import datetime

# @desc: Connection to the database
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="matrix"
)
cursor = db.cursor(buffered=True)


# @desc: Timestamps
def timestamps():
    # @format: Day, Month, Year, @ Hour:Minute:Second
    return datetime.now().strftime("%A, %B %d, %Y @ %I:%M:%S %p")


# @desc: User registration route
@app.route('/signup', methods=['POST'])
def signup():
    if not request.is_json:
        return jsonify({"status": "error", "message": "Invalid request"})

    email = request.json['email']
    first_name = request.json['first_name']
    last_name = request.json['last_name']
    username = request.json['username']
    password = request.json['password']
    role = request.json['role']

    if not iv.validate_empty_fields(email, first_name, last_name, username, password, role):
        return jsonify({"status": "error", "message": "Please fill in all the fields"}), 400
    if not iv.validate_email(email):
        return jsonify({"status": "error", "message": "Invalid email address"}), 400
    if not iv.validate_username(username):
        return jsonify({"status": "error", "message": "Invalid username"}), 400
    if not iv.validate_password(password):
        return jsonify({"status": "error", "message": "Password must be alphanumeric "
                                                      "and contain at least one uppercase, one lowercase, "
                                                      "one number and one special character"}), 400
    if not iv.validate_text(first_name):
        return jsonify({"status": "error", "message": "Invalid first name"}), 400
    if not iv.validate_text(last_name):
        return jsonify({"status": "error", "message": "Invalid last name"}), 400
    if not iv.validate_number(role):
        return jsonify({"status": "error", "message": "Invalid role"}), 400

    # @desc: Check if the user's email exists
    if not dq.create_user(email, first_name, last_name, username, password, role):
        return jsonify({"status": "error", "message": "Email already exists"}), 409

    return jsonify({"status": "success", "message": "User account created successfully"}), 201


# @desc User authentication
@app.route("/authenticate", methods=["POST"])
def authenticate():
    if not request.is_json:
        return jsonify({"status": "error", "message": "Invalid request"})

    username = request.json["username"]
    password = request.json["password"]

    if not iv.validate_empty_fields(username, password):
        return jsonify({"status": "error", "message": "Please fill in all the fields"}), 400

    if not iv.validate_username(username) or not iv.validate_password(password):
        return jsonify({"status": "error", "message": "Not a valid username or password"}), 400

    if not dq.authenticate_user(username, password):
        return jsonify({"status": "error", "message": "Invalid username or password"}), 401

    return jsonify({"status": "success", "message": "User authenticated successfully",
                    "path": dq.redirect_to()}), 200


# @desc: Gets the authenticated user by id
@app.route("/get_user", methods=["GET"])
def get_authenticated_user():
    user = dq.authenticated_user()
    if not user:
        return jsonify({"status": "error", "message": "Unauthorized access"}), 401

    return jsonify({"status": "success", "message": "User retrieved successfully",
                    "user": {"id": user[0], "email": user[1], "first_name": user[2],
                              "last_name": user[3], "username": user[4], "password": user[5]
                             }}
                   ), 200


# @desc: Signs out the authenticated user by id and deletes the session
@app.route("/sign-out", methods=["GET"])
def signout():
    if not dq.remove_session():
        return jsonify({"status": "error", "message": "Session not found"}), 404

    return jsonify({"status": "success", "message": "User signed out successfully"}), 200


# @desc: Sends a password reset link to the user's email address
@app.route("/forgot-password", methods=["POST"])
def forgot_password():
    if not request.is_json:
        return jsonify({"status": "error", "message": "Invalid request"})

    email = request.json["email"]

    if not iv.validate_empty_fields(email):
        return jsonify({"status": "error", "message": "Please fill in all the fields"}), 400
    if not iv.validate_email(email):
        return jsonify({"status": "error", "message": "Invalid email address"}), 400

    if not dq.check_email_exists(email):
        return jsonify({"status": "error", "message": "Email address does not exist"}), 404

    # @desc: generates a new password and sends it to the user
    dq.password_reset_link(email)

    return jsonify({"status": "success", "message": "Password reset successfully, Please check your email"}), 200


# @desc: Resets the password of the user based on the token sent to the user's email address
@app.route("/reset-password/<token>", methods=["POST"])
def reset_password(token: str):
    if not request.is_json:
        return jsonify({"status": "error", "message": "Invalid request"})

    password = request.json["password"]

    if not iv.validate_empty_fields(password):
        return jsonify({"status": "error", "message": "Please fill in all the fields"}), 400
    if not iv.validate_password(password):
        return jsonify({"status": "error", "message": "Password must be alphanumeric "
                                                      "and contain at least one uppercase, one lowercase, "
                                                      "one number and one special character"}), 400

    if not dq.password_reset(token, password):
        return jsonify({"status": "error", "message": "Token session expired"}), 404

    # @desc: resets the password of the user
    dq.password_reset(password, token)

    return jsonify({"status": "success", "message": "Password reset successfully"}), 200

