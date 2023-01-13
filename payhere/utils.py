from django.conf import settings
import cryptocode
from ast import literal_eval
import base64


def make_dict_to_url(data:dict) -> str:
    # 데이터 > 암호화 > 암호화 데이터 > base화
    CRYPTO_KEY = getattr(settings, "CRYPTO_KEY", 'scret')    
    str_encrypt = cryptocode.encrypt(str(data), CRYPTO_KEY)
    url = base64.urlsafe_b64encode(bytes(str_encrypt, 'UTF-8')).decode("UTF-8").rstrip("=")
    return url

def make_url_to_dict(url:str) -> dict:
    # base > 암호화 처리된 데이터  > 복호화 > 데이터
    pad = "=" * (4 - (len(url) % 4))
    url = url + pad
    str_encrypted = base64.urlsafe_b64decode(bytes(url, 'UTF-8')).decode("UTF-8") 
    CRYPTO_KEY = getattr(settings, "CRYPTO_KEY", 'scret')
    str_decrypted_dict = cryptocode.decrypt(str(str_encrypted), CRYPTO_KEY)
    decrypted_dict = literal_eval(str_decrypted_dict)
    return decrypted_dict