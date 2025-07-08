import json

from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.views import View

from core.auth import TokenManager
from core.crypto import Crypto

from .serializers import UserSerializer

User = get_user_model()


class LoginView(View):

    serializer = UserSerializer()

    def get(self, request: HttpRequest) -> HttpResponse:
        code = request.GET.get("code")
        if code is None:
            return redirect(f"{settings.FRONT_END_URL}/error")
        try:
            token_manager = TokenManager()
            access_token = token_manager.get_access_token(code)
            email = token_manager.get_email_from_token(access_token)
            try:
                self.serializer.find_by_email(email)
            except User.DoesNotExist:
                self.serializer.create({"email": email})

            crypto = Crypto()
            credentials_map = {
                "access_token": access_token,
            }
            credentials = json.dumps(credentials_map)
            encrypted_credentials = crypto.encrypt(credentials)
            response = redirect(f"{settings.FRONT_END_URL}/profiles")
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
            return response
        except Exception as e:
            print(e)
            return redirect(f"{settings.FRONT_END_URL}/error")


class CurrentUserView(View):
    serializer = UserSerializer()

    def get(self, request: HttpRequest) -> HttpResponse:
        try:
            if not request.user.is_authenticated:
                return JsonResponse({"error": "Not authenticated"}, status=401)
            email = request.user.email
            user = self.serializer.find_by_email(email)
            return JsonResponse({"user": self.serializer.to_dict(user)})
        except Exception as e:
            json_error = {"error": str(e)}
            return JsonResponse(json_error, status=401)
