import base64
import hashlib
from django.conf import settings

def get_signed_url_path(cdn_resource_url, file_path, secure_token, expiry_timestamp=None):
    # Because of hls/dash, anything included after the last slash (e.g. playlist/{chunk}) shouldn't be part of the path string,
    # for which we generate the secure token. Because of that, everything included after the last slash is stripped.
    stripped_path = file_path[:file_path.rfind('/')]

    # Add slash to start of stripped path if missing
    if stripped_path[0] != '/':
        stripped_path = '/' + stripped_path
        file_path = '/' + file_path

    # Cut the query string from stripped path
    position_of_start_query = stripped_path.find('?')
    if position_of_start_query != -1:
        stripped_path = stripped_path[:position_of_start_query]

    hash_string = stripped_path + secure_token
    if expiry_timestamp is not None:
        hash_string = str(expiry_timestamp) + hash_string
        expiry_timestamp = ',' + str(expiry_timestamp)

    # Replace invalid URL query string characters +, / with valid characters -, _
    invalid_chars = ['+', '/']
    valid_chars = ['-', '_']
    final_hash = base64.b64encode(hashlib.md5(hash_string.encode()).digest()).decode()
    final_hash = final_hash.translate(str.maketrans(''.join(invalid_chars), ''.join(valid_chars)))

    # The URL is however, intentionally returned with the previously stripped parts (eg. playlist/{chunk}..)
    return f'https://{cdn_resource_url}/{final_hash}{expiry_timestamp}{file_path}'


def get_signed_url_parameter(cdn_resource_url, file_path, secure_token, expiry_timestamp=None):
    # Add slash to start of file path if missing
    if file_path[0] != '/':
        file_path = '/' + file_path

    # Cut the query string from file path (e.g. "/file/video.mp4?autoplay=true" changes to "/file/video.mp4")
    position_of_start_query = file_path.find('?')
    if position_of_start_query != -1:
        file_path = file_path[:position_of_start_query]

    hash_string = file_path + secure_token
    if expiry_timestamp is not None:
        hash_string = str(expiry_timestamp) + hash_string
        expiry_timestamp = ',' + str(expiry_timestamp)

    # Replace invalid URL query string characters +, / with valid characters -, _
    invalid_chars = ['+', '/']
    valid_chars = ['-', '_']
    final_hash = base64.b64encode(hashlib.md5(hash_string.encode()).digest()).decode()
    final_hash = final_hash.translate(str.maketrans(''.join(invalid_chars), ''.join(valid_chars)))
    return f'https://{cdn_resource_url}{file_path}?secure={final_hash}{expiry_timestamp}'

# token =get_signed_url_path('thkeecdn.com', '/private/users/278/courses/a8ad1f4a-fef3-49c4-81b0-74703e5f8257/sample-30s.mp4', settings.CDN_77_SECURE_TOKEN, 1680720327)
