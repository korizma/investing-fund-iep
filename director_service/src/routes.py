from flask import Blueprint, request

from .validator import validate_jwt

auth_routes = Blueprint("auth_routes", __name__)


@auth_routes.get("/pending_orders")
def pending_orders():
    pass

@auth_routes.post("/decision")
def decision():
    pass

@auth_routes.get("/report")
def report():
    pass