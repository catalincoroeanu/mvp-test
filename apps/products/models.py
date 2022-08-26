from django.db import models


class Product(models.Model):
    name = models.CharField(max_length=250)
    seller = models.ForeignKey("accounts.User", on_delete=models.CASCADE)
    cost = models.PositiveSmallIntegerField(help_text="Item Price")
    amount_available = models.PositiveBigIntegerField(
        help_text="Items on Stock"
    )

    def __str__(self):
        return self.name
