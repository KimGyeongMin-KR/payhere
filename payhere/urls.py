from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path('admin/', admin.site.urls),
    path('moneylogs/', include('moneylogs.urls')),
    path('users/', include('users.urls')),

]
