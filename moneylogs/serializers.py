from rest_framework import serializers
from .models import MoneyDayLog, MoneyDetailLog, MoneyCategory
from datetime import datetime



class MoneyDayLogSerializer(serializers.ModelSerializer):

    class Meta:
        model = MoneyDayLog
        fields = "__all__"


class MoneyDetailLogSerializer(serializers.ModelSerializer):

    description = serializers.SerializerMethodField()

    def get_description(self, obj):
        action = self.context["action"]
        if action == 'list':
            return obj.short_description
        elif action == 'create':
            return self.context["request"].data.get('description', '')
        return obj.description

    class Meta:
        model = MoneyDetailLog
        fields = "__all__"
        read_only_fields = ['user', 'day_log']


class MoneyMonthSerializer(serializers.Serializer):
    money_day_logs = MoneyDayLogSerializer(many=True)
    money_detail_logs = MoneyDetailLogSerializer(many=True)