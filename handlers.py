import requests
from flask import Response
import schema as ormSchema
import json
import logging
from marshmallow import ValidationError
import config

METADATA_HEADERS = {'Metadata-Flavor': 'Google'}
METADATA_URL = 'http://metadata.google.internal/computeMetadata/v1/' \
                           'instance/service-accounts/default/identity?' \
                           'audience={}'

def fetch_identity_token(audience):
    # Construct a URL with the audience and format.
    url = METADATA_URL.format(audience)

    # Request a token from the metadata server.
    r = requests.get(url, headers=METADATA_HEADERS)

    r.raise_for_status()
    return r.text

def ProcessPayload(url, method, payload):
    id_token = fetch_identity_token(url)
    
    headers        = {
        'Authorization': f'Bearer {id_token}',
        'Content-Type': 'application/json'}
    response       = requests.request(method, url, json=payload, headers=headers)
    return response

def handle_get(user, project_id, item_id):
    result = {}
    if project_id is None:
        result = ProcessPayload(config.DATA_LAYER_URL, 'GET', None)
    else:
        if item_id is None:
            result = ProcessPayload(config.DATA_LAYER_URL + "/" + project_id, 'GET', None)
        else:
            result = ProcessPayload(config.DATA_LAYER_URL + "/" + project_id + "/" + item_id, 'GET', None)
    
    return Response(response=json.dumps(result.json()), status=200, mimetype="application/json")

def handle_post(user, project_id, request):
    request_data = request.get_json()
    schema = ormSchema.BaseSchema()
    try:
        # Validate request body against schema data types
        result = schema.load(request_data)
    except ValidationError as err:
        logging.error(err.messages)
        return Response(response=json.dumps({'message': 'Invalid data provided'}), status=400, mimetype="application/json")
    
    result = ProcessPayload(config.DATA_LAYER_URL + "/" + project_id, 'POST', request_data)
    return Response(response=json.dumps(result.json()), status=200, mimetype="application/json")

def handle_put(user, request, project_id, item_id):
    request_data = request.get_json()
    if request_data is None:
        return Response(response=json.dumps({'message': 'No data provided'}), status=400, mimetype="application/json")
    
    request_data['code'] = item_id
    schema = ormSchema.BaseSchema()
    try:
        # Validate request body against schema data types
        result = schema.load(request_data)
    except ValidationError as err:
        logging.error(err.messages)
        return Response(response=json.dumps({'message': 'Invalid data provided'}), status=400, mimetype="application/json")
            
    result = ProcessPayload(config.DATA_LAYER_URL + "/" + project_id + "/" + str(item_id), 'PUT', request_data)
    return Response(response=json.dumps(result.json()), status=200, mimetype="application/json") 

def handle_delete(user, project_id, item_id):
    result = {}
    if item_id is None:
        return Response(response=json.dumps({'message': 'Item ID is required'}), status=400, mimetype="application/json")
            
    result = ProcessPayload(config.DATA_LAYER_URL + "/" + project_id + "/" + item_id, 'DELETE', None)
    if result.status_code == 200:
        return Response(response=json.dumps({'message': 'Item deleted'}), status=200, mimetype="application/json")
    elif result.status_code == 404:
        return Response(response=json.dumps({'message': 'Item not found'}), status=200, mimetype="application/json")
    else:
        return Response(response=json.dumps({'message': 'Error deleting item'}), status=500, mimetype="application/json")
    