from flask import jsonify, request
from server.config.app import app
import server.controllers.helpers.input_validation as iv
import server.controllers.helpers.database_queries as dq
import mysql.connector
from datetime import datetime


# @desc: Timestamps
def timestamps():
    # @format: Day, Month, Year, @ Hour:Minute:Second
    return datetime.now().strftime("%A, %B %d, %Y @ %I:%M:%S %p")


# global variables
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="matrix"
)
cursor = db.cursor(buffered=True)


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

    if dq.check_email_exists(email):
        return jsonify({"status": "error", "message": "Email address already exists"}), 409

    # @desc: inserting new user into database with hashed password
    dq.insert_user(email, first_name, last_name, username, password, role)

    return jsonify({"status": "success", "message": "User registered successfully"}), 201


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
        return jsonify({"status": "error", "message": "Unauthorized access"}), 401

    return jsonify({"status": "success", "message": "User authenticated successfully"}), 200
