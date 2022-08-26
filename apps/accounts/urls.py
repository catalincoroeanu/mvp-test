from rest_framework import routers

from apps.accounts.views import (
    DepositViewsSet, LoginViewsSet, ResetDepositViewSet, UserViewSet
)

account_router = routers.DefaultRouter()
account_router.register("deposit", DepositViewsSet, "deposit")
account_router.register("reset", ResetDepositViewSet, "reset")
account_router.register("login", LoginViewsSet, "login")
account_router.register("", UserViewSet, "accounts")


urlpatterns = account_router.urls
