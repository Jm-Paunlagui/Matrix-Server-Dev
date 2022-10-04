import mysql.connector
from datetime import datetime
from server.config.app import app, bcrypt
from flask import session
from flask_session import Session

server_session = Session(app)

# global variables
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="matrix"
)


# @desc: Timestamps
def timestamps():
    # @format: Day, Month, Year, @ Hour:Minute:Second
    return datetime.now().strftime("%A, %B %d, %Y @ %I:%M:%S %p")


# @desc: Check if users email exists
def check_email_exists(email):
    cursor = db.cursor(buffered=True)
    cursor.execute("SELECT email FROM `00_user` WHERE email = %s", (email,))
    is_email = cursor.fetchone()
    cursor.close()
    if is_email:
        return True
    else:
        return False


# @desc: inserting new user
def insert_user(email, first_name, last_name, username, password, role):
    cursor = db.cursor(buffered=True)
    hashed_password = bcrypt.generate_password_hash(password)
    cursor.execute("INSERT INTO `00_user` (`email`, `first_name`, `last_name`, "
                   "`username`, `password`, `role`, `date_created`) "
                   "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                   (email, first_name, last_name, username, hashed_password, role, timestamps()))
    db.commit()


# @desc: For user authentication
def authenticate_user(username, password):
    cursor = db.cursor(buffered=True)
    cursor.execute(
        "SELECT `user_id`,`username`, `password` FROM `00_user` WHERE username = %s", (username,))
    user = cursor.fetchone()
    cursor.close()

    if user is None:
        return False

    if not bcrypt.check_password_hash(user[2], password):
        return False

    session['user_id'] = user[0]

    return True


def authenticated_user():
    cursor = db.cursor(buffered=True)
    user_id = session.get('user_id')

    if user_id is None:
        return False

    cursor.execute("SELECT `user_id` FROM `00_user` WHERE user_id = %s", (user_id,))
    user = cursor.fetchone()

    return user


# @desc: Gets the user's role from the database and redirects to the appropriate page
def redirect_to():
    cursor = db.cursor(buffered=True)
    user_id = session.get('user_id')
    cursor.execute("SELECT `role` FROM `00_user` WHERE user_id = %s", (user_id,))
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
