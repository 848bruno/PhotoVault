from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator


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
        null=True,  # Add null=True temporarily for migration
        blank=True  # Add blank=True for forms
    )
    image = models.ImageField(upload_to='photos/')
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    description = models.TextField(blank=True, null=True)
    is_purchased = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.category} - KSH {self.price}"

    def save(self, *args, **kwargs):
        # If photographer is not set and the photo is being created by a user,
        # set the photographer to the current user if they're a photographer
        if not self.photographer and hasattr(self, '_current_user'):
            profile = Profile.objects.filter(user=self._current_user).first()
            if profile and profile.is_photographer:
                self.photographer = self._current_user
        super().save(*args, **kwargs)

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
        unique_together = ('user', 'photo')  # Prevent duplicate items in cart
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
        # When a purchase is made, mark the photo as purchased
        if self.status == 'completed' and not self.photo.is_purchased:
            self.photo.is_purchased = True
            self.photo.save()
        super().save(*args, **kwargs)