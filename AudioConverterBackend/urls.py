"""
URL configuration for AudioConverterBackend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from audioconverter.views import convert_upload
from django.conf import settings
from django.conf.urls.static import static
import audioconverter.views as views

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('convert_upload/', convert_upload, name='convert_upload'),
    path('api/subscriptions/', views.SubscriptionList.as_view(), name='subscription-list'),
    path('api/users/', views.UserList.as_view(), name='user-list'),
    path('api/login/', views.login_view, name='login'),
    path('api/user/', views.user_detail, name='user-detail'),
    path('api/change-password/', views.change_password, name='change-password'),
    path('api/update_subscription/', views.update_subscription, name='update-subscription'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
