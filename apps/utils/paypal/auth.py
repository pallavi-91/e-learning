import json, ssl

from django.conf import settings
from requests import Request, Session
from urllib.error import HTTPError


ACCESS_TOKEN_URL = f"{settings.PAYPAL_API_URL}/v1/oauth2/token"


class Authorization(object):
    """ grants access token by sending a
        request to the paypal server.
        https://developer.paypal.com/api/rest/authentication/
    """
    def __init__(self, **kwargs):
        self.session = self.__init_session()
        return super().__init__()

    def __init_session(self):
        """ initialize session
        """
        return Session()

    def get_auth_token(self):
        """ get access token
        """
        req = Request("POST", ACCESS_TOKEN_URL,
            auth=(settings.PAYPAL_CLIENT_ID, settings.PAYPAL_CLIENT_SECRET),
            data={'grant_type': 'client_credentials'}
        ).prepare()
        req.headers['Content-Type'] = 'application/x-www-form-urlencoded'

        resp = self.__handle_response(self.session.send(req))
        return resp.get('access_token')

    def __http_headers(self, request_, headers={}, content_type="application/json"):
        """ request headers
        """
        req = request_.prepare()
        req.headers['Content-Type'] = content_type
        req.headers['Authorization'] = f"Bearer {self.get_auth_token()}"
        # if there are additional headers
        req.headers.update(headers)

        return req

    def __handle_response(self, resp):
        """ paypal response
        """
        try:
            return resp.json()
        except Exception as e:
            raise e

    def POST(self, url, data={}, headers={}):
        """ send a POST request to the server
            through API endpoint
        """
        req = self.__http_headers(
            Request("POST", url,
                data=json.dumps(data),
                cookies=self.session.cookies
            ),
            headers=headers,
        )

        return self.__handle_response(self.session.send(req))

    def GET(self, url, params={}, headers={}):
        """ send a GET request to the server
            through API endpoint
        """
        req = self.__http_headers(
            Request("GET", url,
                params=params,
                cookies=self.session.cookies
            ),
            headers=headers,
        )
        return self.__handle_response(self.session.send(req))
