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
    # Admin
    path('admin/', admin.site.urls),
    
    # Authentication
    path('', views.index, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),
    
    # Main Pages
    path('client/', views.client, name='client'),
    path('admin-page/', views.admin, name='admin'),
    path('trackOrder',views.trackOrder, name='trackOrder'),
    path('pic/', views.pic, name='pic'),
      
    # Cart & Purchases
    path('cart/', views.cart, name='cart'),
    path('add-to-cart/', views.add_to_cart, name='add_to_cart'),
    path('remove-from-cart/', views.remove_from_cart, name='remove_from_cart'),
    path('update-cart-quantity/', views.update_cart_quantity, name='update_cart_quantity'),
    path('checkout/', views.checkout, name='checkout'),
    path('clear-cart/', views.clear_cart, name='clear_cart'),
    path('quick-buy/<int:photo_id>/', views.quick_buy, name='quick_buy'),
    path('purchase-photo/<int:photo_id>/', views.purchase_photo, name='purchase_photo'),
    
    # Print Orders
    path('create-print-order/', views.create_print_order, name='create_print_order'),
    
    # Order Tracking (FIXED: using the correct view names)
    path('track-orders/', views.track_order_view, name='track_orders'),
    path('track-order/<int:order_id>/', views.track_order_view, name='track_order_detail'),
    path('order-history/', views.orderHistory, name='order_history'),
    
    # Admin/Photographer Pages
    path('upload-photos/', views.upload_photos, name='upload_photos'),
    path('admin_orders/', views.admin_orders, name='admin_orders'),
    path('admin/orders/<int:order_id>/update-status/', views.update_order_status, name='update_order_status'),
    
    # Other Pages (keeping old names for compatibility)
 
    path('client-manage/', views.clientManage, name='clientManage'),
]