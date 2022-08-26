import logging

from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from apps.accounts.choices import UserRole
from apps.accounts.models import User
from apps.products.models import Product


log = logging.getLogger(__file__)


class UserViewSetTestCase(APITestCase):

    def setUp(self):
        self.product_data = {
            "name": "Product 0",
            "cost": 10,
            "amount_available": 2
        }
        self.create_product_data = {
            "name": "Product 1",
            "cost": 5,
            "amount_available": 3
        }
        self.user_data_1 = {
            "username": "johndoe",
            "password": "1234test",
            "role": UserRole.BUYER
        }
        self.user_data_2 = {
            "username": "mrsmith",
            "password": "1234test",
            "role": UserRole.SELLER
        }
        self.user_data_3 = {
            "username": "jasonbourne",
            "password": "1234test",
            "role": UserRole.SELLER
        }
        self.buyer = User.objects.create_user(
            **self.user_data_1
        )
        self.seller = User.objects.create_user(
            **self.user_data_2
        )
        self.another_seller = User.objects.create_user(
            **self.user_data_3
        )
        self.product = Product.objects.create(
            **self.product_data, seller=self.seller
        )
        self.create_product_url = reverse('products-list')
        self.get_product_url = reverse('products-list')
        self.buy_product_url = reverse("buy-list")

    def test_create_product(self):
        self.client.force_login(self.seller)

        log.debug(self.create_product_url)

        response = self.client.post(
            self.create_product_url,
            data=self.create_product_data
        )
        log.debug(response.data)
        assert response.status_code == status.HTTP_201_CREATED
        expected_data = self.create_product_data
        expected_data["id"] = 2
        expected_data["seller_id"] = self.seller.id

        assert response.data == expected_data

        self.client.force_login(self.buyer)

        response = self.client.post(
            self.create_product_url,
            data=self.create_product_data
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data == {
            "detail": "You do not have permission to perform this action."
        }

    def test_get_product(self):
        self.client.force_login(self.seller)

        log.debug(self.get_product_url)
        url = reverse("products-detail", args=[1])

        response = self.client.get(url)

        log.debug(response.data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == 1
        assert response.data["name"] == self.product_data["name"]
        assert response.data["cost"] == self.product_data["cost"]
        assert response.data["seller_id"] == self.seller.id
        assert (response.data["amount_available"] ==
                self.product_data["amount_available"])

        self.client.force_login(self.buyer)

        url = reverse("products-list")
        response = self.client.get(url)

        log.debug(response.data)

        assert response.status_code == status.HTTP_200_OK

        assert len(response.data["results"]) == 1

    def test_update_product(self):
        self.client.force_login(self.seller)

        edit_product_url = reverse("products-detail", args=[1])
        new_product_name = "Edited Name"
        self.product_data["name"] = new_product_name
        response = self.client.put(
            edit_product_url,
            data=self.product_data
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == new_product_name

        self.client.force_login(self.another_seller)

        response = self.client.put(
            edit_product_url,
            data=self.product_data
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data == {
            "detail": "You do not have permission to perform this action."
        }

    def test_delete_product(self):
        self.client.force_login(self.buyer)
        delete_product_url = reverse("products-detail", args=[1])

        response = self.client.delete(delete_product_url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data == {
            "detail": "You do not have permission to perform this action."
        }

        self.client.force_login(self.another_seller)

        response = self.client.delete(delete_product_url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data == {
            "detail": "You do not have permission to perform this action."
        }

        self.client.force_login(self.seller)
        response = self.client.delete(delete_product_url)

        assert response.status_code == status.HTTP_204_NO_CONTENT

        url = reverse("products-list")
        response = self.client.get(url)

        log.debug(response.data)

        assert response.status_code == status.HTTP_200_OK

        assert len(response.data["results"]) == 0

    def test_buy_product(self):
        self.client.force_login(self.seller)
        log.debug(self.buy_product_url)

        buy_product_data = {
            "product_id": self.product.id,
            "amount_products": 2
        }

        response = self.client.post(
            self.buy_product_url,
            data=buy_product_data
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

        self.client.force_login(self.buyer)

        buy_product_data = {
            "product_id": self.product.id,
            "amount_products": self.product.amount_available + 1
        }
        self.buyer.deposit = 100
        self.buyer.save()

        response = self.client.post(
            self.buy_product_url,
            data=buy_product_data
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == {
            "details": [f"Product insufficient stock. You can only buy a "
                        f"total of {self.product.amount_available}."]
        }

        self.buyer.deposit = 0
        self.buyer.save()
        buy_product_data = {
            "product_id": self.product.id,
            "amount_products": self.product.amount_available
        }
        total_cost = self.product.amount_available * self.product.cost

        response = self.client.post(
            self.buy_product_url,
            data=buy_product_data
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == {
            "details": [f"Insufficient funds. Please make sure to have at "
                        f"least {total_cost} in your deposit."]
        }

        buy_product_data = {
            "product_id": self.product.id,
            "amount_products": self.product.amount_available
        }
        total_cost = self.product.amount_available * self.product.cost

        self.buyer.deposit = total_cost
        self.buyer.save()

        response = self.client.post(
            self.buy_product_url,
            data=buy_product_data
        )

        assert response.status_code == status.HTTP_200_OK
        log.debug(response.data)
        self.buyer.refresh_from_db()

        assert response.data == {
            "change": self.buyer.deposit,
            "product_name": str(self.product.name),
            "total_cost": total_cost
        }
