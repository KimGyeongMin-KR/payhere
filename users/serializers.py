import re
# drf
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
# model
from users.models import User

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        token['email'] = user.email
        token['username'] = user.username
        token['user_id'] = user.id

        return token



class SignUpSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'username', 'password']
        extra_kwargs = {'password': {'write_only': True}}


    def create(self, validated_data):
        user  = super().create(validated_data)
        password = user.password
        user.set_password(password)
        user.save()
        return user


    def validate_password(self, pw):
        # 패스워드 정규식표현(최소 1개 이상의 영문, 숫자, 특수문자로 구성, 길이는 8~16자리)
        REGEX_PASSWORD = '^(?=.*[a-zA-Z])((?=.*\d)(?=.*\W)).{8,16}$'

        if not re.search(REGEX_PASSWORD, pw):
            raise serializers.ValidationError(detail="비밀번호 8자 이상 16이하 영문, 숫자, 특수문자 하나 이상씩 포함해 주세요.")

        return pw