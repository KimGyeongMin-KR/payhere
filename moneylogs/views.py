from django.shortcuts import render
from django.db import transaction
from django.db.models import Q, F
from .models import MoneyDayLog, MoneyDetailLog
from .serializers import MoneyDetailLogSerializer, MoneyDayLogSerializer, MoneyMonthSerializer

from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from datetime import datetime
from dateutil.relativedelta import *
# Create your views here.

def get_date_range(date):
    """날짜 데이터(ex. 2022-02-22)를 받아서
    1일 00시 00분 과 말일 23:59의 datetime 객체 튜플을 반환합니다.
    return start_time, end_time
    """
    date = datetime(*map(int,date.split('-')))
    start_date_time = datetime(date.year, date.month, 1)
    end_date_time = datetime(date.year, date.month, 1) + relativedelta(months=1) + relativedelta(seconds=-1)

    return start_date_time, end_date_time


class MoneyLogModelViewSet(ModelViewSet):
    serializer_class = MoneyDetailLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """base가 되는 queryset

        현재 로그인한 유저의 MoneyDetailLog를 가져옵니다.
        """
        user_id = self.request.user.id
        return MoneyDetailLog.objects.filter(user_id=user_id)

    def get_serializer_class(self):
        if self.action == 'list':
            return MoneyMonthSerializer
        return super().get_serializer_class()
    
    def get_serializer_context(self):
        """
        Extra context provided to the serializer class.
        """
        return {
            'request': self.request,
            'format': self.format_kwarg,
            'view': self,
            'action' : self.action
        }


    def list(self, request, *args, **kwargs):
        """월별로 데이터를 제공합니다. 데이터를 제공합니다.

        query_string에는 date가 들어오며 default 값으로는 오늘 날짜입니다. (ex. 2022-02-11)
        money_day_logs : 이번 달의 각 일별 수입/지출 리스트
        money_detail_logs : 이번 달의 전체 로그 리스트
        """
        user = request.user
        today = datetime.today().date()
        date = request.query_params.get('date', str(today))

        start_date_time, end_date_time = get_date_range(date)

        day_q = Q(date__gte=start_date_time.date()) & Q(date__lte=end_date_time.date()) & Q(user_id=user.id)
        detail_q = Q(day_log__date__gte=start_date_time.date()) & Q(day_log__date__lte=end_date_time.date()) & Q(user_id=user.id) \
                    & Q(is_delete=False)

        money_day_logs = MoneyDayLog.objects.select_related('user').filter(day_q).order_by('date')
        money_detail_logs = MoneyDetailLog.objects.select_related('user', 'day_log', 'day_log__user')\
                        .filter(detail_q).annotate(date=F("day_log__date")).order_by('date', '-updated_at')
        queryset = {
            'money_day_logs' : money_day_logs,
            'money_detail_logs' : money_detail_logs
        }

        serializer = self.get_serializer(queryset)
        return Response(serializer.data)
        
    def perform_create(self, serializer):
        user = self.request.user
        data = self.request.data

        today = datetime.today().date()
        date = data.get('date', str(today))

        with transaction.atomic():
            day_log, _ = MoneyDayLog.objects.get_or_create(user=user, date=date)
            instance = serializer.save(user=user, day_log=day_log)

            money_type = instance.money_type
            is_expense = True if money_type == '0' else False

            if is_expense:
                day_log.expense += instance.money
            else:
                day_log.income += instance.money
                
            day_log.save()

    def perform_update(self, serializer):
        """
        되돌렸던 수입/지출의 값에 새로 들어온 금액을 업데이트 해줍니다.
        """
        with transaction.atomic():
            instance = serializer.save()

            money_type = instance.money_type
            is_expense = True if money_type == '0' else False

            if is_expense:
                instance.day_log.expense += instance.money
            else:
                instance.day_log.income += instance.money

            instance.day_log.save()
    
    def update(self, request, *args, **kwargs):
        """
        put request 요청에서 is_delete 값의 포함 여부에 따라
        soft_delete와 partial_update로 나뉩니다.(soft-delete 우선 순위)
        soft-delete : is_delete값이 True라면 삭제이고 False라면 복원입니다.
                    그에 따라 일별 총 수입/지출의 값을 바꿔줍니다.
        update : 이전 상세 기록의 수입/지출을 참조하여 일별 수입/지출을 되돌린 후 업데이트 된 값으로 대체합니다.
                    이후 상세 기록의 값을 업데이트 해줍니다.
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        money_type = instance.money_type
        is_expense = True if money_type == '0' else False
        is_delete = serializer.validated_data.get('is_delete', '')

        if is_delete != '' and instance.is_delete != is_delete:
            if is_delete:
                message = "휴지통 이동"
                if is_expense:
                    instance.day_log.expense -= instance.money
                else:
                    instance.day_log.income -= instance.money
            else:
                message = "복원 완료"
                if is_expense:
                    instance.day_log.expense += instance.money
                else:
                    instance.day_log.income += instance.money

            instance.is_delete = is_delete

            with transaction.atomic():
                instance.save()
                instance.day_log.save()

            return Response({'message' : message}, status=status.HTTP_200_OK)
        
        if is_expense:
            instance.day_log.expense -= instance.money
        else:
            instance.day_log.income -= instance.money

        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)