from datetime import datetime
from server.config.app import app, bcrypt, mail, db
from flask import session
from flask_session import Session
from flask_mail import Message

from server.controllers.helpers.input_validation import validate_password
import random
import string

server_session = Session(app)


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


# @desc Checks if user id exists
def check_user_id(user_id):
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


# @desc: Password text generator for the user's password
def password_generator():
    # @desc: Password length
    password_length = 13

    # @desc: Custom special characters for the password
    special_characters = "#?!@$%^&*-"

    # @desc: Password characters
    password_characters = string.ascii_letters + string.digits + special_characters

    # @desc: Generate the password should be 8 characters long and alphanumeric and special characters
    passwords = ''.join(random.choices(password_characters, k=password_length))

    # @desc: Check if the password is valid
    if validate_password(passwords):
        return passwords
    else:
        return password_generator()


# @desc: Password hasher checker function
def password_hash_check(hashed_password, password):
    if not bcrypt.check_password_hash(hashed_password, password):
        return False
    else:
        return True


# @desc: Password hasher function
def password_hasher(password):
    hashed_password = bcrypt.generate_password_hash(password)
    return hashed_password


# @desc: Timestamps
def timestamps():
    # @format: Day, Month, Year, @ Hour:Minute:Second
    return datetime.now().strftime("%A, %B %d, %Y @ %I:%M:%S %p")


# @desc: Creates a new user account
def create_user(email, first_name, last_name, username, password, role):
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
def delete_user(user_id):
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
def delete_user_permanently(user_id):
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
def restore_user(user_id):
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
def authenticate_user(username, password):
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

    # @desc: Commit the changes to the database and close the cursor
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
