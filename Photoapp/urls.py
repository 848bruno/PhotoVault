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
    path('logout/', views.logout_view, name='logout'),
   
    path('register/', views.register, name='register'),
    path('cart/', views.cart, name='cart'),
    path('order-history/', views.orderHistory, name='orderHistory'),
    path('track-order/', views.trackOrder, name='trackOrder'),
    path('client-manage/', views.clientManage, name='clientManage'),
    path('upload-photos/', views.upload_photos, name='upload_photos'),
    path('client-gallery/', views.client_gallery, name='client_gallery'),
    path('pic/', views.pic, name='pic'),
    path('client-page/', views.client_page, name='client_page'),
    path('purchase-photo/<int:photo_id>/', views.purchase_photo, name='purchase_photo'),
    path('add-to-cart/', views.add_to_cart, name='add_to_cart'),
    path('remove-from-cart/<int:cart_item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('update-cart-quantity/', views.update_cart_quantity, name='update_cart_quantity'),
    path('checkout/', views.checkout, name='checkout'),
    path('clear-cart/', views.clear_cart, name='clear_cart'),
  
    
    
    
    path('login/', views.login_view, name='login'),
]
