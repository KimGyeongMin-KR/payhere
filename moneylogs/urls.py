from django.urls import path, include
from moneylogs.views import MoneyLogModelViewSet, CategoryModelViewSet

urlpatterns = [
    # MoneyLog url
    path('', MoneyLogModelViewSet.as_view({
            'get' : 'list',
            'post' : 'create',
        })
    ),
    path('<int:pk>/', MoneyLogModelViewSet.as_view({
            'get' : 'retrieve',
            'put' : 'partial_update',
            'delete' : 'destroy',
        })
    ),
    # share url
    path('<int:pk>/share/', MoneyLogModelViewSet.as_view({
            'get' : 'enter_link',
            'post' : 'make_link',
        })
    ),
    # category url
    path('category/', CategoryModelViewSet.as_view({
            'get' : 'list',
            'post' : 'create',
        })
    ),
    path('category/<int:pk>/', CategoryModelViewSet.as_view({
            # 'get' : 'retrieve',
            # 'put' : 'partial_update',
            'delete' : 'destroy',
        })
    ),
]