from django.core.management.base import BaseCommand, CommandError
from users.models import User
import time
import string
import random

class Command(BaseCommand):
    help = '유저 더미 데이터를 생성합니다.'
    random_name = ['김경민', '김일경', '김이경', '이이경', '삼이경', '이경민', '이철민', '이케케']
    def handle(self, *args, **options):
        self.stdout.write("10만 유저 생성 시작")
        st = time.time()
        users_list = [
            User(
                email=f"test{num}@test.com",
                username=random.choice(self.random_name),
                age=random.randint(5, 99),
                password="dkssud12!@"
            ) for num in range(100000)
        ]
        User.objects.bulk_create(users_list)
        et = time.time()
        self.stdout.write(f"10만 유저 생성 시간{round(et-st, 2)}초 걸림")