"""
URL configuration for PhotoVault project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from Photoapp import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='home'),
    path('client/', views.client, name='client'),
    path('admin-page/', views.admin, name='admin'),
    path('logout/', views.logout, name='logout'),
   
    path('register/', views.register, name='register'),
    path('cart/', views.cart, name='cart'),
    path('order-history/', views.orderHistory, name='orderHistory'),
    path('track-order/', views.trackOrder, name='trackOrder'),
    path('client-manage/', views.clientManage, name='clientManage'),
    
    path('login/', views.login_view, name='login'),
]
