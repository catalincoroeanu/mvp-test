from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.accounts.choices import UserRole


class User(AbstractUser):
    role = models.CharField(
        max_length=6, choices=UserRole.choices, default=UserRole.BUYER
    )
    deposit = models.IntegerField(default=0)
