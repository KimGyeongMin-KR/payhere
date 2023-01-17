from rest_framework import serializers
from .models import MoneyDayLog, MoneyDetailLog, MoneyCategory
from datetime import datetime



class MoneyDayLogSerializer(serializers.ModelSerializer):

    class Meta:
        model = MoneyDayLog
        fields = "__all__"


class MoneyDetailLogSerializer(serializers.ModelSerializer):

    date = serializers.SerializerMethodField()

    def get_date(self, obj):
        return obj.day_log.date

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        description = self.fields.get("description", '')
        action = self.context.get("action", '')

        if description and action == "list":
            self.fields['description'] = serializers.CharField(source='short_description')

    class Meta:
        model = MoneyDetailLog
        fields = "__all__"
        read_only_fields = ['user', 'day_log']


class MoneyMonthSerializer(serializers.Serializer):
    money_day_logs = MoneyDayLogSerializer(many=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["money_detail_logs"] = MoneyDetailLogSerializer(many=True, context=self.context)

        
class MoneyCategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = MoneyCategory
        fields = "__all__"
        read_only_fields = ['user',]