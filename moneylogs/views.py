# django
from django.shortcuts import render, get_object_or_404
from django.db import transaction
from django.db.models import Q, F
# project
from .models import MoneyCategory, MoneyDayLog, MoneyDetailLog
from .serializers import MoneyCategorySerializer, MoneyDetailLogSerializer, MoneyDayLogSerializer, MoneyMonthSerializer
from payhere.utils import (
    make_dict_to_url, make_url_to_dict, check_valid_log_url,
    get_date_range, get_date_or_default    
)
# drf
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
# utils
from datetime import datetime
from dateutil.relativedelta import *


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
        date = request.query_params.get('date', '')
        date = get_date_or_default(date)

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

        date = data.get('date', '')
        date = get_date_or_default(date)

        with transaction.atomic():
            day_log, _ = MoneyDayLog.objects.get_or_create(user=user, date=date)
            instance = serializer.save(user=user, day_log=day_log)
            self.set_money_by_func(instance, "add")
            instance.day_log.save()

    def perform_update(self, serializer):
        """
        되돌렸던 수입/지출의 값에 새로 들어온 금액을 업데이트 해줍니다.
        """
        with transaction.atomic():
            self.set_money_by_func(instance, "sub") # 변경 전 금액을 제거
            instance = serializer.save()
            self.set_money_by_func(instance, "add") # 변경 후 금액 추가
            instance.day_log.save()
    
    def update(self, request, *args, **kwargs):
        """
        put request 요청에서 is_delete 값의 포함 여부에 따라
        soft_delete|복원과 partial_update로 나뉩니다.(soft_delete 우선 순위)
        soft_delete : is_delete값이 True라면 삭제이고 False라면 복원입니다.
                    그에 따라 일별 총 수입/지출의 값을 바꿔줍니다.
        update : 이전 상세 기록의 수입/지출을 참조하여 일별 수입/지출을 되돌린 후 업데이트 된 값으로 대체합니다.
                    이후 상세 기록의 값을 업데이트 해줍니다.
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        is_delete = serializer.validated_data.get('is_delete', '')

        if is_delete != '' and instance.is_delete != is_delete:
            if is_delete:
                data = '휴지통 이동'
                self.set_money_by_func(instance, "sub")
            else:
                data = MoneyDetailLogSerializer(instance).data
                self.set_money_by_func(instance, "add")
            instance.is_delete = is_delete

            with transaction.atomic():
                instance.save()
                instance.day_log.save()
            return Response(data, status=status.HTTP_200_OK)
        
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def copy_log(self, request, pk=None):
        """로그를 복사하는 메서드
        """
        instance = self.get_object()
        instance.pk = None
        self.set_money_by_func(instance, "add")

        with transaction.atomic():
            instance.save()
            instance.day_log.save()
        return Response(status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def make_link(self, request, pk=None):
        """금전 로그 공유 url설정 메서드
        """
        share_limit = datetime.now() + relativedelta(hours=24)
        url_data = {
            "pk" : pk,
            "expiration_time" : share_limit.strftime('%y-%m-%d %H:%M:%S')
        }
        url = make_dict_to_url(url_data)
        instance = self.get_object()
        instance.share_limit = share_limit
        instance.share_url = url
        instance.save()
        return Response(url ,status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def enter_link(self, request, url=None):
        """공유된 로그의 정보 제공 메서드

        문자열의 url의 유효성을 검사하는 함수를 통과하면(디코딩 가능 여부, 만료 여부)
        DB에서 해당 유효 기간 필터를 한 번 더 검사하여 가져옵니다.
        """
        is_valid_url = check_valid_log_url(url)
        if not is_valid_url:
            return Response(status=status.HTTP_404_NOT_FOUND)
        log_dict = make_url_to_dict(url)
        instance = get_object_or_404(MoneyDetailLog, pk=log_dict["pk"], share_limit__gte=datetime.now())
        serializer = MoneyDetailLogSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def set_money_by_func(self, instance:object, func:str):
        """MoneyDayLog 객체의 수입/지출내역을 변경합니다.
        
        instance : MoneyDetailLog 객체
        func : 메서드 내에 func_dict의 key값 중 하나를 받습니다. ex) "add"
        """
        func_dict = {
            "add" : lambda x,y : x+y,
            "sub" : lambda x,y : x-y,
        }
        money_type_dict = {
            "0" : "expense",
            "1" : "income"
        }
        money_type = instance.money_type
        money_type_value = money_type_dict[money_type]
        op_func = func_dict[func]
        before_money = getattr(instance.day_log, money_type_value)
        after_money = op_func(before_money, instance.money)
        setattr(instance.day_log, money_type_value, after_money)


class CategoryModelViewSet(ModelViewSet):
    serializer_class = MoneyCategorySerializer
    permission_classes = [permissions.IsAuthenticated,]

    def get_queryset(self):
        """base가 되는 queryset

        현재 로그인한 유저의 MoneyCategory를 가져옵니다.
        """
        user_id = self.request.user.id
        return MoneyCategory.objects.filter(user_id=user_id)
    
    def create(self, request, *args, **kwargs):
        """
        카테고리 생성 메서드 (중복 방지)
        """
        name = request.data.get('name', '')
        user = self.request.user
        if MoneyCategory.objects.filter(user=user, name=name).exists():
            return Response({"message" : "이미 존재하는 카테고리입니다."},status=status.HTTP_409_CONFLICT)
        return super().create(request, *args, **kwargs)
    
    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(user=user)

    def destroy(self, request, *args, **kwargs):
        """
        해당 카테고리를 참조하는 MoneyDetailLog들의 카테고리를 없애고
        카테고리를 지웁니다.
        """
        instance = self.get_object()
        instance.detail_logs.update(category=None)
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
        