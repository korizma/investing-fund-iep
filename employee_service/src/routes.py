from flask import Blueprint, request
from .validator import validate_jwt, extract_jwt
from .search_helpers import serialize_asset, create_search_query
import os
from pymongo import MongoClient
import redis
import uuid


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

    query = create_search_query(name, category, buying_date, selling_date, info_filters)

    results = list(assets.find(query))

    reformatted = []

    for result in results:
        reformatted.append(serialize_asset(result))

    return {'assets': reformatted}, 200

@auth_routes.post("/create_buy_order")
def create_buy_order():
    global assets

    token = extract_jwt(request.headers.get("Authorization"))

    if token is None:
        return {'msg': 'Missing Authorization Header'}, 401
    
    valid = validate_jwt(token)

    if not valid:
        return {'message': 'Invalid credentials.'}, 400
    
    data = request.get_json(silent=True) or {}

    name = data['name']
    categories = data['categories']
    buying_price = data['buying_price']
    info = data['info']

    if name is None or name == '':
        return {'message': 'Field name is missing'}, 400
    
    if categories is None:
        return {'message': 'Field categories is missing'}, 400
    
    if buying_price is None or buying_price == '':
        return {'message': 'Field buying_price is missing'}, 400
    
    if info is None:
        return {'message': 'Field info is missing'}, 400
    
    if categories == []:
        return {'message': 'Categories list is empty'}, 400
    
    try:
        if int(buying_price) <= 0:
            return {'message': 'Invalid buying price'}, 400

    except ValueError:
        return {'message': 'Invalid buying price'}, 400
    
    uuid_doc = str(uuid.uuid4())

    value = {
        'order_type': "BUY",
        'name': name,
        'categories': categories,
        'buying_price': buying_price,
        'info': info
    }

    r.set(uuid_doc, value, ex=3600)

    print('employee_service: inserting into redis:', value)

    return {}, 200

@auth_routes.post("/create_sell_order")
def create_sell_order():
    global assets

    token = extract_jwt(request.headers.get("Authorization"))

    if token is None:
        return {'msg': 'Missing Authorization Header'}, 401
    
    valid = validate_jwt(token)

    if not valid:
        return {'message': 'Invalid credentials.'}, 400
    
    data = request.get_json(silent=True) or {}

    id = data['id']
    selling_price = data['selling_price']

    if id is None or id == '':
        return {'message': 'Field id is missing.'}, 400
    
    if selling_price is None or selling_price == '':
        return {'message': 'Field selling_price is missing.'}, 400

    imovina = assets.find_one({'_id': id})

    if imovina is None:
        return {'message': 'Invalid id.'}, 400

    try:
        if int(selling_price) <= 0:
            return {'message': 'Invalid selling price'}, 400

    except ValueError:
        return {'message': 'Invalid selling price'}, 400
    
    # add to redis
    uuid_doc = str(uuid.uuid4())

    value = {
        'order_type': 'SELL',
        'id': id,
        'selling_price': selling_price
    }

    r.set(uuid_doc, value, ex=3600)

    print('employee_service: inserting into redis:', value)

    return {}, 200
