from django.urls import path, include
from .views import UserViewSet



urlpatterns = [
    path('', UserViewSet.as_view({'post':'create'})),
]
