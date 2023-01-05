from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from .views import UserViewSet, CustomTokenObtainPairView


urlpatterns = [
    path('', UserViewSet.as_view({'post':'create'}), name='signup'),

    # signin
    path('signin/', CustomTokenObtainPairView.as_view(), name='signin'),
    path('signin/refresh/', TokenRefreshView.as_view(), name='signin_refresh'),
]