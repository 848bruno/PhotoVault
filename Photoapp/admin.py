# admin.py
from django.contrib import admin
from .models import (
    Profile, Photo, Cart, Purchase, 
    PrintPrice, PrintOrder, PrintOrderItem, OrderStatusUpdate,
    ContactMessage  # Add this import
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

# ===== CONTACT MESSAGE ADMIN =====
@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'subject', 'message_type', 'status', 'is_urgent', 'created_at', 'time_since_creation']
    list_filter = ['status', 'message_type', 'is_urgent', 'is_replied', 'created_at']
    search_fields = ['name', 'email', 'subject', 'message']
    readonly_fields = ['created_at', 'updated_at', 'read_at', 'replied_at']
    list_per_page = 25
    ordering = ['-created_at']
    
    fieldsets = (
        ('Message Information', {
            'fields': ('name', 'email', 'phone', 'subject', 'message_type', 'message')
        }),
        ('User Information', {
            'fields': ('user',),
            'classes': ('collapse',)
        }),
        ('Status & Tracking', {
            'fields': ('status', 'is_urgent', 'is_replied', 'created_at', 'updated_at')
        }),
        ('Admin Response', {
            'fields': ('admin_notes', 'admin_reply', 'replied_by', 'replied_at'),
            'classes': ('collapse',)
        }),
        ('Read Status', {
            'fields': ('read_by', 'read_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_read', 'mark_as_replied', 'mark_as_closed', 'mark_as_urgent']
    
    def time_since_creation(self, obj):
        return obj.time_since_creation
    time_since_creation.short_description = 'Time Since'
    
    def mark_as_read(self, request, queryset):
        for message in queryset:
            message.mark_as_read(request.user)
        self.message_user(request, f"{queryset.count()} messages marked as read.")
    mark_as_read.short_description = "Mark selected messages as read"
    
    def mark_as_replied(self, request, queryset):
        updated = queryset.update(status='replied', is_replied=True)
        self.message_user(request, f"{updated} messages marked as replied.")
    mark_as_replied.short_description = "Mark selected messages as replied"
    
    def mark_as_closed(self, request, queryset):
        updated = queryset.update(status='closed')
        self.message_user(request, f"{updated} messages marked as closed.")
    mark_as_closed.short_description = "Mark selected messages as closed"
    
    def mark_as_urgent(self, request, queryset):
        for message in queryset:
            message.is_urgent = True
            message.save()
        self.message_user(request, f"{queryset.count()} messages marked as urgent.")
    mark_as_urgent.short_description = "Mark selected messages as urgent"
    
    # Custom view for admin panel
    change_list_template = 'emails/contact_message_change_list.html'
    
    def changelist_view(self, request, extra_context=None):
        # Add statistics to the context
        extra_context = extra_context or {}
        extra_context['new_count'] = ContactMessage.objects.filter(status='new').count()
        extra_context['urgent_count'] = ContactMessage.objects.filter(is_urgent=True).count()
        extra_context['total_count'] = ContactMessage.objects.count()
        extra_context['replied_count'] = ContactMessage.objects.filter(is_replied=True).count()
        return super().changelist_view(request, extra_context=extra_context)