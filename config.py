import os
import requests

AUDIENCE = os.getenv('AUDIENCE')
SECRET_KEY = os.getenv('SECRET_KEY')
DATA_LAYER_URL = os.getenv('DATA_LAYER_URL')
PROJECT_ID = os.getenv('PROJECT_ID')
REGION = os.getenv('REGION')
K_SERVICE = os.getenv('K_SERVICE')
CONTEXT_ROOT = os.getenv('CONTEXT_ROOT')

METADATA_HEADERS = {'Metadata-Flavor': 'Google'}
r = requests.get("http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token", headers=METADATA_HEADERS)
r.raise_for_status()

METADATA_HEADERS = {
    'Metadata-Flavor': 'Google',
    'Authorization': f'Bearer {r.json()["access_token"]}'
    }
r = requests.get("https://{REGION}-run.googleapis.com/apis/serving.knative.dev/v1/namespaces/{PROJECT_ID}/services/{K_SERVICE}".format(
    REGION = REGION,
    PROJECT_ID = PROJECT_ID,
    K_SERVICE = K_SERVICE
    )
    , headers=METADATA_HEADERS)
r.raise_for_status()

OL_LAYER_URL = r.json()['status']['url']