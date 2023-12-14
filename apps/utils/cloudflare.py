from distutils.command.upload import upload
import os
from django.conf import settings
import requests
from tusclient import client
from datetime import datetime
import base64
from jwcrypto import jwt, jwk  # pip install jwcrypto

b64_jwk = 'eyJ1c2UiOiJzaWciLCJrdHkiOiJSU0EiLCJraWQiOiJhZGVhMGZiMGVmMWYzZDlhMTVmZWUxODMyMmVlMTMzMiIsImFsZyI6IlJTMjU2IiwibiI6IjdGa1MtY0dCdFFwamtwNWxLLUZrMEJNaXVBZGF0c3UyTEtjS3o1LW5JQUdsTXgydk5ISW42Q0JZd180UmM5aE9CX1BuSUZtcmpzaFJFbEx3X0lRNlR0blFMd1dXVkxvaXBtVzRtcURjemk2Sno5T2RRM0h2YjlUbnVGRncwZnhGVkZTMjdpRmRPbEpsMmVwVlp2UU5DOU5aLVVwYjRPalFkdUdJNlNaSk52Q1loSmUxTkJWMkR2NjQtWE1rRnZrVDloMUhlSmxMSkdxUWdrTENmRmItMjVWSUJfRGRBekJfby1HRnNuYno0WlRHLVBYNFFOeHJ6blBLT2g0NVR3Q0NicFZDQkZkMWhjZUh5WUllZUotMV9BM1pNRm9MQlNESmRLejEzZlFMYjZ4bTRQM01WU2M3dlVHX2lXazlrMGU3c2gxeDk4RkdwN3ZYcWFjT3JqWExNdyIsImUiOiJBUUFCIiwiZCI6Ikhac3MydGRvR1pjVEVROUJhaVZDWFNSQWdaXy1ONDYtSThySy1tWXI1OEQ5QWpHeVBGWWVkSl8wcnB4NWNETUUxMDh3d1NjcWEtamc2dlF6MXRYemZlUWdCWHZrTUhuZWxFeUN1dV95cU90QWZTV3JlZ0xnTlBpTkRGUTdWenFNTHJ1cjdKbUdWYU56dWJfMmNiNlprY1VvYktkcGFmdVBfWXhULTZ5OW1DRi12NVRETnZCNHlmVjF3c21vVnQ4Rmxyci1tQ0J2bGIyM1Uyd1ZZaW1WMDRYODk4NWxXTlB1VC11MWpEZTA2djMwOG1NUDhTekJLeFhoR205aW1wNjF6T0hVaElaN2NkMmJRVDluSnRsUGJPNWJNazZaSm5BdGNFWVZlM0dfSnRpZ1lwcjF0RHRNeXN4RTFlaDNyVnVCN0F6TzlLNzhQUlhYT3BTeFl4SkpDUSIsInAiOiItYUhOdHVXM0d2NkJ3Ry11eG9aMXJRMTJNS2F6QlI5TnJJY2tFVFM4bDJyQ0hYWHZFQndzaEo4SWVHcXRzM2VvaGZrakhUYW5NZjFXeTRFVzdLa1NpdFQ4eWVQQkl2YUVVYzRnV041SlBpUWIzU3NoWmpiWVdubm85X21TSXBrS0lmNFlCcUx6a1dxYjJ0bFkwNjJ1OFhTd0ZhQzI2NGduV3NNczRYVTI1WGsiLCJxIjoiOG1DRkpaZEVfeHRWREp6T212SzJ6eDJsY1ItTGtlNHZCWWVxamxpOVNIVG1iQnZQaHl0Y1lZMzE1Y0g4WTEwNE1fUTFJcWtrdkJjbVVCNEFMRHVkbURFSW01cFh2UVpCdWRSeHphUHRod20waEowM0tmVXNpemUyZXp1Y1lCaXI3Y0N4dDdCVXFCY1YtbExRLS1jbWRvYV9hMnJiX1JwdXF4SGJGSHhvcHdzIiwiZHAiOiJPYUprMTNSai1TU0htb0Z1amNGZmktdk92TjdQLURfSTlDdGpaV0dTcFRidHlGV0JNMnY5ejBUVWRORFVkOW9KbTV6d3dYN3J6VHZiZlRLNXN6dzUzcm5iXzFUSk02Uk0yb0pIcjV6cXRpRXFHYjhxZi1ucnU3X256TkRmTDRPNzlpc3ZLdUVXY1IxM0RHa2ZfQWRlbTdyQUtNNHBUV25yQkNhSnh5Z0QyNmsiLCJkcSI6ImVObWhhZFhiNUNzWG9fdEhsTUN5WC1EVFRlMUJwUmlTdjNvZWsyMHhxOEFGNkItUndUN2dpQV9GYkxMbGloR181VC05Z3JPOWlqOHNya1BYS0RidFpDWUd1YmNpU2pDbGN1ZTNlcVppMTdNQ0hDRmJrUU1iRzZ0Q3hIMDdnanFxOXhmZVJNMloyRm55Ym1iLXBxdGhaVFhZbWRHbE1MVU9PeVBqRFhyZW4zTSIsInFpIjoiTWR2LW5mdG5IZlBZa3NLeWRuTW95OU9ILXd1cVQtN05HcWRPUVpldkdDVHllQ3hyM0VzdW5Ta05KQ3JmNk4zX3BJTVNaT2RFaTVIS1Ftb3pLVUs3bUljbklOVXZ6WUs1RlRzcEhGMW1VcjRJVmpVQ1RKYVk3TV9yX1dYaGIyQUIxUktmRWdnM2poU2FUVDltYTRwVDhUVnJobUsybXRGNzM3Wk9JT1dKeFRZIn0='
jwk_key = jwk.JWK.from_json(base64.b64decode(b64_jwk))
BASE_URL = 'https://api.cloudflare.com/client/v4/accounts/'
BASE_URL_ACCOUNT = os.path.join(BASE_URL,settings.CLOUDFLARE_ACCOUNT_ID)

class CloudflareStream():
    STREAM_URL = os.path.join(BASE_URL_ACCOUNT,'stream')
    headers = {'Authorization': f'Bearer {settings.CLOUDFLARE_API_TOKEN}'}

    def __init__(self,file=None,video_id=None,metadata={}) -> None:
        self.file = file
        self.metadata = metadata
        self.video_id = video_id

    def get_stream_info(self,media_id):
        res = requests.get(os.path.join(self.STREAM_URL,media_id), headers=self.headers)
        res.raise_for_status()
        data = res.json()['result']
        return self._extract_data(data)

    def get_read_info(self,media_id):
        res = requests.get(os.path.join(self.STREAM_URL,media_id), headers=self.headers)
        res.raise_for_status()
        data = res.json()['result']
        if data['duration'] == -1: return self.get_read_info(media_id)
        return self._extract_data(data)

    def upload(self):
        self.metadata.update({
            'requireSignedURLs': 'True'
        })
        my_client = client.TusClient(self.STREAM_URL,headers=self.headers)

        uploader = my_client.uploader(file_stream=self.file, chunk_size= 50 * 1024 * 1024, # 50 mb
            metadata=self.metadata)
        uploader.upload()   
        self.delete()
        media_id = uploader.request.response_headers['stream-media-id']
        data = self.get_read_info(media_id)
        return data

    def _extract_data(self,data):
        return {
            'thumbnail': data['thumbnail'],
            'uid': data['uid'],
            'size': data['size'],
            'duration': data['duration'],
            'input': data['input'],
            'playback': data['playback'],
            'status': data['status'],
        }

    def delete(self):
        if not self.video_id: return 

        res = requests.delete(os.path.join(self.STREAM_URL,self.video_id), headers=self.headers)
        if res.status_code == 404:
            return True
        else:
            res.raise_for_status()

        return True

    @staticmethod
    def signed_playback_url(video_info: dict) -> dict:
        video_id = video_info.get('uid')
        if not video_id: return {}
        lifetime = video_info.get('duration',0) + 3600
        header = {"kid": jwk_key["kid"], "alg": "RS256"}
        payload = {
            "sub": video_id,
            "kid": jwk_key["kid"],
            "exp": int(datetime.now().timestamp() + lifetime),
        }
        token = jwt.JWT(header=header, claims=payload)
        token.make_signed_token(jwk_key)
        signed_token = token.serialize()
        playback = video_info.get('playback')
        hls = playback.get('hls')
        dash = playback.get('dash')
        thumbnail = video_info.get('thumbnail')

        video_info.update({
            'thumbnail': thumbnail.replace(video_id,signed_token)
        })
        playback.update({
            'hls': hls.replace(video_id,signed_token),  
            'dash': dash.replace(video_id,signed_token),  
        })
        return video_info

