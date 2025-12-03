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


