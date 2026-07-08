from flask import Blueprint, request

from .validator import validate_email, validate_password, validate_jwt, create_jwt, truncate_string_field
from .db_manip import create_user, credentials_valid, delete_user

auth_routes = Blueprint("auth_routes", __name__)

DEFAULT_USER_ROLE = 'employee'


@auth_routes.post("/register")
def register():
    data = request.get_json(silent=True) or {}

    forename: str = data.get("forename")
    surname: str = data.get("surname")
    email: str = data.get("email")
    password: str = data.get("password")

    if forename is None or forename == '':
        return {'message': "Field forename is missing."}, 400
    
    if surname is None or surname == '':
        return {'message': "Field surname is missing."}, 400
    
    if email is None or email == '':
        return {'message': "Field email is missing."}, 400
    
    if password is None or password == '':
        return {'message': "Field password is missing."}, 400

    forename = truncate_string_field(forename)
    surname = truncate_string_field(surname)
    
    if not validate_email(email):
        return {'message': "Invalid email."}, 400
    
    if not validate_password(password):
        return {'message': "Invalid password."}, 400

    if not create_user(forename, surname, email, password, DEFAULT_USER_ROLE):
        return {'message': "Email already exists."}, 400

    return {}, 200

@auth_routes.post("/login")
def login():
    data = request.get_json(silent=True) or {}

    email: str = data.get("email")
    password: str = data.get("password")

    if email is None or email == '':
        return {'message': "Field email is missing."}, 400

    if password is None or password == '':
        return {'message': "Field password is missing."}, 400

    if not validate_email(email):
        return {'message': "Invalid email."}, 400

    user = credentials_valid(email, password)

    if user is None:
        return {'message': "Invalid credentials."}, 400

    token = create_jwt(user)

    return {"accessToken": token}, 200

@auth_routes.post("/delete")
def delete():
    auth_header = request.headers.get("Authorization")

    if auth_header is None:
        return {"msg": "Missing Authorization Header"}, 401

    # auth header is: "Authorization" : "Bearer <ACCESS_TOKEN>"
    parts = auth_header.split()

    if len(parts) != 2 or parts[0] != "Bearer":
        return {"msg": "Missing Authorization Header"}, 401

    token = parts[1]

    valid, email = validate_jwt(token)

    if not valid or not delete_user(email):
        return {"message": "Unknown user."}, 400
    
    return {}, 200
    
