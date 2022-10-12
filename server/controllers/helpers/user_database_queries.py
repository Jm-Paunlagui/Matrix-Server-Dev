import os
from datetime import datetime
from server.controllers.helpers import user_agent
from server.config.app import app, bcrypt, mail, db, private_key
from flask import session, request
from flask_session import Session
from flask_mail import Message

from server.controllers.helpers.input_validation import validate_password
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature, BadData, BadTimeSignature, BadPayload
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


# @desc: Check if reset password token exists
def check_password_reset_token_exists(email: str):
    cursor = db.cursor(buffered=True)
    cursor.execute(
        "SELECT `password_reset_token` "
        "FROM `00_user` "
        "WHERE email = %s", (email,))
    is_token = cursor.fetchone()
    cursor.close()

    if is_token and not is_token[0] is None:
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


# @desc: Password text generator for the user's password
def password_generator():
    # @desc: Password length
    password_length = 15

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


password_reset_serializer = URLSafeTimedSerializer(
    secret_key=private_key, salt="password-reset-salt")


def password_reset_link(email: str):
    cursor = db.cursor(buffered=True)

    # @desc: Check if the email address exists
    if not check_email_exists(email):
        return False

    # @desc: Get email name
    cursor.execute("SELECT `first_name` "
                   "FROM `00_user` "
                   "WHERE email = %s", (email,))
    email_name = cursor.fetchone()
    email_name = email_name[0]

    # @desc: JWS token for the password reset link with the email address as the payload and the secret key as the key
    password_reset_token = password_reset_serializer.dumps(
        email, salt='password-reset-salt')

    # @desc: Gets user OS and browser including version
    os_type = user_agent.ParsedUserAgent(request.user_agent.string).platform
    os_version = user_agent.ParsedUserAgent(
        request.user_agent.string).os_version
    browser_type = user_agent.ParsedUserAgent(
        request.user_agent.string).browser
    browser_version = user_agent.ParsedUserAgent(
        request.user_agent.string).version

    # @desc: Save the password reset link to the database
    cursor.execute("UPDATE `00_user` "
                   "SET password_reset_token = %s "
                   "WHERE email = %s", (password_reset_token, email))

    # @desc: Commit the changes to the database and close the cursor
    db.commit()
    cursor.close()

    print(password_reset_token)

    # desc: Send the password reset link to the user's email address
    msg = Message('Password Reset Link - Matrix Lab',
                  sender="noreply.service.matrix.ai@gmail.com", recipients=[email])

    # @desc: The email's content and format (HTML)
    msg.html = f""" <html xmlns="http://www.w3.org/1999/xhtml"><body 
    style="background-color:#f2f4f6;width:100%;height:100%;margin:0;-webkit-text-size-adjust:none;font-family
    :Helvetica,Arial,sans-serif"><span style="display:none!important;visibility:hidden;mso-hide:all;font-size:1px
    ;line-height:1px;max-height:0;max-width:0;opacity:0;overflow:hidden">Use this link to reset your password. The 
    link is only valid for 24 hours.</span><table 
    style="width:100%;margin:0;padding:0;-premailer-width:100%;-premailer-cellpadding:0;-premailer-cellspacing:0
    ;background-color:#f2f4f6" role="presentation"><tr><td 
    style="font-size:16px;margin:auto;word-break:break-word;font-family:Helvetica,Arial,sans-serif"><table 
    style="width:100%;margin:0;padding:0;-premailer-width:100%;-premailer-cellpadding:0;-premailer-cellspacing:0" 
    role="presentation"><tr><td style="font-size:16px;padding:25px 
    0;text-align:center;word-break:break-word;font-family:Helvetica,Arial,sans-serif"><img 
    src="https://s.gravatar.com/avatar/e7315fe46c4a8a032656dae5d3952bad?s=80" alt="Paris" 
    style="display:block;margin-left:auto;margin-right:auto;width:80px"><a href="https://example.com" 
    class="f-fallback" style="font-size:24px;font-weight:700;color:#a8aaaf;text-decoration:none;text-shadow:0 1px 0 
    #fff">Matrix Lab</a></td></tr><tr><td style="font-size:16px;font-family:Helvetica,Arial,
    sans-serif;word-break:break-word;width:100%;margin:0;padding:0;-premailer-width:100%;-premailer-cellpadding:0
    ;-premailer-cellspacing:0" cellpadding="0" cellspacing="0"><table style="width:570px;margin:0 
    auto;padding:0;-premailer-width:570px;-premailer-cellpadding:0;-premailer-cellspacing:0;background-color:#fff" 
    role="presentation"><tr><td style="font-size:16px;padding:45px;word-break:break-word;font-family:Helvetica,Arial,
    sans-serif"><div class="f-fallback"><h1 style="margin-top:0;color:#333;font-weight:700;text-align:left">Hi {
    email_name},</h1><p style="color:#878a92;margin:.4em 0 1.1875em;font-size:16px;line-height:1.625">You recently 
    requested to reset your password for your Matrix account. Use the button below to reset it.<strong>This password 
    reset is only valid for the next 24 hours.</strong></p><table style="width:100%;margin:30px 
    auto;padding:0;-premailer-width:100%;-premailer-cellpadding:0;-premailer-cellspacing:0;text-align:center" 
    role="presentation"><tr><td style="font-size:16px"><table style="width:100%" role="presentation"><tr><td 
    align="center" style="font-size:16px;word-break:break-word;text-align:center;font-family:Helvetica,Arial,
    sans-serif"><a href="{"http://localhost:3000/reset-password/" + password_reset_token}" class="f-fallback" 
    target="_blank" style="background-color:#22bc66;border-top:10px solid #22bc66; width: 100%; border-bottom:10px solid 
    #22bc66;display:inline-block;color:#fff;text-decoration:none;border-radius:3px;box-shadow:0 2px 3px rgba(0,0,0,
    .16);-webkit-text-size-adjust:none;box-sizing:border-box">Reset your 
    password</a></td></tr></table></td></tr></table><p style="margin:.4em 0 
    1.1875em;font-size:16px;line-height:1.625;color:#878a92">For security, this request was received from a <b>
    {os_type} {os_version} device using {browser_type} {browser_version}</b>. If you did not request a password reset, 
    please ignore this email or contact technical support by email:<b><a style="text-decoration:none;color:#878a92" 
    href="mailto:paunlagui.cs.jm@gmail.com">paunlagui.cs.jm@gmail.com</a></b></p><p style="color:#878a92;margin:.4em 
    0 1.1875em;font-size:16px;line-height:1.625">Thanks,<br>The Matrix Lab team</p><table 
    style="margin-top:25px;padding-top:25px;border-top:1px solid #eaeaec" role="presentation"><tr><td 
    style="font-size:16px"><p style="color:#878a92;margin:.4em 0 1.1875em;font-size:13px;line-height:1.625" 
    class="f-fallback">If you&backprime;re having trouble with the button above, copy and paste the URL below into 
    your web browser.</p><p style="color:#878a92;margin:.4em 0 1.1875em;font-size:13px;line-height:1.625" 
    class="f-fallback">{"http://localhost:3000/reset-password/" + password_reset_token}</p></td></tr></table></div 
    ></td></tr></table></td></tr><tr><td><table style="width:570px;margin:0 
    auto;padding:0;-premailer-width:570px;-premailer-cellpadding:0;-premailer-cellspacing :0;text-align:center" 
    role="presentation"><tr><td style="font-size:16px;padding:45px;word-break:break-word;font-family:Helvetica,Arial, 
    sans-serif" align="center"><p style="color:#a8aaaf;margin:.4em 0 
    1.1875em;font-size:13px;line-height:1.625;text-align:center" class="f-fallback">Group 14 - Matrix Lab<br>Blk 01 
    Lot 18 Lazaro 3 Brgy. 3 Calamba City, Laguna<br>4027 
    Philippines</p></td></tr></table></td></tr></table></td></tr></table></body></html> """

    # @desc: Send the email
    mail.send(msg)

    return True


# @desc: Checks if the password reset link is valid, and if it is valid, reset the user's password
def password_reset(password_reset_token: str):
    cursor = db.cursor(buffered=True)
    try:
        # @desc: Loads the password reset token and has a max_age that automatically counts down from the time the
        # token is taken from the request
        email = password_reset_serializer.loads(
            password_reset_token, salt='password-reset-salt', max_age=86400)

        # @desc: Hash the user's password
        password = password_generator()
        password_hash = password_hasher(password)

        # @desc: Check if the token is still in the database, if it is, reset the user's password, if not, return False
        cursor.execute("SELECT `password_reset_token` "
                       "FROM `00_user` "
                       "WHERE email = %s", (email,))
        token = cursor.fetchone()

        if token[0] == password_reset_token:
            cursor.execute("UPDATE `00_user` "
                           "SET password = %s, password_reset_token = NULL "
                           "WHERE email = %s", (password_hash, email))
            db.commit()
            cursor.close()
            return True
    except BadData or BadSignature or BadTimeSignature or SignatureExpired or BadPayload:
        # @desc: If the password reset link has expired, remove the token from the database
        cursor.execute("UPDATE `00_user` "
                       "SET password_reset_token = NULL "
                       "WHERE password_reset_token = %s", (password_reset_token,))
        db.commit()
        cursor.close()
        return False
