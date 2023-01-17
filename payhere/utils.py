from django.conf import settings
from ast import literal_eval
import base64
from datetime import datetime
from dateutil.relativedelta import *
import re


def make_dict_to_url(data:dict) -> str:
    """정보를 base64로 인코딩합니다.
    """
    url = base64.urlsafe_b64encode(bytes(str(data), 'UTF-8')).decode("UTF-8").rstrip("=")
    return url

def make_url_to_dict(url:str) -> dict:
    """base64를 통해 인코딩 되었던 url을 정보 데이터로 디코딩합니다.
    """
    pad = "=" * (4 - (len(url) % 4))
    url = url + pad
    try: # 옳바르지 않은 url입력을 대비
        str_dict = base64.urlsafe_b64decode(bytes(url, 'UTF-8')).decode("UTF-8") 
    except: # 특정 Error를 raise하지 않는다
        return False
    data_dict = literal_eval(str_dict)
    return data_dict

def check_valid_log_url(url:str) -> bool:
    """url의 유효성을 여부를 반환합니다.

    1. url의 정보를 얻기 위해 make_url_to_dict메서드로 디코딩합니다.
    2. 만료 기간 유효성 검사를 통과 여부를 반환합니다.
    """
    log_dict = make_url_to_dict(url)
    if not log_dict:
        return False
    expiration_time = log_dict.get('expiration_time', '')
    is_valid_time = datetime.now().strftime('%y-%m-%d %H:%M:%S') <= str(expiration_time)
    if is_valid_time:
        return True
    return False


def get_date_or_default(date):
    """올바른 형식의 날짜 여부를 확인하고 올바르지 않다면 오늘의 날짜를 반환합니다.
    """
    REGEX_DATE = '^\d{4}-(0[1-9]|1[012])-(0[1-9]|[12][0-9]|3[01])$'
    today = datetime.today().date()
    if re.search(REGEX_DATE, date):
        return date
    return str(today)

def get_date_range(date):
    """날짜 데이터(ex. 2022-02-22)를 받아서
    1일 00시 00분 과 말일 23:59의 datetime 객체 튜플을 반환합니다.
    return start_time, end_time
    """
    date = datetime(*map(int,date.split('-')))
    start_date_time = datetime(date.year, date.month, 1)
    end_date_time = datetime(date.year, date.month, 1) + relativedelta(months=1) + relativedelta(seconds=-1)
    return start_date_time, end_date_time
