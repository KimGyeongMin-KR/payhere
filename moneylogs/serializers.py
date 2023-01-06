from rest_framework import serializers
from .models import MoneyDayLog, MoneyDetailLog, MoneyCategory
from datetime import datetime



class MoneyDayLogSerializer(serializers.ModelSerializer):

    class Meta:
        model = MoneyDayLog
        fields = "__all__"


class MoneyDetailLogSerializer(serializers.ModelSerializer):

    # description = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()

    # def get_description(self, obj):
    #     action = self.context["action"]
    #     if action == 'list':
    #         return obj.short_description
    #     elif action in ['create', 'partial_update']:
    #         return self.context["request"].data.get('description', '')
    #     return obj.description
    
    def get_date(self, obj):
        return obj.day_log.date

    class Meta:
        model = MoneyDetailLog
        fields = "__all__"
        read_only_fields = ['user', 'day_log']


class MoneyMonthSerializer(serializers.Serializer):
    money_day_logs = MoneyDayLogSerializer(many=True)
    money_detail_logs = MoneyDetailLogSerializer(many=True)