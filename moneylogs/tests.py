from django.urls import reverse
from rest_framework.test import APITestCase

from users.models import User
from moneylogs.models import MoneyDetailLog, MoneyDayLog, MoneyCategory
from payhere.utils import make_dict_to_url

from datetime import datetime
from dateutil.relativedelta import *

class MoneyLogSetUp(APITestCase):

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user_data = {'email' : 'test@test.com', 'username' : 'Kim', 'password' : '123', }
        cls.another_user_data = {'email' : 'test2@test.com', 'username' : 'Kim', 'password' : '123', }
        cls.user = User.objects.create_user(**cls.user_data)
        cls.another_user = User.objects.create_user(**cls.another_user_data)
        cls.day_log = MoneyDayLog.objects.create(user=cls.user, date='2023-01-07')
        cls.setup_moneylog_detail_data = {
            'id' : 10000,
            'money' : 1000,
            'money_type' : '0'
        }
        cls.basic_moneylog_detail_data = {
            'money' : 1000,
            'money_type' : '0'
        }
    
    def setUp(self) -> None:
        self.access_token = self.client.post(reverse('signin'), self.user_data).data['access']
        self.another_access_token = self.client.post(reverse('signin'), self.another_user_data).data['access']


class MoneyLogTest(MoneyLogSetUp):

    def test_log_access(self):
        """로그인 사용자의 월 단위의 로그 테스트
        """
        response = self.client.get(
            '/moneylogs/?date=2022-12-22',
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}"
        )
        self.assertEqual(response.status_code, 200)
    
    def test_log_access(self):
        """비로그인 사용자의 월 단위의 로그 접근 테스트
        """
        response = self.client.get(
            '/moneylogs/?date=2022-12-22',
        )
        self.assertEqual(response.status_code, 401)

    def test_log_create_success(self):
        """로그인 사용자 로그 생성 테스트
        """
        response = self.client.post(
            '/moneylogs/',
            self.setup_moneylog_detail_data,
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}"
        )
        self.assertEqual(response.status_code, 201)

    def test_log_create_success(self):
        """날짜 지정 로그 생성 테스트
        """
        data = self.setup_moneylog_detail_data
        data['date'] = '2022-11-11'
        response = self.client.post(
            f'/moneylogs/',
            data,
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}"
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(data['date'], response.data['date'])

    def test_log_create_fail(self):
        """비로그인 접근 테스트
        """
        response = self.client.post(
            '/moneylogs/',
            self.setup_moneylog_detail_data,
        )
        self.assertEqual(response.status_code, 401)

    def test_same_day_income_and_detail_income(self):
        """일별 수입/지출과 상세 로그들의 수입/지출의 합의 일치 테스트
        """
        for i in range(1, 11):
            data = self.basic_moneylog_detail_data
            data['id'] = i
            data['money_type'] = ['0', '1'][i%2]
            response = self.client.post(
                '/moneylogs/',
                data,
                HTTP_AUTHORIZATION=f"Bearer {self.access_token}"
            )

        money_detail_log_id = response.data['id']
        money_detail_log = MoneyDetailLog.objects.get(pk=money_detail_log_id)
        money_day_log = money_detail_log.day_log

        income = 0
        expense = 0

        for detail_log in money_day_log.detail_logs.filter(is_delete=False):
            money_type = detail_log.money_type
            is_expense = True if money_type == '0' else False
            money = detail_log.money

            if is_expense:
                expense += money
            else:
                income += money

        day_income = money_day_log.income
        day_expense = money_day_log.expense

        self.assertEqual(income, day_income)
        self.assertEqual(expense, day_expense)

    def test_soft_delete_and_restore(self):
        """휴지통으로 이동 후, 복원 후
        
        하루 내역의 수입/지출과
        상세 내역들의 수입/지출의 합의 일치 테스트
        """
        for i in range(1, 11):
            data = self.basic_moneylog_detail_data
            data['id'] = i
            data['money_type'] = ['0', '1'][i%2]
            self.client.post(
                '/moneylogs/',
                data,
                HTTP_AUTHORIZATION=f"Bearer {self.access_token}"
            )

        detail_log_id = 1
        del_data = {
            'is_delete' : True
        }
        self.client.put(
            f'/moneylogs/{detail_log_id}/',
            del_data,
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}"
        )

        detail_log = MoneyDetailLog.objects.get(pk=detail_log_id)
        day_log = detail_log.day_log

        income = 0
        expense = 0

        for detail_log in day_log.detail_logs.filter(is_delete=False):

            money_type = detail_log.money_type
            is_expense = True if money_type == '0' else False
            money = detail_log.money

            if is_expense:
                expense += money
            else:
                income += money

        self.assertEqual(day_log.income, income)
        self.assertEqual(day_log.expense, expense)

        del_data = {
            'is_delete' : False
        }
        self.client.put(
            f'/moneylogs/{detail_log_id}/',
            del_data,
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}"
        )

        detail_log = MoneyDetailLog.objects.get(pk=detail_log_id)
        day_log = detail_log.day_log

        income = 0
        expense = 0

        for detail_log in day_log.detail_logs.filter(is_delete=False):

            money_type = detail_log.money_type
            is_expense = True if money_type == '0' else False
            money = detail_log.money

            if is_expense:
                expense += money
            else:
                income += money
        self.assertEqual(day_log.income, income)
        self.assertEqual(day_log.expense, expense)

    def test_access_another_user(self):
        """다른 이용자의 접근을 방지 테스트
        """
        detail_log = MoneyDetailLog.objects.create(user=self.user, day_log=self.day_log, **self.setup_moneylog_detail_data)
        detail_log_id = detail_log.id
        another_access_token = self.client.post(reverse('signin'), self.another_user_data).data['access']
        response = self.client.get(
            f'/moneylogs/{detail_log_id}/',
            HTTP_AUTHORIZATION=f"Bearer {another_access_token}"
        )
        self.assertEqual(response.status_code, 404)

    def test_url공유_작성자와비작성자_url접속_로그인유저와비로그인유저(self):
        """
        url 공유
        - 작성자 : 200 반환
        - 비작성자 : 404 반환

        url 접속
        - 로그인 유저 : 200 반환
        - 비로그인 유저 : 401 반환
        """
        detail_log = MoneyDetailLog.objects.create(user=self.user, day_log=self.day_log, **self.setup_moneylog_detail_data)
        detail_log_id = detail_log.id
        response = self.client.post(
            f'/moneylogs/{detail_log_id}/share/',
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}"
        )
        share_url = response.data
        self.assertEqual(response.status_code, 200)

        another_access_token = self.client.post(reverse('signin'), self.another_user_data).data['access']

        response = self.client.post(
            f'/moneylogs/{detail_log_id}/share/',
            HTTP_AUTHORIZATION=f"Bearer {self.another_access_token}"
        )
        self.assertEqual(response.status_code, 404)

        response = self.client.get(
            f'/moneylogs/{share_url}/',
            HTTP_AUTHORIZATION=f"Bearer {another_access_token}"
        )
        self.assertEqual(response.status_code, 200)

        response = self.client.get(
            f'/moneylogs/{share_url}/'
        )
        self.assertEqual(response.status_code, 401)

    def test_url공유_만료기간이지나면_404_반환합니다(self):
        """공유 만료 기간이 지난 경우의 요청 테스트
        """
        detail_log = MoneyDetailLog.objects.create(user=self.user, day_log=self.day_log, **self.setup_moneylog_detail_data)
        detail_log_id = detail_log.id
        response = self.client.post(
            f'/moneylogs/{detail_log_id}/share/',
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}"
        )
        share_url = response.data

        detail_log.share_limit = datetime.now() + relativedelta(hours=-24)
        detail_log.save()

        response = self.client.get(
            f'/moneylogs/{share_url}/',
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}"
        )

        self.assertEqual(response.status_code, 404)



    def test_url조작후접근은_404_반환합니다(self):
        """공유 설정하지 않은 로그의 url 정보를 조작 후 접근 시도 테스트
        """
        detail_log = MoneyDetailLog.objects.create(user=self.user, day_log=self.day_log, **self.setup_moneylog_detail_data)
        detail_log_id = detail_log.id
        another_access_token = self.client.post(reverse('signin'), self.another_user_data).data['access']
        data = {
            "pk" : detail_log_id,
            "expiration_time" : str(datetime.now() + relativedelta(hours=24))
        }
        url = make_dict_to_url(data)
        response = self.client.get(
            f'/moneylogs/{url}/',
            HTTP_AUTHORIZATION=f"Bearer {another_access_token}"
        )
        self.assertEqual(response.status_code, 404)


    # 날짜가 제대로 들어오지 않았을 경우
    def test_옳바르지않은날짜의리스트요청은_오늘날짜로변경하여_요청합니다(self):
        dates = ["2022-24-00", "문자", "2022"]
        for date in dates:
            response = self.client.get(
                f'/moneylogs/?date={date}',
                HTTP_AUTHORIZATION=f"Bearer {self.access_token}"
            )
            self.assertEqual(response.status_code, 200)