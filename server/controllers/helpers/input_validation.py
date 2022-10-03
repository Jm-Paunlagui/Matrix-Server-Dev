import re


def validate_empty_fields(*args):
    for arg in args:
        if arg == "" or arg is None or arg == " ":
            return False
    return True


def validate_email(email):
    if re.compile(r"[^@]+@[^@]+\.[^@]+").match(email):
        return True
    else:
        return False


def validate_password(password):
    if re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!#%*?&]{8,20}$").match(password):
        return True
    else:
        return False


def validate_username(username):
    if re.compile(r"^[a-zA-Z0-9_-]{5,20}$").match(username):
        return True
    else:
        return False


def validate_text(text):
    if re.compile(r"^[^0-9_!¡?÷?¿/\\+=@#$%ˆ&*(){}|~<>;:[\]]{2,}$").match(text):
        return True
    else:
        return False


def validate_number(number):
    if re.compile(r"^[0-9]{1,}$").match(number):
        return True
    else:
        return False
