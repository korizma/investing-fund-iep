
from datetime import datetime, timezone
from re import escape

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


def create_search_query(name, category, buying_date, selling_date, info_filters):
    # $and treba za podrsku vise info filtera nad jednim poljem
    query = {"$and": []}

    if name:
        # proverava da li name polje u bazi sadrzi name string
        query["name"] = {"$regex": ".*" + escape(name) + ".*"}

    if category:
        # proverava da li polje categories polje koje je lista sadrzi zadatu kategoriju
        query["categories"] = category

    if buying_date:
        # gleda sve kupljene nakon buying date-a, proverava u python formatu datetime
        query["buying_date"] = {"$gt": parse_iso_datetime(buying_date)}

    if selling_date:
        # gleda sve prodate pre selling date-a, proverava u python formatu datetime
        query["selling_date"] = {"$lt": parse_iso_datetime(selling_date), "$exists": True, "$ne": None}

    for info_filter in info_filters:
        # polje nad kojim se radi filter
        field = "info." + info_filter["field"]
        operator = info_filter["operator"]
        value = info_filter["value"]

        # preskacemo nevazece operacije
        if operator not in ["eq", "ne", "gt", "gte", "lt", "lte"]:
            continue

        mongo_operator = "$" + operator
        
        query['$and'].append({field: {mongo_operator: value}})

    # ako nije bilo info filtera onda se $and polje brise
    if query["$and"] == []:
        query.pop("$and")

    return query