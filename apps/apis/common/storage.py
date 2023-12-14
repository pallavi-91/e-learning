import logging
import boto3, requests, os
from botocore.exceptions import ClientError
from smart_open import open as sopen
from django.conf import settings

from apps.utils.helpers import convert2webp

session = boto3.Session(aws_access_key_id= settings.AWS_ACCESS_KEY_ID, 
                            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                            region_name=settings.AWS_S3_REGION_NAME)

def create_s3_bucket(bucket_name):
    """Create an S3 bucket in a specified region

    :param bucket_name: Bucket to create
    :return: True if bucket created, else False
    """

    # Create bucket
    try:
        s3_client = session.client('s3')
        location = {'LocationConstraint': settings.AWS_S3_REGION_NAME}
        s3_client.create_bucket(Bucket=bucket_name, CreateBucketConfiguration=location)
    except ClientError as e:
        logging.error(e)
        return False
    return True

def s3_create_presigned_post(file, bucket_name, object_key,
                          fields=None, conditions=None, expiration=3600):
    """Generate a presigned URL S3 POST request to upload a file
    :param file: file to upload
    :param bucket_name: string
    :param object_key: string
    :param fields: Dictionary of prefilled form fields
    :param conditions: List of conditions to include in the policy
    :param expiration: Time in seconds for the presigned URL to remain valid
    :return: Dictionary with the following keys:
        url: URL to post to
        fields: Dictionary of form fields and values to submit with the POST
    :return: None if error.
    """

    # Generate a presigned S3 POST URL
    s3_client = session.client('s3')
    
    try:
        filename, _ = os.path.splitext(file.name)
        file_content = convert2webp(file)
        object_key = f"{object_key}/{filename}.webp"

        response = s3_client.generate_presigned_post(bucket_name,
                                                     object_key,
                                                     Fields=fields,
                                                     Conditions=conditions,
                                                     ExpiresIn=expiration)
        files = {'file': (object_key, file_content)}
        http_response = requests.post(response['url'], data=response['fields'], files=files)
        if http_response.status_code == 204:
            print('Completed')
        file_url = os.path.join(response.get('url'), object_key)
        return file_url
    except ClientError as e:
        print(e)

    return None

def get_s3_presigned_url(bucket_name, object_name, expiration=3600):
    """Generate a presigned URL to share an S3 object

    :param bucket_name: string
    :param object_name: string
    :param expiration: Time in seconds for the presigned URL to remain valid
    :return: Presigned URL as string. If error, returns None.
    """

    # Generate a presigned URL for the S3 object
    s3_client = session.client('s3')
    endpointUrl = s3_client.meta.endpoint_url
    s3_client = session.client('s3', endpoint_url=endpointUrl)
    try:
        response = s3_client.generate_presigned_url('get_object',
                                                    Params={'Bucket': bucket_name,
                                                            'Key': object_name},
                                                    ExpiresIn=expiration)
    except ClientError as e:
        logging.error(e)
        return None

    # The response contains the presigned URL
    return response

def fast_s3_upload(file, bucket_name, bucket_key):
    filename, _ = os.path.splitext(file.name)
    file_content = convert2webp(file)
    bucket_key = f"{bucket_key}/{filename}.webp"
    with sopen(f"s3://{bucket_name}/{bucket_key}", 'wb', transport_params={'client': session.client('s3')}) as ff:
        ff.write(file_content)
    return get_s3_presigned_url(bucket_name, bucket_key)