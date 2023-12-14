from storages.backends.s3boto3 import S3Boto3Storage
import boto3, os
from django.utils.encoding import filepath_to_uri
from urllib.parse import urlencode
from datetime import datetime
from datetime import timedelta
import threading
from smart_open import open as sopen
from django.utils._os import safe_join
from apps.courses.tasks import handle_video_uploading


class PrivateMediaStorage(S3Boto3Storage):
    location = 'private'
    file_overwrite = False

    def __init__(self, **kwargs) -> None:
        self._s3connections = threading.local()
        super().__init__(**kwargs)
    
    def __getstate__(self):
        state = self.__dict__.copy()
        state.pop('_connections', None)
        state.pop('_s3connections', None)
        state.pop('_bucket', None)
        return state

    def __setstate__(self, state):
        state['_connections'] = threading.local()
        state['_s3connections'] = threading.local()
        state['_bucket'] = None
        self.__dict__ = state


    def _create_session(self):
        """
        If a user specifies a profile name and this class obtains access keys
        from another source such as environment variables,we want the profile
        name to take precedence.
        """
        if self.session_profile:
            session = boto3.Session(profile_name=self.session_profile)
        else:
            session = boto3.Session(
                    aws_access_key_id=self.access_key,
                    aws_secret_access_key=self.secret_key,
                    aws_session_token=self.security_token,
                    region_name=self.region_name,
            )
        return session

    @property
    def s3connection(self):
        connection = getattr(self._s3connections, 's3_client', None)
        if connection is None:
            session = self._create_session()
            s3_client = session.client('s3')
            self.endpoint_url = s3_client.meta.endpoint_url
            self._s3connections.s3_client = session.client('s3', 
                use_ssl=self.use_ssl,
                endpoint_url=self.endpoint_url,
                config=self.config,
                verify=self.verify,
            )
        return self._s3connections.s3_client

    def url(self, name, parameters=None, expire=None, http_method=None):
        # Preserve the trailing slash after normalizing the path.
        name = self._normalize_name(self._clean_name(name))
        params = parameters.copy() if parameters else {}
        if expire is None:
            expire = self.querystring_expire

        if self.custom_domain:
            url = '{}//{}/{}{}'.format(
                self.url_protocol,
                self.custom_domain,
                filepath_to_uri(name),
                '?{}'.format(urlencode(params)) if params else '',
            )

            if self.querystring_auth and self.cloudfront_signer:
                expiration = datetime.utcnow() + timedelta(seconds=expire)
                return self.cloudfront_signer.generate_presigned_url(url, date_less_than=expiration)

            return url

        params['Bucket'] = self.bucket.name
        params['Key'] = name
        url = self.s3connection.generate_presigned_url('get_object', Params=params, ExpiresIn=expire, HttpMethod=http_method)
        if self.querystring_auth:
            return url
        return self._strip_signing_parameters(url)

    def path(self, name):
        # TO fix: This backend doesn't support absolute paths.
        return os.path.join(self.location, name)

class CoursesMediaStorage(PrivateMediaStorage):
    bucket_name = 'packaged-assets'
    region_name = 'us-east-1'

    def _save(self, name, content):
        cleaned_name = self._clean_name(name)
        name = self._normalize_name(cleaned_name)
        params = self._get_write_parameters(name, content)

        if not hasattr(content, 'seekable') or content.seekable():
            content.seek(0, os.SEEK_SET)
        if (self.gzip and
                params['ContentType'] in self.gzip_content_types and
                'ContentEncoding' not in params):
            content = self._compress_content(content)
            params['ContentEncoding'] = 'gzip'

        obj = self.bucket.Object(name)
        handle_video_uploading(content=content.read(), bucket_name=obj.bucket_name, object_key=obj.key, instance=self) # Separate task
        # obj.upload_fileobj(content, ExtraArgs=params, Config=self._transfer_config)
        return cleaned_name