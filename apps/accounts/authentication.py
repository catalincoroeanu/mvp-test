import jwt
from rest_framework import HTTP_HEADER_ENCODING, authentication
from django.conf import settings
from rest_framework.exceptions import AuthenticationFailed

from apps.accounts.models import User


AUTH_HEADER_TYPES = settings.JWT["allowed_header"]

AUTH_HEADER_TYPE_BYTES = set(
    h.encode(HTTP_HEADER_ENCODING)
    for h in AUTH_HEADER_TYPES
)


class JWTAuthentication(authentication.BaseAuthentication):
    www_authenticate_realm = 'api'

    def authenticate(self, request):
        header = self.get_header(request)
        if header is None:
            return None

        raw_token = self.get_raw_token(header)
        if raw_token is None:
            return None

        validated_token, errors = self.get_validated_token(raw_token)

        if not validated_token:
            raise AuthenticationFailed(**errors)

        return self.get_user(validated_token), validated_token

    def authenticate_header(self, request):
        return '{0} realm="{1}"'.format(
            AUTH_HEADER_TYPES[0],
            self.www_authenticate_realm,
        )

    def get_header(self, request):
        """
        Extracts the header containing the JSON web token from the given
        request.
        """
        header = request.META.get('HTTP_AUTHORIZATION')
        if isinstance(header, str):
            # Work around django test client oddness
            header = header.encode(HTTP_HEADER_ENCODING)

        return header

    def get_raw_token(self, header):
        """
        Extracts an unvalidated JSON web token from the given "Authorization"
        header value.
        """
        parts = header.split()

        if len(parts) == 0:
            # Empty AUTHORIZATION header sent
            return None

        if parts[0] not in AUTH_HEADER_TYPE_BYTES:
            # Assume the header does not contain a JSON web token
            return None

        if len(parts) != 2:
            raise AuthenticationFailed()

        return parts[1]

    def get_validated_token(self, raw_token):
        """
        Validates an encoded JSON web token and returns a validated token
        wrapper object.
        """
        payload, error = None, {}
        try:
            payload = jwt.decode(
                raw_token,
                settings.SECRET_KEY,
                algorithms=[settings.JWT["algorithm"]]
            )
        except Exception as e:
            error = {
                'detail': f'Authentication failed: {e.args[0]}'
            }
        return payload, error

    def get_user(self, validated_token):
        """
        Attempts to find and return a user using the given validated token.
        """
        try:
            user_username = validated_token["username"]
        except KeyError:
            raise AuthenticationFailed(
                'Token contained no recognizable user identification'
            )

        try:
            user = User.objects.get(username=user_username)
        except User.DoesNotExist:
            raise AuthenticationFailed('User not found',
                                       code='user_not_found')

        if not user.is_active:
            raise AuthenticationFailed('User is inactive',
                                       code='user_inactive')

        return user
