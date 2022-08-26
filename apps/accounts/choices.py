from django.db import models


class UserRole(models.TextChoices):
    BUYER = "BUYER", "buyer"
    SELLER = "SELLER", "seller"
