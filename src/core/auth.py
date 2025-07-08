import json
from typing import Optional, Tuple

import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.middleware import AuthenticationMiddleware
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest

from core.crypto import Crypto
from user.serializers import UserSerializer

User = get_user_model()


class TokenManager:
    """
    Class to manage Okta authentication and token handling
    """

    def get_email_from_tokens(
        self,
        access_token: str,
        refresh_token: str
    ) -> str:
        """
        Get the email from the token. It decodes the token and retrieves
        the email from the claims.

        :param token: The JWT token received from Okta

        :return: The email address from the token
        """
        # In testing environments we don't use real Okta, so the token is
        # just a JSON string containing the claims
        if settings.MOCK_AUTH:
            # Decode the token as a JSON string
            decoded_token = json.loads(access_token)
            # Get the email from the decoded token
            mock_email: str = decoded_token.get('sub')
            return mock_email

        url = f"{settings.OKTA['DOMAIN']}/userinfo"
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {access_token}"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        userinfo = response.json()
        email: str = userinfo.get("email")
        if not email:
            raise ValueError("Email not found in the token")
        return email

    def get_tokens_from_provider(self, code: str) -> Tuple[str, str]:
        """
        Make a request to Okta to retrieve the access token based on the
        code

        :param code: The authorization code received from Okta

        :return: The access token and refresh token
        """
        url = f"{settings.OKTA['DOMAIN']}/oauth/token"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        }
        payload = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.OKTA["LOGIN_REDIRECT"],
            "client_id": settings.OKTA["CLIENT_ID"],
            "client_secret": settings.OKTA["CLIENT_SECRET"]
        }
        response = requests.post(url, headers=headers, data=payload)
        response.raise_for_status()
        access_token: str = response.json().get("access_token")
        refresh_token: str = response.json().get("refresh_token")
        return access_token, refresh_token

    def get_tokens_from_request(self, request: HttpRequest) -> Optional[
        Tuple[str, str]
    ]:
        """
        Get the tokens from the request. It checks both the cookies and the
        Authorization header.

        :param request: The request object

        :return: A tuple containing the access token and refresh token, or None
        """
        encrypted_credentials = request.COOKIES.get(
            settings.AUTH_COOKIE_CONFIG["NAME"]
            )
        if encrypted_credentials is None:
            auth_header = request.headers.get("Authorization")
            if auth_header:
                header_parts = auth_header.split(" ")
                if len(header_parts) >= 2 and header_parts[0] == "Bearer":
                    access_token = " ".join(header_parts[1:])
                    refresh_token = 'placeholder_refresh_token'
        else:
            crypto = Crypto()
            credentials_json = crypto.decrypt(encrypted_credentials)
            credentials = json.loads(credentials_json)
            access_token = credentials.get("access_token")
            refresh_token = credentials.get("refresh_token")
        return access_token, refresh_token


class CustomAuthMiddleware(AuthenticationMiddleware):
    """
    Custom authentication middleware to handle Okta authentication
    """

    verifier = TokenManager()
    serializer = UserSerializer()

    def process_request(self, request: HttpRequest) -> None:
        """
        Process the request to authenticate the user based on the token

        :param request: The request object
        """
        try:
            at, rt = self.verifier.get_tokens_from_request(request)
            if at is None:
                request.user = AnonymousUser()
                return
            email = self.verifier.get_email_from_tokens(at, rt)
            user = self.serializer.find_by_email(email)
            request.user = user
        except Exception as e:
            print(f"Authentication failed: {str(e)}")
            request.user = AnonymousUser()
