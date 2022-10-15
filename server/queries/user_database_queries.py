import uuid
from datetime import datetime, timedelta
from server.modules import user_agent
from server.modules.password_bcrypt import password_hasher, password_hash_check
from server.config.configurations import app, mail, db, private_key, public_key, timezone_current_time
from flask import session, request
from flask_session import Session
from flask_mail import Message

import jwt
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
    return False


# @desc: Check email if it exists by username
def check_email_exists_by_username(username: str):
    cursor = db.cursor(buffered=True)
    cursor.execute("SELECT email, username "
                   "FROM `00_user` "
                   "WHERE username = %s", (username,))
    is_email = cursor.fetchone()
    cursor.close()
    if is_email is None:
        return False
    if is_email[1] == username:
        # Hide some of the text in the email address for security purposes and return the email address
        email = is_email[0][:2] + "*****" + \
            is_email[0][is_email[0].index("@"):]
        return email


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
    if not password_hash_check(user[2], password) or user[1] != username:
        return False
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
    return False


# @desc: Gets user OS and browser including version
def get_os_browser_versions():
    os_type = user_agent.ParsedUserAgent(request.user_agent.string).platform
    os_version = user_agent.ParsedUserAgent(
        request.user_agent.string).os_version
    browser_type = user_agent.ParsedUserAgent(
        request.user_agent.string).browser
    browser_version = user_agent.ParsedUserAgent(
        request.user_agent.string).version
    dayntime = datetime.now().strftime("%A, %I:%M:%S %p")
    return os_type, os_version, browser_type, browser_version, dayntime


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
    # @desc: First name is used to greet the user
    email_name = email_name[0]
    # payload for the password reset link and the expiration time of the link is 5 minutes and timestamp is in
    # seconds and timezones are in Local Time
    payload = {
        "iss": "http://127.0.0.1:5000",
        "sub": email,
        "iat": datetime.timestamp(timezone_current_time),
        "exp": datetime.timestamp(timezone_current_time + timedelta(hours=24)),
        "jti": str(uuid.uuid4())
    }
    # @desc: Generate the password reset link
    password_reset_token = jwt.encode(payload, private_key, algorithm="RS256")
    # desc: Gets the source of the request
    source = get_os_browser_versions()
    # @desc: Save the password reset link to the database
    cursor.execute("UPDATE `00_user` "
                   "SET password_reset_token = %s "
                   "WHERE email = %s", (password_reset_token, email))
    # @desc: Commit the changes to the database and close the cursor
    db.commit()
    cursor.close()
    # desc: Send the password reset link to the user's email address
    msg = Message('Password Reset Link - Matrix Lab',
                  sender="service.matrix.ai@gmail.com", recipients=[email])
    # @desc: The email's content and format (HTML)
    msg.html = f""" <!doctype html><html lang="en-US"><head> <meta content="text/html; charset=utf-8" 
    http-equiv="Content-Type"/></head><body marginheight="0" topmargin="0" marginwidth="0" style="margin: 0px; 
    background-color: #f2f3f8;" leftmargin="0"> <table cellspacing="0" border="0" cellpadding="0" width="100%" 
    bgcolor="#f2f3f8" style="@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@100;200;300;400
    ;500;600;700;800;900&display=swap');font-family: 'Montserrat', sans-serif;"> <tr> <td> <table 
    style="background-color: #f2f3f8; max-width:670px; margin:0 auto; padding: auto;" width="100%" border="0" 
    align="center" cellpadding="0" cellspacing="0"> <tr> <td style="height:30px;">&nbsp;</td></tr><tr> <td 
    style="text-align:center;"> <a href="" title="logo" target="_blank"> <img width="60" 
    src="https://s.gravatar.com/avatar/e7315fe46c4a8a032656dae5d3952bad?s=80" title="logo" alt="logo"> </a> 
    </td></tr><tr> <td style="height:20px;">&nbsp;</td></tr><tr> <td> <table width="87%" border="0" align="center" 
    cellpadding="0" cellspacing="0" style="max-width:670px;background:#fff; border-radius:3px; 
    text-align:center;-webkit-box-shadow:0 6px 18px 0 rgba(0,0,0,.06);-moz-box-shadow:0 6px 18px 0 rgba(0,0,0,
    .06);box-shadow:0 6px 18px 0 rgba(0,0,0,.06);"> <tr> <td style="padding:35px;"> <h1 
    style="color:#5d6068;font-weight:700;text-align:left">Hi {email_name},</h1> <p style="color:#878a92;margin:.4em 0 
    2.1875em;font-size:16px;line-height:1.625; text-align: justify;">You recently requested to reset your password 
    for your Matrix account. Use the button below to reset it. <strong>This password reset is only valid for the next 
    24 hours.</strong></p><a href="{"http://localhost:3000/reset-password/" + password_reset_token}" 
    style="background:#22bc66;text-decoration:none !important; font-weight:500; color:#fff;text-transform:uppercase; 
    font-size:14px;padding:12px 24px;display:block;border-radius:5px;box-shadow:0 2px 3px rgba(0,0,0,.16);">Reset 
    Password</a> <p style="color:#878a92;margin: 2.1875em 0 .4em;font-size:16px;line-height:1.625; text-align: 
    justify;">For security, this request was received from a <b>{source[0]} {source[1]}</b> device using <b>
    {source[2]} {source[3]}</b> on <b>{source[4]}</b>.</p><p style="color:#878a92;margin: .4em 0 
    2.1875em;font-size:16px;line-height:1.625; text-align: justify;">If you did not request a password reset, 
    please ignore this email or contact technical support by email: <b> <a 
    style="text-decoration:none;color:#878a92;" 
    href="mailto:paunlagui.cs.jm@gmail.com">paunlagui.cs.jm@gmail.com</a></p><p style="color:#878a92;margin:1.1875em 
    0 .4em;font-size:16px;line-height:1.625;text-align: left;">Thanks, <br>The Matrix Lab team </p><hr 
    style="margin-top: 12px; margin-bottom: 12px;"> <p style="color:#878a92;margin:.4em 0 
    1.1875em;font-size:13px;line-height:1.625; text-align: left;">If you&#39;re having trouble with the button above, 
    copy and paste the URL below into your web browser.</p><p style="color:#878a92;margin:.4em 0 
    1.1875em;font-size:13px;line-height:1.625; text-align: left;">
    {"http://localhost:3000/reset-password/" + password_reset_token}</p></td></tr></table> </td><tr> <td 
    style="height:20px;">&nbsp;</td></tr><tr> <td style="text-align:center;"> <p style="font-size:14px; color:rgba(
    124, 144, 163, 0.741); line-height:18px; margin:0 0 0;">Group 14 - Matrix Lab <br>Blk 01 Lot 18 Lazaro 3 Brgy. 3 
    Calamba City, Laguna <br>4027 Philippines</p></td></tr><tr> <td style="height:20px;">&nbsp;</td></tr></table> 
    </td></tr></table></body></html> """
    # @desc: Send the email
    mail.send(msg)
    return True


# @desc: Checks if the password reset link is valid, and if it is valid, reset the user's password
def password_reset(password_reset_token: str, password: str):
    cursor = db.cursor(buffered=True)
    try:
        # @desc: Get the user's email address from the password reset link
        email: dict = jwt.decode(password_reset_token, public_key, algorithms=[
                                 "RS256"], verify=True)
        # @desc: Hash the user's password
        password_hash = password_hasher(password)
        # @desc: Check if the token is still in the database, if it is, reset the user's password, if not, return False
        cursor.execute("SELECT `password_reset_token`, `first_name` "
                       "FROM `00_user` "
                       "WHERE email = %s", (email["sub"],))
        token = cursor.fetchone()
        # @desc: First name is used to greet the user
        email_name = token[1]
        if token[0] == password_reset_token:
            cursor.execute("UPDATE `00_user` "
                           "SET password = %s, password_reset_token = NULL "
                           "WHERE email = %s", (password_hash, email["sub"],))
            db.commit()
            cursor.close()
            # desc: Gets the source of the request
            source = get_os_browser_versions()
            # desc: Send an email to the user that their password has been reset successfully with a device and browser
            # info
            msg = Message("Password Reset Successful",
                          sender="service.matrix.ai@gmail.com", recipients=[email["sub"]])
            msg.html = f""" <!doctype html><html lang="en-US"><head> <meta content="text/html; charset=utf-8" 
            http-equiv="Content-Type"/></head><body marginheight="0" topmargin="0" marginwidth="0" style="margin: 
            0px; background-color: #f2f3f8;" leftmargin="0"> <table cellspacing="0" border="0" cellpadding="0" 
            width="100%" bgcolor="#f2f3f8" style="@import url(
            'https://fonts.googleapis.com/css2?family=Montserrat:wght@100;200;300;400;500;600;700;800;900&display
            =swap');font-family: 'Montserrat', sans-serif;"> <tr> <td> <table style="background-color: #f2f3f8; 
            max-width:670px; margin:0 auto; padding: auto;" width="100%" border="0" align="center" cellpadding="0" 
            cellspacing="0"> <tr> <td style="height:30px;">&nbsp;</td></tr><tr> <td style="text-align:center;"> <a 
            href="https://rakeshmandal.com" title="logo" target="_blank"> <img width="60" 
            src="https://s.gravatar.com/avatar/e7315fe46c4a8a032656dae5d3952bad?s=80" title="logo" alt="logo"> </a> 
            </td></tr><tr> <td style="height:20px;">&nbsp;</td></tr><tr> <td> <table width="87%" border="0" 
            align="center" cellpadding="0" cellspacing="0" style="max-width:670px;background:#fff; border-radius:3px; 
            text-align:center;-webkit-box-shadow:0 6px 18px 0 rgba(0,0,0,.06);-moz-box-shadow:0 6px 18px 0 rgba(0,0,
            0,.06);box-shadow:0 6px 18px 0 rgba(0,0,0,.06);"> <tr> <td style="padding:35px;"> <h1 
            style="color:#5d6068;font-weight:700;text-align:left">Hi {email_name},</h1> <p 
            style="color:#878a92;margin:.4em 0 2.1875em;font-size:16px;line-height:1.625; text-align: justify;">Your 
            password has been changed successfully.</p><p style="color:#878a92;margin: 2.1875em 0 
            .4em;font-size:16px;line-height:1.625; text-align: justify;">For security, this request was received from 
            a <b>{source[0]} {source[1]}</b> device using <b>{source[2]} {source[3]}</b> on <b>{source[4]}</b>.</p><p 
            style="color:#878a92;margin: .4em 0 2.1875em;font-size:16px;line-height:1.625; text-align: justify;">If 
            you did not change your password on this time period, please contact us immediately by email: <b><a 
            style="text-decoration:none;color:#878a92;" 
            href="mailto:paunlagui.cs.jm@gmail.com">paunlagui.cs.jm@gmail.com</a></b>.</p><p 
            style="color:#878a92;margin:1.1875em 0 .4em;font-size:16px;line-height:1.625;text-align: left;">Thanks, 
            <br>The Matrix Lab team. </p></td></tr></table> </td><tr> <td style="height:20px;">&nbsp;</td></tr><tr> 
            <td style="text-align:center;"> <p style="font-size:14px; color:rgba(124, 144, 163, 
            0.741); line-height:18px; margin:0 0 0;">Group 14 - Matrix Lab <br>Blk 01 Lot 18 Lazaro 3 Brgy. 3 Calamba 
            City, Laguna <br>4027 Philippines</p></td></tr><tr> <td style="height:20px;">&nbsp;</td></tr></table> 
            </td></tr></table></body></html> """
            mail.send(msg)
            return True
    except jwt.exceptions.InvalidTokenError:
        # @desc: If the password reset link has expired, tampers with the link, or the link is invalid, return False
        cursor.execute("UPDATE `00_user` "
                       "SET password_reset_token = NULL "
                       "WHERE password_reset_token = %s", (password_reset_token,))
        db.commit()
        cursor.close()
        return False
