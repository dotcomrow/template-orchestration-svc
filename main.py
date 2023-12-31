from flask import Flask, request, Response
from flask_cors import CORS, cross_origin
import google.cloud.logging
import logging
import json
import schema as ormSchema
from google.oauth2 import id_token
from google.auth.transport import requests
from openapi_gen.lib.wrappers import swagger_metadata
from openapi_gen.lib.security import OAuth as SwaggerOAuth
from openapi_gen.swagger import Swagger
from handlers import handle_get, handle_post, handle_put, handle_delete

logClient = google.cloud.logging.Client()
logClient.setup_logging()

app = Flask(__name__)
app.config.from_object('config')
app.secret_key = app.config['SECRET_KEY']
context_root = app.config['CONTEXT_ROOT']

cors = CORS(app, resources={
    r"/*": {"origins": "*"},
    # r"/login": {"origins": "*"},
}, supports_credentials=True)
         
def authorized_user_decorator(func):
    def inner(*args, **kwargs):
        try:
            token = request.headers.get('Authorization').split(" ")[1]
            user = id_token.verify_oauth2_token(token, requests.Request(), app.config['AUDIENCE'])
            kwargs["user"]= user
        except Exception as e:
            logging.error("Error: " + str(e))
            return Response(response=json.dumps({'message': 'Unauthorized'}), status=401, mimetype="application/json")
 
        return func(*args, **kwargs)

    inner.__name__ = func.__name__
    return inner

@app.before_request
def basic_authentication():
    if request.method.lower() == 'options':
        return Response()

@app.route("/" + context_root, defaults={'project_id': None, 'item_id': None}, methods=['GET'])
@app.route("/" + context_root + "/<item_id>", methods=['GET'])
@cross_origin(supports_credentials=True)
@swagger_metadata(
    summary='Get lookup code data',
    description='Get lookup code(s) by project id or by project and item id',
    query_params=[],
    response_model=[(200, "OK"), (401, "Unauthorized"), (404, "Item Not Found")],
    security='google',
    scopes=['openid', 'email', 'profile']
)
def get(item_id, **kwargs):
    return handle_get(item_id)
    
@app.route("/" + context_root, methods=['POST'])
@cross_origin(supports_credentials=True)
@authorized_user_decorator
@swagger_metadata(
    summary='Create Lookup Code by project ID',
    description='Creates new lookup code for a project',
    query_params=[],
    request_model=ormSchema.BaseSchema.to_dict(),
    response_model=[(200, "OK"), (401, "Unauthorized")],
    security='google',
    scopes=['openid', 'email', 'profile']
)
def post(*args, **kwargs):
    user =  kwargs.get("user")
    return handle_post(user, request)
    
@app.route("/" + context_root + "/<item_id>", methods=['PUT'])
@cross_origin(supports_credentials=True)
@authorized_user_decorator
@swagger_metadata(
    summary='Update Lookup Code by project and item ID',
    description='Updates a lookup code by project and item id',
    query_params=[],
    request_model=ormSchema.BaseSchema.to_dict(),
    response_model=[(200, "OK"), (401, "Unauthorized")],
    security='google',
    scopes=['openid', 'email', 'profile']
)
def put(item_id, **kwargs):
    user = kwargs.get("user")
    return handle_put(user, request, item_id)
    
@app.route("/" + context_root + "/<item_id>", methods=['DELETE'])
@cross_origin(supports_credentials=True)
@authorized_user_decorator
@swagger_metadata(
    summary='Delete Lookup Code by project and item ID',
    description='Deletes a lookup code by project and item id',
    query_params=[],
    response_model=[(200, "OK"), (401, "Unauthorized")],
    security='google',
    scopes=['openid', 'email', 'profile']
)
def delete(item_id, **kwargs):
    user = kwargs.get("user")
    return handle_delete(user, item_id)
    
swagger = Swagger(
    app=app,
    title='Lookup Codes orchestration API',
    version='1.0.0',
    description='This is the API for the Lookup Codes orchestration layer service',
    auth_schemes=[
        SwaggerOAuth(
            "google", 
            "https://accounts.google.com/o/oauth2/v2/auth", 
            [("scope","openid"), ("email","email"), ("profile","profile")],
            "https://www.googleapis.com/oauth2/v3/certs"
        )
    ],
    servers=[app.config['OL_LAYER_URL']],
    produces=["application/json"],
    schemes=["https"]
)

swagger.configure()

if __name__ == "__main__":
    # Development only: run "python main.py" and open http://localhost:8080
    # When deploying to Cloud Run, a production-grade WSGI HTTP server,
    # such as Gunicorn, will serve the app.
    app.run(host="localhost", port=8080, debug=True)