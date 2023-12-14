from functools import reduce
from math import ceil
import os
import json
import subprocess
import io
from PIL import Image, ImageOps
from pathlib import Path

from django.core.files.images import get_image_dimensions
from apps.utils.validators import is_image

MAX_SIZE = (900, 700)

def set_image_dimensions(model, field_name):
    """ field  must be a FileField
        The model must have width and height fields 
    """
    f = getattr(model,field_name)
    if is_image(f.name):
        width, height = get_image_dimensions(f)
        model.width = width         
        model.height = height         
        model.save()

def sizeof_fmt(num, suffix="b"):
    for unit in ["", "k", "m", "g", "t", "p", "e", "z"]:
        if abs(num) < 1024.0:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}y{suffix}"

def decimal_to_time(total_seconds):
    min, sec = divmod(total_seconds, 60)
    hours, min = divmod(min, 60)

    return ":".join([str(int(i)) for i in [hours, min, sec]])

def file_info(fpath):
    """ return the file information
    """
    output = subprocess.check_output(
        f'ffprobe -v quiet -show_streams -select_streams v:0 -of json {fpath}',
        shell=True
    ).decode()
    return json.loads(output)['streams'][0]


def convert2webp(photo, dest=None):
    """ convert the image instance into webp
        format.
    """
    image = Image.open(io.BytesIO(photo.read()))
    orig_image = image.convert("RGB")
    img = ImageOps.exif_transpose(orig_image)
    img.thumbnail(MAX_SIZE, Image.ANTIALIAS)

    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, 'webp', quality=95)
    img_byte_arr = img_byte_arr.getvalue()
    return img_byte_arr


def quill_delta_to_text(delta={}):
    def _combine_str(acc,o):
        if not o: return ''
        arr = o['insert'] if isinstance(o['insert'], str) else '';
        return acc + " " + arr
    if type(delta) == str:
        return delta
    return reduce(_combine_str,delta.get('ops',[]),'').strip()


def count_words(text: str):
    return len(text.split(' '))


# http://www.assafelovic.com/blog/2017/6/27/estimating-an-articles-reading-time
WPM = 200
WORD_LENGTH = 5
def count_words_in_text(text_list, word_length):
    total_words = 0
    for current_text in text_list:
        total_words += len(current_text)/word_length
    return total_words


def calc_read_time(text: str):
    total_words = count_words_in_text(text, WORD_LENGTH)
    return total_words * WPM / 1000 # convert minutes to seconds


def sec_to_hour(secs):
    return secs / 3600


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip