# admin.py
from django.contrib import admin
from .models import (
    Profile, Photo, Cart, Purchase, 
    PrintPrice, PrintOrder, PrintOrderItem, OrderStatusUpdate
)

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone', 'user_type']
    list_filter = ['user_type']

@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ['category', 'price', 'photographer', 'is_purchased', 'uploaded_at']
    list_filter = ['category', 'is_purchased']
    search_fields = ['category', 'description']

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'photo', 'quantity', 'added_at']
    list_filter = ['is_active']

@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ['user', 'photo', 'amount_paid', 'status', 'purchase_date']
    list_filter = ['status']

@admin.register(PrintPrice)
class PrintPriceAdmin(admin.ModelAdmin):
    list_display = ['size', 'price', 'framing_price']

@admin.register(PrintOrder)
class PrintOrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'user', 'print_size', 'total_amount', 'status', 'created_at']
    list_filter = ['status', 'shipping_method']
    search_fields = ['order_number', 'user__username']

@admin.register(PrintOrderItem)
class PrintOrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'photo', 'quantity', 'unit_price']
    list_filter = ['order__status']

@admin.register(OrderStatusUpdate)
class OrderStatusUpdateAdmin(admin.ModelAdmin):
    list_display = ['order', 'status', 'updated_by', 'created_at']
    list_filter = ['status']