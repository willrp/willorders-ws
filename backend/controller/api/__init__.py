from flask import Blueprint
from flask_restplus import Api


bpapi = Blueprint("api", __name__)

authorizations = {
    "token": {
        "type": "apiKey",
        "in": "header",
        "name": "Authorization"
    }
}

api = Api(bpapi,
    title="WillOrders API",
    description="WillOrders Web service API - Serving WillBuyer project.",
    version="0.0.1",
    doc="/",
    authorizations=authorizations
)

api.namespaces.clear()

from .order import NSOrder

for ns in NSOrder:
    api.add_namespace(ns, path="/order")
