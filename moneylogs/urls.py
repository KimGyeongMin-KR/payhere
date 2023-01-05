from django.urls import path, include
from moneylogs.views import MoneyLogModelViewSet

urlpatterns = [
    path('',MoneyLogModelViewSet.as_view({
                'get' : 'list',
                'post' : 'create'
            })
        ),
    path('<int:pk>/',MoneyLogModelViewSet.as_view({
                'get' : 'retrieve',
                'put' : 'partial_update'
            })
        ),
]