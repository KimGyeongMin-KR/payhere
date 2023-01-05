from django.db import models

# Create your models here.

class MoneyDayLog(models.Model):
    user = models.ForeignKey('users.User', related_name='day_logs',on_delete=models.CASCADE)
    date = models.DateField() # default today
    income = models.IntegerField(default=0)
    expense = models.IntegerField(default=0)

    class Meta:
        db_table = 'MoneyDayLogs'

    def __str__(self):
        return f"{self.user}의 {self.date} 수입/지출"

class MoneyDetailLog(models.Model):
    Type = [
        ('0', "지출"),
        ('1', "수입"),
    ]

    user = models.ForeignKey('users.User', related_name='detail_logs', on_delete=models.CASCADE)
    category = models.ForeignKey('MoneyCategory', related_name='detail_logs', blank=True, null=True, on_delete=models.DO_NOTHING)
    day_log = models.ForeignKey('MoneyDayLog', related_name='detail_logs', on_delete=models.CASCADE)
    money = models.IntegerField(default=0)
    money_type = models.CharField(choices=Type, default='0', max_length=10)  # 수입, 지출 구분
    description = models.CharField(blank=True, null=True, max_length=128)
    is_delete = models.BooleanField(default=False)

    share_url = models.CharField(max_length=128, blank=True,null=True)
    share_limit = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def short_description(self):
        if self.description:
            return self.description[:10]
        return None


    class Meta:
        db_table = 'MoneyDetailLogs'

    def __str__(self):
        is_minus = '-' if self.money_type == '0' else '+'
        return f'book_name: {self.day_log} / price: {is_minus} {self.money}'

class MoneyCategory(models.Model):

    name = models.CharField(max_length=50)
    user = models.ForeignKey('users.User', related_name='money_categories', on_delete=models.CASCADE)
    is_delete = models.BooleanField(default=False)

    class Meta:
        db_table = 'MoneyCategorys'

    def __str__(self):
        return self.name