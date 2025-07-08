import json
from typing import Optional

import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.middleware import AuthenticationMiddleware
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest

from user.serializers import UserSerializer

User = get_user_model()


class TokenManager:
    """
    Class to manage Okta authentication and token handling
    """

    def get_email_from_token(self, token: str) -> str:
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
            decoded_token = json.loads(token)
            # Get the email from the decoded token
            mock_email: str = decoded_token.get('sub')
            return mock_email

        url = f"{settings.OKTA['DOMAIN']}/userinfo"
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {token}"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        userinfo = response.json()
        email: str = userinfo.get("email")
        if not email:
            raise ValueError("Email not found in the token")
        return email

    def get_access_token(self, code: str) -> str:
        """
        Make a request to Okta to retrieve the access token based on the
        code

        :param code: The authorization code received from Okta

        :return: The access token
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
        access_token: str = response.json()["access_token"]
        return access_token

    def get_token_from_request(self, request: HttpRequest) -> Optional[str]:
        """
        Get the token from the request. It checks both the cookies and the
        Authorization header.

        :param request: The request object

        :return: The token if found, otherwise None
        """
        token = request.COOKIES.get(settings.TOKEN_COOKIE_CONFIG["NAME"])
        if token is None:
            auth_header = request.headers.get("Authorization")
            if auth_header:
                header_parts = auth_header.split(" ")
                if len(header_parts) >= 2 and header_parts[0] == "Bearer":
                    token = " ".join(header_parts[1:])
        return token


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
            token = self.verifier.get_token_from_request(request)
            if token is None:
                request.user = AnonymousUser()
                return
            email = self.verifier.get_email_from_token(token)
            user = self.serializer.find_by_email(email)
            request.user = user
        except Exception as e:
            print(f"Authentication failed: {str(e)}")
            request.user = AnonymousUser()
