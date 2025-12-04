from django.db import models
from django.contrib.auth.models import User


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


class Photo(models.Model):
    CATEGORY_CHOICES = [
        ('portrait', 'Portrait'),
        ('landscape', 'Landscape'),
        ('event', 'Event'),
        ('product', 'Product'),
        ('nature', 'Nature'),
    ]

    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name="photos")
    image = models.ImageField(upload_to='client_photos/')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    description = models.TextField(blank=True, null=True)
    is_purchased = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.client.username} - {self.category}"
