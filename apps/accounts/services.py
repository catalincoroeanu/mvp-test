from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

import jwt
from django.conf import settings
from django.contrib.auth import authenticate

from apps.accounts.choices import UserRole
from apps.accounts.models import User


def create_user(*,
                username: str,
                password: str,
                role: UserRole,
                **kwargs) -> Tuple[User, dict]:
    errors = {}
    user = User.objects.create_user(
        username=username,
        password=password,
        role=role,
        **kwargs
    )
    return user, errors


def update_user(*, pk, username) -> Tuple[User, dict]:
    errors = {}
    user = User.objects.get(pk=pk)
    try:
        other_user = User.objects.get(username=username)
        errors["username"] = ["Username is already taken. "
                              "Please choose another one"]
        if other_user.pk == user.pk:
            errors = {}
    except User.DoesNotExist:
        user.username = username
        user.save()
    return user, errors


def change_password(*, pk, old_password, new_password) -> Tuple[User, dict]:
    errors = {}
    user = User.objects.get(pk=pk)
    if user.check_password(raw_password=old_password):
        user.password = new_password
        user.save()
    else:  # pragma: no cover
        errors["old_password"] = ["Old password didn't match"]
    return user, errors


def deposit_amount(*,
                   amount: int,
                   buyer: User) -> Tuple[Optional[dict], dict]:
    deposit_response, errors = None, {}

    error_message = validate_user_deposit(amount=amount)
    if error_message:
        errors = {
            "amount": error_message
        }
    else:
        buyer.deposit = buyer.deposit + amount
        buyer.save()
        deposit_response = {
            "deposit": buyer.deposit
        }
    return deposit_response, errors


def validate_user_deposit(amount: int):
    errors = []
    if amount % 5:
        errors.append("Deposit amount can only be a multiple of 5.")
    if amount > 100 or amount < 0:
        errors.append("Deposit amount can be set values between 0 to 100.")
    return errors


def reset_deposit(*, buyer: User) -> dict:
    buyer.deposit = 0
    buyer.save()
    reset_deposit_response = {
        "deposit": buyer.deposit
    }

    return reset_deposit_response


def obtain_jwt_token(*, username, password) -> Tuple[Optional[dict], dict]:
    login_response, errors = None, {}
    user = authenticate(username=username, password=password)

    if not user:
        errors = {
            "details": "Authentication failed. Make sure to provide "
                       "the correct credentials."
        }
    else:
        token, expires_at = generate_jwt_token(user)
        login_response = {
            "token": token,
            "expires_at": expires_at
        }

    return login_response, errors


def generate_jwt_token(user: User):
    expires_at = (
        datetime.now(tz=timezone.utc)
        + timedelta(hours=settings.JWT_EXPIRY_HOURS)
    )
    payload = {
        "iss": settings.JWT_ISS,
        "iat": datetime.now(tz=timezone.utc),
        "exp": expires_at,
        "username": user.username,
    }
    token = jwt.encode(
        payload=payload,
        key=settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return token, expires_at
