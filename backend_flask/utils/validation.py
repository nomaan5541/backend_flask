import re

def validate_email(email):
    # Basic regex for email
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def validate_password(password):
    return len(password) >= 6
