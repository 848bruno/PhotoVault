from django.contrib import admin
from django.urls import path
from django.views.generic import TemplateView
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
    path('trackOrder/', views.trackOrder, name='trackOrder'),
    path('trackOrder/<int:order_id>/', views.trackOrder, name='track_order_detail'),
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
    
    # Order Tracking
    path('order-history/', views.orderHistory, name='order_history'),
    
    # Admin/Photographer Pages
    path('upload-photos/', views.upload_photos, name='upload_photos'),
    path('orders/', views.admin_orders, name='admin_orders'),
    path('orders/<int:order_id>/update-status/', views.update_order_status, name='update_order_status'),
    path('orders/<int:order_id>/details/', views.order_details, name='order_details'),
    
    # Client management
    path('client-manage/', views.clientManage, name='clientManage'),
    path('client/<int:client_id>/', views.client_details, name='client_details'),
    path('clients/bulk-assign/', views.bulk_assign_photos, name='bulk_assign_photos'),
    path('clients/delete/', views.delete_clients, name='delete_clients'),
    path("add-client/", views.add_client, name="add_client"),

    
    # Chatbot
    path("chat/", views.chatbot_page, name="chatbot_page"),
    path("api/chatbot/", views.chatbot_api, name="chatbot_api"),
    path('orders/<int:order_id>/details/', views.get_order_details_ajax, name='get_order_details_ajax'),

     # Contact messages
    path('contact/submit/', views.submit_contact_message, name='submit_contact'),
    path('contact-messages/', views.admin_contact_messages, name='admin_contact_messages'),
    path('contact-messages/<int:message_id>/', views.admin_contact_message_detail, name='admin_contact_message_detail'),
     
    path('process-cart-payment/', views.process_cart_payment, name='process_cart_payment'),
    path('verify-cart-payment/', views.verify_cart_payment, name='verify_cart_payment'),
    path('process-quick-buy/<int:photo_id>/', views.process_quick_buy, name='process_quick_buy'),
    path('verify-quick-buy/<int:photo_id>/', views.verify_quick_buy, name='verify_quick_buy'),
]