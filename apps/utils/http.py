import os
import pdb
from urllib.parse import urlencode
 
def urlsafe(url, *args, **kwargs):
    """ return the url combination
        in the correct format.
    """
    _url = os.path.join(url, *args)
    if not kwargs: return _url
    return f"{_url}?{urlencode(kwargs)}"