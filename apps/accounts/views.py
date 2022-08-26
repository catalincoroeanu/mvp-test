import logging

from rest_framework import mixins, serializers, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ViewSet, ModelViewSet
from apps.accounts import services
from apps.accounts.choices import UserRole
from apps.accounts.permissions import BuyerAllowedOnly
from apps.accounts.services import deposit_amount, obtain_jwt_token, \
    reset_deposit


log = logging.getLogger(__file__)


class UserViewSet(GenericViewSet):

    class LoggedInUserSerializer(serializers.Serializer):
        id = serializers.IntegerField(read_only=True)
        username = serializers.CharField(read_only=True)
        role = serializers.CharField(read_only=True)
        deposit = serializers.IntegerField(read_only=True)

    class CreateUserSerializer(serializers.Serializer):
        username = serializers.CharField(required=True)
        password = serializers.CharField(required=True)
        role = serializers.ChoiceField(required=True, choices=UserRole)

    class UpdateUserSerializer(serializers.Serializer):
        username = serializers.CharField(required=True)

    class ChangeUserPasswordSerializer(serializers.Serializer):
        old_password = serializers.CharField(required=True)
        new_password = serializers.CharField(required=True)


    def get_serializer_class(self):
        if self.action == "logged_in_user":
            if hasattr(self.request, "method"):  # pragma: no cover
                if self.request.method == "GET":
                    self.serializer_class = self.LoggedInUserSerializer
                elif self.request.method == "POST":
                    self.serializer_class = self.CreateUserSerializer
                elif self.request.method == "PUT":
                    self.serializer_class = self.UpdateUserSerializer
            else:  # pragma: no cover
                self.serializer_class = self.LoggedInUserSerializer
        elif self.action == "change_password":
            self.serializer_class = self.ChangeUserPasswordSerializer
        else:  # pragma: no cover
            self.serializer_class = self.LoggedInUserSerializer
        return self.serializer_class

    def get_permissions(self):
        if self.action == "logged_in_user":
            if hasattr(self.request, "method"):
                if self.request.method == "POST":
                    self.permission_classes = [AllowAny]
        return super().get_permissions()

    @action(
        ["GET", "POST", "PUT"],
        detail=False,
        url_path="user",
        url_name="user"
    )
    def logged_in_user(self, request, *args, **kwargs):
        if request.method == "POST":
            return self.create_new_user(request=request, *args, **kwargs)
        if request.method == "PUT":
            return self.update_logged_in_user(request=request, *args, **kwargs)
        user = request.user
        serializer = self.get_serializer(instance=user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create_new_user(self, request, *args, **kwargs):
        serializer = self.CreateUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user, errors = services.create_user(**serializer.validated_data)
        response_serializer = self.LoggedInUserSerializer(user)
        if errors:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(response_serializer.data,
                        status=status.HTTP_201_CREATED)

    def update_logged_in_user(self, request, *args, **kwargs):
        user = request.user
        serializer = self.get_serializer(
            instance=user,
            data=request.data,
            partial=False
        )
        serializer.is_valid(raise_exception=True)
        user, errors = services.update_user(
            pk=user.id,
            username=serializer.validated_data["username"]
        )
        response_serializer = self.LoggedInUserSerializer(user)
        if errors:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(response_serializer.data)

    @action(
        ["PUT"],
        detail=False,
        url_path="change-password",
        url_name="change_password"
    )
    def change_password(self, request, *args, **kwargs):
        instance = request.user
        serializer = self.get_serializer(
            instance,
            data=request.data
        )
        serializer.is_valid(raise_exception=True)
        user, errors = services.change_password(
            pk=instance.pk,
            old_password=serializer.validated_data["old_password"],
            new_password=serializer.validated_data["new_password"]
        )
        response_serializer = self.LoggedInUserSerializer(user)
        if errors:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            "message": "Password changed successfully",
            **response_serializer.data
        })


class ResetDepositViewSet(GenericViewSet):

    class OutputSerializer(serializers.Serializer):
        deposit = serializers.IntegerField()

    permission_classes = [BuyerAllowedOnly]
    serializer_class = OutputSerializer

    def list(self, request, *args, **kwargs):
        buyer = request.user
        reset_deposit(buyer=buyer)

        response_serializer = self.OutputSerializer(instance=buyer)
        return Response(
            data=response_serializer.data,
            status=status.HTTP_200_OK
        )


class DepositViewsSet(GenericViewSet):

    class InputSerializer(serializers.Serializer):
        amount = serializers.IntegerField(min_value=1, max_value=1000)

    class OutputSerializer(serializers.Serializer):
        deposit = serializers.IntegerField()

    permission_classes = [BuyerAllowedOnly]
    serializer_class = InputSerializer

    def create(self, request, *args, **kwargs):
        buyer = request.user

        serializer = self.InputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product, errors = deposit_amount(
            **serializer.validated_data, buyer=buyer
        )

        if errors:
            return Response(data=errors, status=status.HTTP_400_BAD_REQUEST)

        response_serializer = self.OutputSerializer(instance=product)
        return Response(
            data=response_serializer.data,
            status=status.HTTP_200_OK
        )


class LoginViewsSet(GenericViewSet):

    class InputSerializer(serializers.Serializer):
        username = serializers.CharField(required=True)
        password = serializers.CharField(
            style={"input_type": "password"}, required=True
        )

    class OutputSerializer(serializers.Serializer):
        token = serializers.CharField()
        expires_at = serializers.DateTimeField()

    permission_classes = [AllowAny]
    serializer_class = InputSerializer

    def create(self, request, *args, **kwargs):

        serializer = self.InputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token_data, errors = obtain_jwt_token(
            **serializer.validated_data
        )
        if errors:
            return Response(data=errors, status=status.HTTP_400_BAD_REQUEST)

        response_serializer = self.OutputSerializer(data=token_data)
        response_serializer.is_valid()
        return Response(
            data=response_serializer.data,
            status=status.HTTP_200_OK
        )
