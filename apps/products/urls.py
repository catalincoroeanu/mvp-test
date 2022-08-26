from rest_framework import routers

from apps.products.views import (
    BuyProductViewSet, ProductViewSet
)

products_router = routers.DefaultRouter()
products_router.register("products", ProductViewSet, "products")
products_router.register("buy", BuyProductViewSet, "buy")


urlpatterns = products_router.urls
