from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import CustomTokenObtainPairSerializer, SignUpSerializer


class CustomTokenObtainPairView(TokenObtainPairView):
    """로그인 View
    """
    serializer_class = CustomTokenObtainPairSerializer

class UserViewSet(ViewSet):
    """로그인 제외 유저 관련 View
    """
    
    def create(self, request):
        """회원가입
        """
        serializer = SignUpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(status=status.HTTP_201_CREATED)