from rest_framework.response import Response
from rest_framework import serializers, status
from rest_framework.settings import api_settings
from rest_framework.viewsets import ModelViewSet, GenericViewSet

from apps.products.models import Product
from apps.accounts.permissions import (
    BuyerAllowedOnly,
    IsSellerProductOwner,
    SellerAllowedOnly
)
from apps.products.services import (
    buy_product,
    create_product,
    update_product
)


class ProductViewSet(ModelViewSet):

    class CreateInputSerializer(serializers.Serializer):
        name = serializers.CharField(max_length=250, required=True)
        seller = serializers.CurrentUserDefault()
        amount_available = serializers.IntegerField(min_value=0, required=True)
        cost = serializers.IntegerField(required=True)

    class CreateOutputSerializer(serializers.Serializer):
        id = serializers.IntegerField(read_only=True)
        name = serializers.CharField(read_only=True)
        seller_id = serializers.IntegerField(read_only=True)
        amount_available = serializers.IntegerField(read_only=True)
        cost = serializers.IntegerField(read_only=True)

    class RetrieveOutputSerializer(serializers.Serializer):
        id = serializers.IntegerField(read_only=True)
        name = serializers.CharField(read_only=True)
        seller_id = serializers.IntegerField(read_only=True)
        amount_available = serializers.IntegerField(read_only=True)
        cost = serializers.IntegerField(read_only=True)

    class ListOutputSerializer(serializers.Serializer):
        id = serializers.IntegerField(read_only=True)
        name = serializers.CharField(read_only=True)
        seller_id = serializers.IntegerField(read_only=True)
        amount_available = serializers.IntegerField(read_only=True)
        cost = serializers.IntegerField(read_only=True)

    class UpdateInputSerializer(serializers.Serializer):
        name = serializers.CharField(max_length=250, required=False)
        amount_available = serializers.IntegerField(min_value=0, required=False)
        cost = serializers.IntegerField(required=False)

    http_method_names = [
        "get",
        "post",
        "put",
        "delete",
        "head",
        "options",
        "trace",
    ]

    def get_serializer_class(self):
        if self.action in ["create"]:
            self.serializer_class = self.CreateInputSerializer
        elif self.action == "retrieve":
            self.serializer_class = self.RetrieveOutputSerializer
        elif self.action == "list":
            self.serializer_class = self.ListOutputSerializer
        elif self.action == "update":
            self.serializer_class = self.UpdateInputSerializer
        else:  # pragma: no cover
            self.serializer_class = self.ListOutputSerializer

        return super(ProductViewSet, self).get_serializer_class()

    def get_permissions(self):
        if self.action == "create":
            self.permission_classes = [SellerAllowedOnly]
        if self.action in ["update", "destroy"]:
            self.permission_classes = [IsSellerProductOwner]

        return super(ProductViewSet, self).get_permissions()

    queryset = Product.objects.all().order_by("id")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product, errors = create_product(
            **serializer.validated_data, seller=request.user
        )

        if errors:
            return Response(data=errors, status=status.HTTP_400_BAD_REQUEST)

        response_serializer = self.CreateOutputSerializer(instance=product)
        headers = self.get_success_headers(serializer.data)
        return Response(
            data=response_serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    def get_success_headers(self, data):
        try:
            return {'Location': str(data[api_settings.URL_FIELD_NAME])}
        except (TypeError, KeyError):
            return {}

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data,
                                         partial=partial)
        serializer.is_valid(raise_exception=True)
        product, errors = update_product(
            **serializer.validated_data, instance=instance
        )

        if errors:
            return Response(data=errors, status=status.HTTP_400_BAD_REQUEST)

        response_serializer = self.CreateOutputSerializer(instance=product)
        return Response(
            data=response_serializer.data,
            status=status.HTTP_200_OK
        )


class BuyProductViewSet(GenericViewSet):

    class InputSerializer(serializers.Serializer):
        product_id = serializers.PrimaryKeyRelatedField(
            queryset=Product.objects.all()
        )
        amount_products = serializers.IntegerField(min_value=1, max_value=1000)

    class OutputSerializer(serializers.Serializer):
        change = serializers.IntegerField()
        product_name = serializers.CharField()
        total_cost = serializers.IntegerField()

    permission_classes = [BuyerAllowedOnly]
    serializer_class = InputSerializer

    def create(self, request, *args, **kwargs):
        buyer = request.user

        serializer = self.InputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product, errors = buy_product(
            **serializer.validated_data, buyer=buyer
        )

        if errors:
            return Response(data=errors, status=status.HTTP_400_BAD_REQUEST)

        response_serializer = self.OutputSerializer(instance=product)
        return Response(
            data=response_serializer.data,
            status=status.HTTP_200_OK
        )
