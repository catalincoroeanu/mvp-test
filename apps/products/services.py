from typing import Optional, Tuple

from apps.accounts.models import User
from apps.products.models import Product


def create_product(*,
                   name: str,
                   cost: int,
                   amount_available: int,
                   seller: User) -> Tuple[Optional[Product], dict]:
    product, errors = None, {}
    error_message = validate_product_cost(cost=cost)
    if error_message:
        errors["cost"] = error_message
    else:
        product = Product.objects.create(
            name=name,
            cost=cost,
            amount_available=amount_available,
            seller=seller
        )
    return product, errors


def update_product(*,
                   name: str,
                   cost: int,
                   amount_available: int,
                   instance: Product) -> Tuple[Optional[Product], dict]:
    product, errors = None, {}
    error_message = validate_product_cost(cost=cost if cost else instance.cost)
    if error_message:
        errors["cost"] = error_message
    else:
        if name:
            instance.name = name
        if cost:
            instance.cost = cost
        if amount_available:
            instance.amount_available = amount_available
        instance.save()
        product = instance

    return product, errors


def validate_product_cost(cost: int):
    errors = []
    if cost % 5:
        errors.append("Product cost can only be a multiple of 5.")
    if cost > 100 or cost < 0:
        errors.append("Product cost can be set values between 0 to 100.")
    return errors


def buy_product(*,
                product_id: Product,
                amount_products: int,
                buyer: User) -> Tuple[Optional[dict], dict]:
    buy_response, errors = None, {}
    validation_errors_messages = validate_buy(
        product=product_id,
        amount=amount_products,
        buyer=buyer
    )
    if validation_errors_messages:
        errors = {
            "details": validation_errors_messages
        }
    else:
        total_cost = product_id.cost * amount_products

        buyer.deposit = buyer.deposit - total_cost
        product_id.amount_available = (
            product_id.amount_available - amount_products)
        product_id.save()
        buyer.save()
        buy_response = {
            "change": buyer.deposit,
            "product_name": str(product_id.name),
            "total_cost": total_cost,
        }

    return buy_response, errors


def validate_buy(product: Product, amount: int, buyer: User):
    errors = []
    total_cost = product.cost * amount
    if buyer.deposit < total_cost:
        errors.append(f"Insufficient funds. Please make sure to have at "
                      f"least {total_cost} in your deposit.")
    if product.amount_available < amount:
        errors.append(f"Product insufficient stock. You can only buy a "
                      f"total of {product.amount_available}.")
    return errors
