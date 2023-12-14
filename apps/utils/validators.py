
from pathlib import Path
from django.core.validators import FileExtensionValidator
from rest_framework.serializers import ValidationError
from django.utils.translation import gettext as _

video_ext = ['mp4',"avi",'webm',"mkv","mov"] # "swf","mpg","ogg","m4v"
img_ext = ["jpeg","gif","tiff","png","jpg","webp","bmp","svg"]

docs_ext = ['pfg','docx','odt','xls','xlsx','ppt','pptx','doc','txt']

media_ext = video_ext + img_ext

def validate_file_extension(type ="media"):
    valid_extensions = [] 
    if type == 'media':
        valid_extensions += media_ext
    elif type == 'docs':
        valid_extensions += docs_ext
    elif isinstance(type,list):
        valid_extensions += type

    return FileExtensionValidator(valid_extensions)


def is_image(txt: str):
    return Path(txt).suffix[1:].lower() in img_ext

def is_media(txt: str):
    return Path(txt).suffix[1:].lower() in media_ext


def validate_file_size(size = 100 * 1024 * 1024): # 100 mb default

    def _validate(temp_file):
        if temp_file.size > size:
            raise ValidationError(_(f'Cannot upload video above {size / 1024 / 1024}mb'))

    return _validate