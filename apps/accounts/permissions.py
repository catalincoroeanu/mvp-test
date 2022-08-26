from rest_framework.permissions import IsAuthenticated

from apps.accounts.choices import UserRole
from apps.products.models import Product


class BuyerAllowedOnly(IsAuthenticated):

    def has_permission(self, request, view):
        has_permission = super(BuyerAllowedOnly, self).has_permission(
            request, view
        )
        return bool(has_permission and request.user.role == UserRole.BUYER)


class SellerAllowedOnly(IsAuthenticated):

    def has_permission(self, request, view):
        has_permission = super(SellerAllowedOnly, self).has_permission(
            request, view
        )
        return bool(has_permission and request.user.role == UserRole.SELLER)


class IsSellerProductOwner(SellerAllowedOnly):

    def has_object_permission(self, request, view, obj: Product):
        seller = request.user

        product_owner = obj.seller

        return bool(seller == product_owner)
