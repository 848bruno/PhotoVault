import uuid
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator


# Create a function to generate order numbers
def generate_order_number():
    return f"PV-{uuid.uuid4().hex[:8].upper()}"


class Profile(models.Model):
    USER_TYPES = (
        ('customer', 'Customer'),
        ('photographer', 'Photographer'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20)
    user_type = models.CharField(max_length=20, choices=USER_TYPES)

    def __str__(self):
        return f"{self.user.username} Profile"

    @property
    def is_photographer(self):
        return self.user_type == 'photographer'


class Photo(models.Model):
    CATEGORY_CHOICES = [
        ('portrait', 'Portrait'),
        ('landscape', 'Landscape'),
        ('event', 'Event'),
        ('product', 'Product'),
        ('nature', 'Nature'),
    ]

    photographer = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name="uploaded_photos",
        null=True,  # Keep null=True for now, we'll fix it later
        blank=True
    )
    image = models.ImageField(upload_to='photos/')
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    description = models.TextField(blank=True, null=True)
    is_purchased = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.category} - KSH {self.price}"

    @property
    def is_available(self):
        return not self.is_purchased


class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='carts')
    photo = models.ForeignKey(Photo, on_delete=models.CASCADE, related_name='carts')
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('user', 'photo')
        ordering = ['-added_at']

    def __str__(self):
        return f"{self.user.username} - {self.photo.category}"

    @property
    def total_price(self):
        return self.photo.price * self.quantity


class Purchase(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='purchases')
    photo = models.ForeignKey(Photo, on_delete=models.CASCADE, related_name='purchases')
    purchase_date = models.DateTimeField(auto_now_add=True)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='completed')
    transaction_id = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        ordering = ['-purchase_date']

    def __str__(self):
        return f"{self.user.username} - {self.photo.category} - KSH {self.amount_paid}"

    def save(self, *args, **kwargs):
        if self.status == 'completed' and not self.photo.is_purchased:
            self.photo.is_purchased = True
            self.photo.save()
        super().save(*args, **kwargs)


class PrintPrice(models.Model):
    size = models.CharField(max_length=20, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    framing_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    def __str__(self):
        return f"{self.size} - KSH {self.price}"


class PrintOrder(models.Model):
    SIZE_CHOICES = [
        ('4x6', '4x6 inches'),
        ('5x7', '5x7 inches'),
        ('8x10', '8x10 inches'),
        ('11x14', '11x14 inches'),
        ('16x20', '16x20 inches'),
        ('20x30', '20x30 inches'),
    ]
    
    PAPER_CHOICES = [
        ('matte', 'Matte'),
        ('glossy', 'Glossy'),
        ('lustre', 'Lustre'),
        ('metallic', 'Metallic'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('printed', 'Printed'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    SHIPPING_CHOICES = [
        ('standard', 'Standard (5-7 days)'),
        ('express', 'Express (2-3 days)'),
        ('overnight', 'Overnight (1 day)'),
    ]

    # Order Information
    order_number = models.CharField(max_length=20, unique=True, default=generate_order_number)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='print_orders')
    
    # Print Details
    print_size = models.CharField(max_length=20, choices=SIZE_CHOICES, default='8x10')
    paper_type = models.CharField(max_length=20, choices=PAPER_CHOICES, default='matte')
    quantity = models.PositiveIntegerField(default=1)
    framing = models.BooleanField(default=False)
    frame_color = models.CharField(max_length=50, blank=True, null=True)
    
    # Shipping Information
    shipping_method = models.CharField(max_length=20, choices=SHIPPING_CHOICES, default='standard')
    shipping_address = models.TextField()
    shipping_city = models.CharField(max_length=100)
    shipping_state = models.CharField(max_length=100)
    shipping_zip = models.CharField(max_length=20)
    shipping_country = models.CharField(max_length=100, default='Kenya')
    
    # Contact Information
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=20)
    
    # Status and Tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    status_updated = models.DateTimeField(auto_now=True)
    tracking_number = models.CharField(max_length=100, blank=True, null=True)
    estimated_delivery = models.DateField(blank=True, null=True)
    
    # Financial Information
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2)
    tax = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.order_number} - {self.user.username} - {self.get_status_display()}"
    
    @property
    def is_digital(self):
        return False
    
    @property
    def item_count(self):
        return self.printorderitem_set.count()


class PrintOrderItem(models.Model):
    order = models.ForeignKey(PrintOrder, on_delete=models.CASCADE)
    photo = models.ForeignKey(Photo, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        unique_together = ('order', 'photo')
    
    def __str__(self):
        return f"{self.order.order_number} - {self.photo.category}"
    
    @property
    def total_price(self):
        return self.unit_price * self.quantity


class OrderStatusUpdate(models.Model):
    order = models.ForeignKey(PrintOrder, on_delete=models.CASCADE, related_name='status_updates')
    status = models.CharField(max_length=20, choices=PrintOrder.STATUS_CHOICES)
    notes = models.TextField(blank=True, null=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.order.order_number} - {self.get_status_display()} - {self.created_at}"

# Add this at the end of your models.py file, before the closing

class ContactMessage(models.Model):
    STATUS_CHOICES = [
        ('new', 'New'),
        ('read', 'Read'),
        ('replied', 'Replied'),
        ('closed', 'Closed'),
    ]
    
    MESSAGE_TYPES = [
        ('general', 'General Inquiry'),
        ('support', 'Technical Support'),
        ('billing', 'Billing/Payment'),
        ('order', 'Order Related'),
        ('feedback', 'Feedback/Suggestion'),
        ('other', 'Other'),
    ]
    
    # Message Information
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True, null=True)
    subject = models.CharField(max_length=200)
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES, default='general')
    message = models.TextField()
    
    # User Info (if logged in)
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='contact_messages'
    )
    
    # Status Tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    is_urgent = models.BooleanField(default=False)
    is_replied = models.BooleanField(default=False)
    
    # Admin Response
    admin_notes = models.TextField(blank=True, null=True)
    admin_reply = models.TextField(blank=True, null=True)
    replied_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='replied_messages'
    )
    replied_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    read_at = models.DateTimeField(null=True, blank=True)
    read_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='read_messages'
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Contact Message'
        verbose_name_plural = 'Contact Messages'
    
    def __str__(self):
        return f"{self.name} - {self.subject} ({self.get_status_display()})"
    
    @property
    def is_new(self):
        return self.status == 'new'
    
    @property
    def is_read(self):
        return self.status == 'read'
    
    @property
    def is_closed(self):
        return self.status == 'closed'
    
    @property
    def time_since_creation(self):
        """Return how long ago the message was created"""
        from django.utils import timezone
        delta = timezone.now() - self.created_at
        
        if delta.days > 0:
            return f"{delta.days} days ago"
        elif delta.seconds > 3600:
            return f"{delta.seconds // 3600} hours ago"
        elif delta.seconds > 60:
            return f"{delta.seconds // 60} minutes ago"
        else:
            return "Just now"
    
    def mark_as_read(self, user=None):
        """Mark message as read"""
        from django.utils import timezone
        self.status = 'read'
        self.read_at = timezone.now()
        if user:
            self.read_by = user
        self.save()
    
    def reply_message(self, reply_text, user=None):
        """Add admin reply to message"""
        from django.utils import timezone
        self.admin_reply = reply_text
        self.status = 'replied'
        self.is_replied = True
        self.replied_at = timezone.now()
        if user:
            self.replied_by = user
        self.save()