
import re
import hashlib

import mysql.connector

from datetime import timedelta, datetime
from flask import jsonify, request
from flask_jwt_extended import create_access_token
from config.app import app

# @desc MySQL function to get connected and execute queries
conn = mysql.connector.connect(
    host="localhost", user="root", password="", database="production_saer")
cursor = conn.cursor()


# @desc test route to check if the server is running
@app.route('/test', methods=['GET'])
def test():
    # get user from database
    cursor.execute("SELECT * FROM `00_user`")
    user = cursor.fetchall()
    if user:
        return jsonify({"message": "User found", "user": user}), 200
    return jsonify({"message": "Create a user"}), 200


# Authentication
@app.route('/login', methods=['POST'])
def auth():
    if request.is_json:
        username = request.json['username']
        password = request.json['password']

        cursor.execute("SELECT `user_id`, `username`, `password`, `role` FROM `00_user` WHERE `username` = %s",
                       (username,))
        is_user = cursor.fetchone()
        if not is_user:
            return jsonify({'status': 'error', 'message': 'User not found :<'})
        if is_user[1] == password:
            if is_user[2] == 5:
                return jsonify({'status': 'success', 'message': 'Login successful',
                                'token': create_access_token(identity={
                                    'username': username, 'role': is_user[2], 'id_number': is_user[0], 'path': 'admin'
                                }, expires_delta=timedelta(days=14))})
            if is_user[2] == 4:
                return jsonify({'status': 'success', 'message': 'Login successful',
                                'token': create_access_token(identity={
                                    'username': username, 'role': is_user[2], 'id_number': is_user[0], 'path': 'admin'
                                }, expires_delta=timedelta(days=14))})
            if is_user[2] == 3:
                return jsonify({'status': 'success', 'message': 'Login successful',
                                'token': create_access_token(identity={
                                    'username': username, 'role': is_user[2], 'id_number': is_user[0],
                                    'path': 'professor'}, expires_delta=timedelta(days=14))})
            return jsonify({'status': 'error', 'message': 'Access denied, Unauthorized user'})
        else:
            return jsonify({'status': 'error', 'message': 'Invalid username or password'})
    else:
        return jsonify({'status': 'error', 'message': 'Invalid request'})


# Validation of create and update user
def validate_user(email, first_name, last_name, username, password, role):
    # if email, name, username, password, role is empty, return error message
    if email == '' or first_name == '' or last_name == '' or username == '' or password == '' or role == '':
        return jsonify({'status': 'error', 'message': 'Please fill in all the fields'})
    # validate the email using the regex
    if not re.match(r'[^@]+@[^@]+\.[^@]+', email):
        return jsonify({'status': 'error', 'message': 'Invalid email'})

    # Check if the name is invalid using the regex
    if not re.match(r"[a-zA-Z]+", first_name) or not re.match(r"[a-zA-Z]+", last_name):
        return jsonify({'status': 'error', 'message': 'Invalid name'})

    # Check the length of the username if it is less than 5 characters or more than 20 characters
    if len(username) < 5 or len(username) > 20:
        return jsonify({'status': 'error', 'message': 'Username must be between 5 and 20 characters'})

    # Check the length of the password if it is less than 5 characters or more than 20 characters
    if len(password) < 8 or len(password) > 20:
        return jsonify({'status': 'error', 'message': 'Password must be between 8 and 20 characters'})
    # Check if the password is weak using the regex
    if not re.match(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!#%*?&]{8,20}$", password):
        return jsonify({'status': 'error', 'message': 'Password must be alphanumeric'})
    # Check if the role is valid
    if role != '3' and role != '4' and role != '5':
        return jsonify({'status': 'error', 'message': 'Invalid role'})
    return True


# @jwt_required()
@app.route('/register', methods=['POST'])
def register():
    if request.form:
        email = request.form['email']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        # Gravatar image url of the user
        image = 'https://www.gravatar.com/avatar/' + \
            hashlib.md5(email.encode('utf-8')).hexdigest() + '?s=600&d=retro'
        # image = request.files['image']
        # save the image to the server and get the path of the image to be saved in the database later
        # image_path = save_image(image)
        now = datetime.now()

        # check if one of them exists
        cursor.execute(
            "SELECT * FROM `00_user` WHERE username = %s OR email = %s", (username, email))
        is_exist = cursor.fetchall()
        if is_exist:
            return jsonify({'status': 'error', 'message': 'Username or email already exists'})
        # validate the user
        validation = validate_user(
            email, first_name, last_name, username, password, role)
        # if validation is true, insert the user to the database
        if validation is True:
            cursor.execute("INSERT INTO `00_user` (`email`, `first_name`, `last_name`, `username`, `password`, "
                           "`role`, `gravatar`, `date_created`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                           (email, first_name, last_name, username, password, role, image, now))
            conn.commit()
            return jsonify({'status': 'success', 'message': 'User registered successfully'})
        return validation
    else:
        return jsonify({'status': 'something went wrong'})


# Get User Profile
@app.route('/users-profile/<id_number>', methods=['GET'])
def user_profile(id_number):
    cursor.execute(
        "SELECT * FROM `00_user` WHERE `user_id` = %s", (id_number,))
    user_ = cursor.fetchall()

    user_info = []
    if user_:
        for _user in user_:
            user_info.append({
                'user_id': _user[0],
                'email': _user[1],
                'first_name': _user[2],
                'last_name': _user[3],
                'username': _user[4],
                'password': _user[5],
                'role': _user[6],
                'gravatar': _user[7],
                'date_created': _user[8]
            })
        return jsonify({'status': 'success', 'message': 'User profile retrieved successfully', 'user': user_info})
    return jsonify({'status': 'error', 'message': 'User profile not found'})


# Get user profile by username
@app.route('/users-profile-username/<username>', methods=['GET'])
def user_profile_username(username):
    cursor.execute(
        "SELECT * FROM `00_user` WHERE `username` = %s", (username,))
    user_ = cursor.fetchall()

    user_info = []
    if user_:
        for _user in user_:
            user_info.append({
                'user_id': _user[0],
                'email': _user[1],
                'first_name': _user[2],
                'last_name': _user[3],
                'username': _user[4],
                'password': _user[5],
                'role': _user[6],
                'gravatar': _user[7],
                'date_created': _user[8]
            })
        return jsonify({'status': 'success', 'message': 'User profile retrieved successfully', 'user': user_info})
    return jsonify({'status': 'error', 'message': 'User profile not found'})
