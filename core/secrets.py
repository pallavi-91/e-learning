import boto3, json
from botocore.exceptions import ClientError


def get_secrets():
    try:
        with open("secrets.json") as file:
            keys = json.loads(file.read())
    except Exception as ex:
        print('Read secret error', ex)
        keys = {}
    return keys