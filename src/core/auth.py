import json
from typing import Optional, Tuple

import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.middleware import AuthenticationMiddleware
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest, HttpResponse

from core.crypto import Crypto
from user.serializers import UserSerializer

User = get_user_model()


class TokenManager:
    """
    Class to manage Okta authentication and token handling
    """

    def authenticate(
        self,
        access_token: str,
        refresh_token: str
    ) -> Tuple[str, str, str]:
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
        if response.status_code == 401:
            access_token = self.get_access_token_from_refresh_token(
                refresh_token
                )
            headers["Authorization"] = f"Bearer {access_token}"
            response = requests.get(url, headers=headers)
        response.raise_for_status()
        userinfo = response.json()
        email: str = userinfo.get("email")
        if not email:
            raise ValueError("Email not found in the token")
        return email, access_token, refresh_token

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

    def get_access_token_from_refresh_token(
        self, refresh_token: str
    ) -> str:
        """
        Get a new access token using the refresh token
        :param refresh_token: The refresh token to use for getting a new
        access token
        :return: The new access token
        """
        url = f"{settings.OKTA['DOMAIN']}/oauth/token"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        }
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": settings.OKTA["CLIENT_ID"],
            "client_secret": settings.OKTA["CLIENT_SECRET"]
        }
        response = requests.post(url, headers=headers, data=payload)
        response.raise_for_status()
        return response.json().get("access_token")

    def set_credentials_as_cookie(self, response: HttpResponse,
                                  access_token: str,
                                  refresh_token: str) -> None:
        """
        Set the access and refresh tokens as a cookie in the response
        :param response: The response object
        :param access_token: The access token to set in the cookie
        :param refresh_token: The refresh token to set in the cookie
        """
        crypto = Crypto()
        credentials_map = {
            "access_token": access_token,
            "refresh_token": refresh_token,
        }
        credentials = json.dumps(credentials_map)
        encrypted_credentials = crypto.encrypt(credentials)

        response.set_cookie(
            key=settings.AUTH_COOKIE_CONFIG["NAME"],
            value=encrypted_credentials,
            domain=settings.AUTH_COOKIE_CONFIG["DOMAIN"],
            path=settings.AUTH_COOKIE_CONFIG["PATH"],
            expires=settings.AUTH_COOKIE_CONFIG["LIFETIME"],
            secure=settings.AUTH_COOKIE_CONFIG["SECURE"],
            httponly=settings.AUTH_COOKIE_CONFIG["HTTP_ONLY"],
            samesite=settings.AUTH_COOKIE_CONFIG["SAMESITE"],
        )


class CustomAuthMiddleware(AuthenticationMiddleware):
    """
    Custom authentication middleware to handle Okta authentication
    """

    verifier = TokenManager()
    serializer = UserSerializer()
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None

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
            self.access_token = at
            self.refresh_token = rt
            email, at, rt = self.verifier.authenticate(at, rt)
            user = self.serializer.find_by_email(email)
            request.user = user
        except Exception as e:
            print(f"Authentication failed: {str(e)}")
            request.user = AnonymousUser()

    def process_response(
        self,
        _: HttpRequest,
        response: HttpResponse
    ) -> HttpResponse:
        """
        Process the response to set the access and refresh tokens as cookies.
        :param _: The request object (not used)
        :param response: The response object
        :return: The response object with the cookies set
        """
        if self.access_token and self.refresh_token:
            self.verifier.set_credentials_as_cookie(
                response, self.access_token, self.refresh_token
            )
        return response
