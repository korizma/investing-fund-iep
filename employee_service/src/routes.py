from flask import Blueprint, request
from .validator import validate_jwt, extract_jwt
from datetime import datetime, timezone
import re

auth_routes = Blueprint("auth_routes", __name__)

import os
from pymongo import MongoClient

mongo_client = MongoClient(os.environ["MONGO_URI"])
mongo_db = mongo_client[os.environ["MONGO_DATABASE"]]

assets = mongo_db["assets"]

def serialize_asset(asset):
    serialized = {
        "id": str(asset["_id"]),
        "name": asset["name"],
        "categories": asset["categories"],
        "buying_price": asset["buying_price"],
        "buying_date": asset["buying_date"].isoformat(),
        "info": asset.get("info", {})
    }

    selling_date = asset.get("selling_date")
    if selling_date is not None:
        serialized["selling_price"] = asset.get("selling_price")
        serialized["selling_date"] = selling_date.isoformat()

    return serialized

def parse_iso_datetime(value: str) -> datetime:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))

    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)

    return dt

@auth_routes.post("/search")
def search():
    global assets

    token = extract_jwt(request.headers.get("Authorization"))

    if token is None:
        return {'msg': 'Missing Authorization Header'}, 401
    
    valid = validate_jwt(token)

    if not valid:
        return {'message': 'Invalid credentials.'}, 400
    

    data = request.get_json(silent=True) or {}

    name = data.get('name')
    category = data.get('category')
    buying_date = data.get('buying_date')
    selling_date = data.get('selling_date')
    info_filters = []
 
    for x in data.get('info_filters') or []:
        info_filters.append(
            {
                'field': x['field'],
                'operator': x['operator'],
                'value': x['value']
            }
        )

    query = {"$and": []}

    if name:
        query["name"] = {"$regex": re.escaped(name)}

    if category:
        query["categories"] = category

    if buying_date:
        query["buying_date"] = {"$gt": parse_iso_datetime(buying_date)}

    if selling_date:
        query["selling_date"] = {"$lt": parse_iso_datetime(selling_date), "$exists": True, "$ne": None}

    for info_filter in info_filters:
        field = "info." + info_filter["field"]
        operator = info_filter["operator"]
        value = info_filter["value"]

        if operator not in ["eq", "ne", "gt", "gte", "lt", "lte"]:
            continue

        mongo_operator = {
            "eq": "$eq",
            "ne": "$ne",
            "gt": "$gt",
            "gte": "$gte",
            "lt": "$lt",
            "lte": "$lte",
        }[operator]

        
        query['$and'].append({field: {mongo_operator: value}})

    if query["$and"] == []:
        query.pop("$and")

    results = list(assets.find(query))

    reformatted = []

    for result in results:
        reformatted.append(serialize_asset(result))

    return {'assets': reformatted}, 200

@auth_routes.post("/create_buy_order")
def create_buy_order():
    pass

@auth_routes.post("/create_sell_order")
def create_sell_order():
    pass
