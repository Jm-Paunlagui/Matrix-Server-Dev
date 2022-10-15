import re
import hashlib

import mysql.connector

from datetime import timedelta
from flask import jsonify, request
from server.config.configurations import app

# @desc MySQL function to get connected and execute queries
conn = mysql.connector.connect(
    host="localhost", user="root", password="", database="matrix")
cursor = conn.cursor()


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
            elif is_user[2] == 4:
                return jsonify({'status': 'success', 'message': 'Login successful',
                                'token': create_access_token(identity={
                                    'username': username, 'role': is_user[2], 'id_number': is_user[0], 'path': 'admin'
                                }, expires_delta=timedelta(days=14))})
            elif is_user[2] == 3:
                return jsonify({'status': 'success', 'message': 'Login successful',
                                'token': create_access_token(identity={
                                    'username': username, 'role': is_user[2], 'id_number': is_user[0],
                                    'path': 'professor'}, expires_delta=timedelta(days=14))})
            else:
                return jsonify({'status': 'error', 'message': 'Access denied, Unauthorized user'})
        else:
            return jsonify({'status': 'error', 'message': 'Invalid username or password'})
    else:
        return jsonify({'status': 'error', 'message': 'Invalid request'})


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
    else:
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
    else:
        return jsonify({'status': 'error', 'message': 'User profile not found'})
