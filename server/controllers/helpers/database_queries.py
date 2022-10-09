import mysql.connector
from datetime import datetime
from server.config.app import app, bcrypt, mail
from flask import session
from flask_session import Session
from flask_mail import Message

server_session = Session(app)

# global variables
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="matrix"
)

# @TODO: Organize the functions below based on their purpose and functionality in the application


# @desc: Timestamps
def timestamps():
    # @format: Day, Month, Year, @ Hour:Minute:Second
    return datetime.now().strftime("%A, %B %d, %Y @ %I:%M:%S %p")


# @desc: Check if users email exists
def check_email_exists(email):
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


# @desc: Password hasher function
def password_hasher(password):
    hashed_password = bcrypt.generate_password_hash(password)
    return hashed_password


def password_check_hash(hashed_password, password):
    if not bcrypt.check_password_hash(hashed_password, password):
        return False
    else:
        return True


# @desc: inserting new user
def insert_user(email, first_name, last_name, username, password, role):
    cursor = db.cursor(buffered=True)
    hashed_password = password_hasher(password)
    cursor.execute("INSERT INTO `00_user` (`email`, `first_name`, `last_name`, "
                   "`username`, `password`, `role`, `date_created`) "
                   "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                   (email, first_name, last_name, username, hashed_password, role, ""))
    db.commit()
    cursor.close()


# @desc: For user authentication
def authenticate_user(username, password):
    cursor = db.cursor(buffered=True)
    cursor.execute(
        "SELECT `user_id`,`username`, `password` "
        "FROM `00_user` "
        "WHERE username = %s", (username,))
    user = cursor.fetchone()
    cursor.close()

    if user is None:
        return False

    if not bcrypt.check_password_hash(user[2], password) or user[1] != username:
        return False

    session['user_id'] = user[0]

    return True


# @desc: Gets the  user's id
def authenticated_user():
    cursor = db.cursor(buffered=True)
    user_id = session.get('user_id')

    if user_id is None:
        return False

    cursor.execute(
        "SELECT `user_id`, `email`, `first_name`, `last_name`, `username`, `password` "
        "FROM `00_user` "
        "WHERE user_id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()

    return user


# @desc: Gets the user's role from the database and redirects to the appropriate page
def redirect_to():
    cursor = db.cursor(buffered=True)
    user_id = session.get('user_id')
    cursor.execute(
        "SELECT `role` "
        "FROM `00_user` "
        "WHERE user_id = %s", (user_id,))
    role = cursor.fetchone()
    cursor.close()

    if role[0] == "5":
        return "/admin/dashboard"
    elif role[0] == "4":
        return "/user/dashboard"
    else:
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


# @desc: Password text generator for the user's password
def password_generator():
    import random
    import string

    # @desc: Password length
    password_length = 8

    # @desc: Custom special characters for the password
    special_characters = "@$!%*#?&"

    # @desc: Password characters
    password_characters = string.ascii_letters + string.digits + special_characters

    # @desc: Generate the password
    password = ''.join(random.choice(password_characters)
                       for _ in range(password_length))

    return password


# @desc: Resets the user's password by entering the email address and send the new password to the user's email address
def password_reset(email):
    cursor = db.cursor(buffered=True)

    # @desc: Check if the email address exists
    if not check_email_exists(email):
        return False

    # @desc: Generate a new password
    new_password = password_generator()

    # @desc: Hash the new password
    hashed_password = password_hasher(new_password)

    # @desc: Update the user's password
    cursor.execute("UPDATE `00_user` "
                   "SET `password` = %s "
                   "WHERE `email` = %s", (hashed_password, email))
    db.commit()
    cursor.close()

    # send the new password to the user's email address
    msg = Message("Password Reset",
                  sender="service.matrix.ai@gmail.com", recipients=[email])
    # Style the email message using HTML
    # @TODO: Design the email message using HTML and CSS and add the new password to the message body
    msg.html = f"""
        <html>
            <body>
                <h1>Matrix AI</h1>
                <p>Hi {email},</p>
                <p>Your new password is <b>{new_password}</b></p>
                <p>Thank you for using Matrix AI</p>
            </body>
        </html>
        """
    mail.send(msg)

    return True
