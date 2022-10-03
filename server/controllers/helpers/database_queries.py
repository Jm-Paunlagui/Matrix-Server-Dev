import mysql.connector
from datetime import datetime
from server.config.app import bcrypt


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
    cursor.execute("SELECT `username`, `password` FROM `00_user` WHERE username = %s", (username,))
    user = cursor.fetchone()
    cursor.close()

    if user is None:
        return False

    if not bcrypt.check_password_hash(user[1], password):
        return False

    return True
