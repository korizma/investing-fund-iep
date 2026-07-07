import re

EMAIL_PATTERN = re.compile(r"[a-zA-Z][a-zA-Z0-9._]*@([a-zA-Z][a-zA-Z0-9]*\.)+[a-zA-Z]+")

def validate_password(password : str) -> bool:
    if len(password) < 8:
        return False
    else:
        return True
    
def validate_email(email : str) -> bool:
    if EMAIL_PATTERN.fullmatch(email) is not None:
        return True
    else:
        return False
