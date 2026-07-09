import json
from flask import Blueprint, request
import os
import redis
from .validator import validate_jwt, extract_jwt
from pymongo import MongoClient
from datetime import datetime, timezone
from bson import ObjectId
from web3 import Web3
from time import sleep
from .web3 import deploy_and_get_response, get_contract

import threading

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
        return {"msg": "Missing Authorization Header"}, 401
    

    orders = []

    for key in r.scan_iter("*"):
        raw = r.get(key)

        if raw is None:
            continue


        try:
            document = json.loads(raw)

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
        return {"msg": "Missing Authorization Header"}, 401
    
    data = request.get_json(silent=True) or {}

    uuid_request: str | None = data.get('uuid')
    voters = data.get('voters')

    if uuid_request is None or uuid_request == '':
        return {'message': 'Field uuid is missing.'}, 400
    

    redis_request = r.get(uuid_request)

    if redis_request is None:
        return {'message': 'Invalid uuid.'}, 400

    if voters is None or voters == '' or voters == []:
        return {'message': 'Field voters is missing.'}, 400
    
    redis_request = json.loads(redis_request)
    
    # address checking
    for addr in voters:
        if not Web3.is_address(addr):
            return {'message': 'Invalid voter address.'}, 400

    if len(voters) % 2 == 0:
        return {'message': 'Even number of voters.'}, 400
    
    deleted = r.delete(uuid_request)
    # someone all ready got this request
    if deleted != 1:
        return {'message': 'Invalid uuid.'}, 400
    
    contract_address, contract_abi, response = deploy_and_get_response(voters)

    # start thread that checks the chain for status
    thread_handler = threading.Thread(target=listen_to_chain, args=(contract_address, contract_abi, redis_request))

    thread_handler.start()
    
    return response, 200

@auth_routes.get("/report")
def report():
    global assets
    token = extract_jwt(request.headers.get("Authorization"))

    if token is None:
        return {'msg': 'Missing Authorization Header'}, 401
    
    valid = validate_jwt(token)

    if not valid:
        return {"msg": "Missing Authorization Header"}, 401
    
    asset_list = list(assets.find(filter={}))

    statistics = {}

    for asset in asset_list:
        
        categories = asset['categories']
        buying_price = asset['buying_price']
        selling_price = asset.get('selling_price') or 0

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

    sorted_statistics = sorted(statistics.values(), key=lambda x: (-x['earned'], x['spent'], x['category']))

    return {'statistics': sorted_statistics}, 200



def listen_to_chain(contract_address, contract_abi, redis_request):
    contract_vt = get_contract(contract_address, contract_abi)

    msg = contract_vt.functions.decisionFinalized().call()

    while msg == 0:
        sleep(1)
        msg = contract_vt.functions.decisionFinalized().call()

    if msg == -1:
        return
    
    if redis_request['order_type'] == 'BUY':
        to_insert = {
                'name': redis_request['name'],
                'categories': redis_request['categories'],
                'buying_date': datetime.now(timezone.utc),
                'buying_price': redis_request['buying_price'],
                'info': redis_request['info']
            }
        

        assets.insert_one(document=to_insert)

    elif redis_request['order_type'] == 'SELL':
        assets.update_one(
            filter=
            {
                '_id': ObjectId(redis_request['id'])
            },
            update=
            {
                '$set': {
                    'selling_price': redis_request['selling_price'],
                    'selling_date': datetime.now(timezone.utc)
                }
            }
        )

    
