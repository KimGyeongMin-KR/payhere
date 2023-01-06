from django.conf import settings
import cryptocode
from ast import literal_eval

def make_dict_to_url(data:dict) -> str:
    CRYPTO_KEY = getattr(settings, "CRYPTO_KEY", 'scret')
    str_encoded = cryptocode.encrypt(str(data), CRYPTO_KEY)
    return str_encoded

def make_url_to_dict(data:str) -> dict:
    CRYPTO_KEY = getattr(settings, "CRYPTO_KEY", 'scret')
    str_decoded_dict = cryptocode.decrypt(str(data), CRYPTO_KEY)
    decoded_dict = literal_eval(str_decoded_dict)
    return decoded_dict