from datetime import datetime

from itsdangerous import SignatureExpired
from itsdangerous.url_safe import URLSafeTimedSerializer

from server.config.app import app, bcrypt, mail, db
from flask import session
from flask_session import Session
from flask_mail import Message

from server.controllers.helpers.input_validation import validate_password
import random
import string

server_session = Session(app)


# @desc: Check if users email exists
def check_email_exists(email: str):
    cursor = db.cursor(buffered=True)
    cursor.execute("SELECT email "
                   "FROM `00_user` "
                   "WHERE email = %s", (email,))
    is_email = cursor.fetchone()
    cursor.close()
    if is_email:
        return True
    else:
        return False


# @desc Checks if user id exists
def check_user_id(user_id: int):
    cursor = db.cursor(buffered=True)
    cursor.execute("SELECT `user_id` "
                   "FROM `00_user` "
                   "WHERE user_id = %s", (user_id,))
    is_id = cursor.fetchone()
    cursor.close()
    if is_id:
        return True
    else:
        return False


# @desc: Password hasher checker function
def password_hash_check(hashed_password: str, password: str):
    if not bcrypt.check_password_hash(hashed_password, password):
        return False
    else:
        return True


# @desc: Password hasher function
def password_hasher(password: str):
    hashed_password = bcrypt.generate_password_hash(password)
    return hashed_password


# @desc: Timestamps
def timestamps():
    # @format: Day, Month, Year, @ Hour:Minute:Second
    return datetime.now().strftime("%A, %B %d, %Y @ %I:%M:%S %p")


# @desc: Creates a new user account
def create_user(email: str, first_name: str, last_name: str, username: str, password: str, role: int):
    cursor = db.cursor(buffered=True)

    # @desc: Check if the user's email exists
    if check_email_exists(email):
        return False

    # @desc: Hash the user's password before storing it in the database
    hashed_password = password_hasher(password)

    # @desc: Insert the user's data into the database
    cursor.execute("INSERT INTO `00_user` (`email`, `first_name`, `last_name`, "
                   "`username`, `password`, `role`, `date_created`) "
                   "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                   (email, first_name, last_name, username, hashed_password, role, ""))

    # @desc: Commit the changes to the database and close the cursor
    db.commit()
    cursor.close()

    return True


# @desc: Flags delete the user's account based on the user's id
def delete_user(user_id: int):
    cursor = db.cursor(buffered=True)

    # @desc: Check if the user's id exists
    if not check_user_id(user_id):
        return False

    # @desc: Delete the user's account by setting the user's flag_deleted to 1
    cursor.execute("UPDATE `00_user` "
                   "SET flag_deleted = 1 "
                   "WHERE user_id = %s", (user_id,))

    # @desc: Commit the changes to the database and close the cursor
    db.commit()
    cursor.close()

    return True


# @desc: Permanently deletes the user's account based on the user's id
def delete_user_permanently(user_id: int):
    cursor = db.cursor(buffered=True)

    # @desc: Check if the user's id exists
    if not check_user_id(user_id):
        return False

    # @desc: Delete the user's account by setting the user's flag_deleted to 1
    cursor.execute("DELETE FROM `00_user` "
                   "WHERE user_id = %s", (user_id,))

    # @desc: Commit the changes to the database and close the cursor
    db.commit()
    cursor.close()

    return True


# @desc: Lists the flagged deleted users
def read_flagged_deleted_users():
    cursor = db.cursor(buffered=True)
    cursor.execute("SELECT `user_id`, `email`, `first_name`, `last_name`, `username`, `role`, `date_created` "
                   "FROM `00_user` "
                   "WHERE flag_deleted = 1")
    users = cursor.fetchall()
    cursor.close()

    if users:
        return users
    else:
        return False


# @desc: Restores the user's account based on the user's id
def restore_user(user_id: int):
    cursor = db.cursor(buffered=True)

    # @desc: Check if the user's id exists
    if not check_user_id(user_id):
        return False

    # @desc: Restore the user's account by setting the user's flag_deleted to 0
    cursor.execute("UPDATE `00_user` "
                   "SET flag_deleted = 0 "
                   "WHERE user_id = %s", (user_id,))

    # @desc: Commit the changes to the database and close the cursor
    db.commit()
    cursor.close()

    return True


# @desc: For user authentication
def authenticate_user(username: str, password: str):
    cursor = db.cursor(buffered=True)

    cursor.execute(
        "SELECT `user_id`,`username`, `password` "
        "FROM `00_user` "
        "WHERE username = %s", (username,))
    user = cursor.fetchone()
    cursor.close()

    # @desc: Check if the user exists
    if user is None:
        return False

    # @desc: Check if the user's password is correct
    if not bcrypt.check_password_hash(user[2], password) or user[1] != username:
        return False

    #
    session['user_id'] = user[0]

    return True


# @desc: Gets the user's id
def authenticated_user():
    cursor = db.cursor(buffered=True)

    # @desc: Get the user's session
    user_id = session.get('user_id')

    # @desc: Check if the user's session exists
    if user_id is None:
        return False

    # @desc: Get the user's data
    cursor.execute(
        "SELECT `user_id`, `email`, `first_name`, `last_name`, `username`, `password` "
        "FROM `00_user` "
        "WHERE user_id = %s", (user_id,))

    # @desc: Fetch the user's data from the database and close the cursor
    user = cursor.fetchone()
    cursor.close()

    return user


# @desc: Gets the user's role from the database and redirects to the appropriate page
# @desc: Gets the user's role from the database and redirects to the appropriate page
def redirect_to():
    cursor = db.cursor(buffered=True)

    # @desc: Get the user's session
    user_id = session.get('user_id')
    cursor.execute(
        "SELECT `role` "
        "FROM `00_user` "
        "WHERE user_id = %s", (user_id,))

    # @desc: Fetch the user's data from the database and close the cursor
    role = cursor.fetchone()
    cursor.close()

    match role[0]:
        case "5":
            return "/admin/dashboard"
        case "4":
            return "/user/dashboard"
    return "/"


# @desc: Removes the user's session
def remove_session():
    # get the user's session
    user_id = session.get('user_id')

    # if the user's session exists, remove it
    if user_id is not None:
        session.pop('user_id', None)
        session.clear()
        return True
    else:
        return False


# @desc: Sends the user a password reset link via email
def password_reset_link(email: str):
    # @desc: Check if the email address exists
    if not check_email_exists(email):
        return False

    # @desc: Serializer for the password reset link and the expiration time of the link is 5 minutes
    password_reset_serializer = URLSafeTimedSerializer(app.secret_key)

    # @desc: Generate the password reset link
    password_reset_url = password_reset_serializer.dumps(
        email, salt='password-reset-salt')
    print(password_reset_url)

    # desc: Send the password reset link to the user's email address
    msg = Message('Password Reset Link - Matrix Lab',
                  sender="noreply.service.matrix.ai@gmail.com", recipients=[email])

    # @desc: The email's content and format (HTML)
    msg.html = f"""
    <html>
            <body>
                <h1>Matrix AI</h1>
                <p>Hi {email},</p>
                <p>You have requested to reset your password. Please click the link below to reset your password.</p>
                <p><a href="{"http://localhost:3000/reset-password/" + password_reset_url}">Reset Password</a></p>
            </body>
        </html>
    """

    # @desc: Send the email
    mail.send(msg)

    return True


# @desc: Checks if the password reset link is valid, and if it is valid, reset the user's password
def password_reset(password_reset_url: str, password: str):
    # @desc: Serializer for the password reset link
    password_reset_serializer = URLSafeTimedSerializer(app.secret_key)

    # @desc: Check if the password reset link is valid
    try:
        # @desc: Get the user's email address from the password reset link
        email = password_reset_serializer.loads(
            password_reset_url, salt='password-reset-salt', max_age=300)
    except SignatureExpired:
        return False

    # @desc: Hash the user's password
    password_hash = password_hasher(password)

    cursor = db.cursor(buffered=True)

    # @desc: Update the user's password
    cursor.execute("UPDATE `00_user` "
                   "SET password = %s "
                   "WHERE email = %s", (password_hash, email))

    # @desc: Commit the changes to the database and close the cursor
    db.commit()
    cursor.close()

    return True
