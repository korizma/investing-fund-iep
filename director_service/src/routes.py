import json
from flask import Blueprint, request
import os
import redis
from .validator import validate_jwt, extract_jwt
from pymongo import MongoClient
from datetime import datetime, timezone

auth_routes = Blueprint("auth_routes", __name__)


# veza sa mongodb
mongo_client = MongoClient(os.environ["MONGO_URI"])
mongo_db = mongo_client[os.environ["MONGO_DATABASE"]]
# pristup svim dokumentima
assets = mongo_db["assets"]

# redis
REDIS_URL = os.environ["REDIS_URL"]

r = redis.from_url(
    REDIS_URL,
    decode_responses=True,
)


@auth_routes.get("/pending_orders")
def pending_orders():
    token = extract_jwt(request.headers.get("Authorization"))

    if token is None:
        return {'msg': 'Missing Authorization Header'}, 401
    
    valid = validate_jwt(token)

    if not valid:
        return {'message': 'Invalid credentials.'}, 400
    

    orders = []

    for key in r.scan_iter("*"):
        raw = r.get(key)

        if raw is None:
            continue


        try:
            document = json.loads(raw)

            print("director_service: Read from redis:", document)

            document['uuid'] = key

            orders.append(document)
        except json.JSONDecodeError:
            continue

    return {'orders': orders}, 200



@auth_routes.post("/decision")
def decision():
    global assets
    token = extract_jwt(request.headers.get("Authorization"))

    if token is None:
        return {'msg': 'Missing Authorization Header'}, 401
    
    valid = validate_jwt(token)

    if not valid:
        return {'message': 'Invalid credentials.'}, 400
    
    data = request.get_json(silent=True) or {}

    uuid_request: str | None = data['uuid']
    approved: str | None = data['approved']

    if uuid_request is None or uuid_request == '':
        return {'message': 'Field uuid is missing.'}, 400
    

    redis_request = r.get(uuid_request)

    if redis_request is None:
        return {'message', 'Invalid uuid.'}, 400

    if approved is None or approved == '':
        return {'message': 'Field approved is missing.'}, 400
    
    redis_request = json.loads(redis_request)
    
    approved = approved.lower()
    if approved != 'true' and approved != 'false':
        return {'message': 'Invalid decision'}, 400
    
    deleted = r.delete(uuid_request)
    # someone all ready got this request
    if deleted != 1:
        return {'message', 'Invalid uuid.'}, 400
    
    print('director_service: deleted from redis:', redis_request)
    
    if redis_request['order_type'] == 'BUY':
        to_insert = {
                'name': redis_request['name'],
                'categories': redis_request['categories'],
                'buying_date': datetime.now(timezone.utc),
                'buying_price': redis_request['buying_price'],
                'info': redis_request['info']
            }
        
        print("director_service: BUY just got approved, inserting into mongodb:", to_insert)

        assets.insert_one(document=to_insert)

        return {}, 200
    elif redis_request['order_type'] == 'SELL':
        assets.update_one(
            filter=
            {
                '_id': redis_request['id']
            },
            update=
            {
                'selling_price': redis_request['selling_price'],
                'selling_date': datetime.now(timezone.utc)
            }
        )
        print("director_service: SELL just got approved, updating mongodb:", redis_request)
        return {}, 200
    
    return {'message': 'Internal server error'}, 500

@auth_routes.get("/report")
def report():
    global assets
    token = extract_jwt(request.headers.get("Authorization"))

    if token is None:
        return {'msg': 'Missing Authorization Header'}, 401
    
    valid = validate_jwt(token)

    if not valid:
        return {'message': 'Invalid credentials.'}, 400
    
    asset_list = list(assets.find(filter={}))

    statistics = {}

    for asset in asset_list:
        
        categories = asset['categories']
        buying_price = asset['buying_price']
        selling_price = asset['selling_price']

        for category in categories:
            if category in statistics:
                statistics[category]['spent'] += buying_price
                statistics[category]['earned'] += selling_price
            else:
                statistics[category] = {
                    'category': category,
                    'spent': buying_price,
                    'earned': selling_price
                }

    sorted_statistics = sorted(statistics.items(), key=lambda x: (x['earned'], x['spent'], x['category']))

    return {'statistics': sorted_statistics}, 200