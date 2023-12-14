import os

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID', '')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY', '')
AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME', 'green-assets')
AWS_S3_SIGNATURE_NAME = 's3v4',
AWS_S3_REGION_NAME = 'me-south-1'
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL =  None
AWS_S3_VERIFY = True
DEFAULT_FILE_STORAGE = 'core.store.storage_backends.PrivateMediaStorage'

AWS_QUERYSTRING_EXPIRE = 3600 # seconds

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

QENCODE_API_KEY = os.getenv('QENCODE_API_KEY','')
CDN_77_SECURE_TOKEN = os.getenv('CDN_77_SECURE_TOKEN','')