import logging

from rest_framework import status
from rest_framework.exceptions import ErrorDetail
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from apps.accounts.choices import UserRole
from apps.accounts.models import User
from config.settings import env


log = logging.getLogger(__file__)


def test_testing_env():
    assert env.str("ENV", default="no_val") == "test"
    assert env.str("SQLITE_BD_NAME", default="no_val") == "db.test_sqlite3"


class UserViewSetTestCase(APITestCase):

    def setUp(self):
        self.create_user_data = {
            "username": "createduser",
            "password": "1234test",
            "role": UserRole.BUYER
        }
        self.wrong_user_data = {
            "username": "createduserwrong",
            "password": "1234",
            "role": UserRole.BUYER
        }
        self.failed_create_user_data = {
            "username": "createduser",
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
        self.user1 = User.objects.create_user(
            **self.user_data_1
        )
        self.user2 = User.objects.create_user(
            **self.user_data_2
        )
        self.user_url = reverse('accounts-user')
        self.change_password = reverse('accounts-change_password')
        self.deposit_url = reverse("deposit-list")

    def test_get_logged_in_user(self):
        response = self.client.get(self.user_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_login(self.user1)
        response = self.client.get(self.user_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        for key in self.user_data_1.keys():
            print(response.data)
            if key != "password":  # we skip Password field
                assert response.data[key] == self.user_data_1[key]

        self.client.force_login(self.user2)
        response2 = self.client.get(self.user_url)

        self.assertEqual(response2.status_code, status.HTTP_200_OK)

        for key in self.user_data_2.keys():
            if key != "password":  # we skip Password field
                assert response2.data[key] == self.user_data_2[key]

    def test_create_user(self):
        response = self.client.post(self.user_url,
                                    data=self.wrong_user_data)
        log.debug(response.data)

        response = self.client.post(self.user_url,
                                    data=self.create_user_data)
        log.debug(response.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        assert "id" in response.data.keys()

        for key in self.create_user_data.keys():
            if key != "password":  # we skip Password field
                assert response.data[key] == self.create_user_data[key]

    def test_create_user_failed(self):
        response = self.client.post(self.user_url,
                                    data=self.failed_create_user_data)
        log.debug(response.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        error_message = {
            'password': [
                ErrorDetail(
                    string='This field is required.',
                    code='required'
                )
            ],
            'role': [
                ErrorDetail(
                    string='This field is required.',
                    code='required'
                )
            ]
        }
        assert response.data == error_message

    def test_update_user(self):
        self.client.force_login(self.user1)
        new_username = "johndoeupdated"
        other_user_username = self.user_data_2["username"]

        response = self.client.put(self.user_url, {
            "username": new_username
        })
        assert response.status_code == status.HTTP_200_OK
        assert response.data["username"] == new_username

        response = self.client.put(self.user_url, {
            "username": new_username
        })
        assert response.status_code == status.HTTP_200_OK
        assert response.data["username"] == new_username

        response = self.client.put(self.user_url, {
            "username": other_user_username
        })
        log.debug(response.data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == {
            'username': [
                'Username is already taken. Please choose another one'
            ]
        }

    def test_change_password(self):
        self.client.force_login(self.user1)
        new_password = "test1234"

        response = self.client.put(self.change_password, {
            "old_password": self.user_data_1["password"],
            "new_password": new_password
        })
        log.debug(response.data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data == {
            'message': 'Password changed successfully',
            'id': 1,
            'username': 'johndoe',
            'role': 'BUYER',
            'deposit': 0
        }

        self.client.force_login(self.user1)

        response = self.client.get(self.user_url)
        log.debug(response.data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

        updated_user = User.objects.get(pk=self.user1.pk)
        self.client.force_login(updated_user)

        response = self.client.get(self.user_url)
        log.debug(response.data)
        assert response.status_code == status.HTTP_200_OK


class UserDepositAndResetViewSetTestCase(APITestCase):

    def setUp(self):
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
        self.buyer = User.objects.create_user(
            **self.user_data_1
        )
        self.buyer_deposit = 10
        self.buyer.deposit = self.buyer_deposit
        self.buyer.save()
        self.seller = User.objects.create_user(
            **self.user_data_2
        )
        self.deposit_url = reverse("deposit-list")
        self.reset_deposit_url = reverse("reset-list")

    def test_deposit_for_buyers(self):
        log.debug(self.deposit_url)
        assert self.deposit_url

        self.client.force_login(self.seller)
        deposit_data = {
            "amount": 10
        }
        response = self.client.post(
            self.deposit_url,
            deposit_data
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

        self.client.force_login(self.buyer)

        response = self.client.post(
            self.deposit_url,
            deposit_data
        )
        self.buyer.refresh_from_db()
        assert response.status_code == status.HTTP_200_OK
        assert response.data["deposit"] == self.buyer.deposit

        deposit_data["amount"] = 13

        response = self.client.post(
            self.deposit_url,
            deposit_data
        )
        self.buyer.refresh_from_db()
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == {
            'amount': ['Deposit amount can only be a multiple of 5.']
        }

    def test_reset_deposit_for_buyers(self):
        log.debug(self.reset_deposit_url)
        assert self.reset_deposit_url

        self.client.force_login(self.seller)
        response = self.client.get(
            self.reset_deposit_url,
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

        self.client.force_login(self.buyer)
        assert self.buyer.deposit == self.buyer_deposit

        response = self.client.get(
            self.reset_deposit_url
        )
        self.buyer.refresh_from_db()
        assert response.status_code == status.HTTP_200_OK
        assert response.data["deposit"] == self.buyer.deposit
        assert self.buyer.deposit == 0
