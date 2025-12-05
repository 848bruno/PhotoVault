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