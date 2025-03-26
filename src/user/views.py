from django.http import HttpResponse, HttpRequest, JsonResponse
from django.views import View
from django.shortcuts import redirect
from django.conf import settings
from .okta import get_access_token, get_email_from_token
from .serializers import UserSerializer
from django.contrib.auth import get_user_model


User = get_user_model()


class LoginView(View):

    serializer = UserSerializer()

    def get(self, request: HttpRequest) -> HttpResponse:
        code = request.GET.get("code")
        if code is None:
            return redirect(f"{settings.FRONT_END_URL}/error")
        try:
            access_token = get_access_token(code)
            email = get_email_from_token(access_token)
            try:
                self.serializer.find_by_email(email)
            except User.DoesNotExist:
                self.serializer.create({"email": email})
            response = redirect(f"{settings.FRONT_END_URL}/profiles")
            response.set_cookie(
                key=settings.TOKEN_COOKIE_CONFIG["NAME"],
                value=access_token,
                domain=settings.TOKEN_COOKIE_CONFIG["DOMAIN"],
                path=settings.TOKEN_COOKIE_CONFIG["PATH"],
                expires=settings.TOKEN_COOKIE_CONFIG["LIFETIME"],
                secure=settings.TOKEN_COOKIE_CONFIG["SECURE"],
                httponly=settings.TOKEN_COOKIE_CONFIG["HTTP_ONLY"],
                samesite=settings.TOKEN_COOKIE_CONFIG["SAMESITE"],
            )
            return response
        except Exception as e:
            print(e)
            return redirect(f"{settings.FRONT_END_URL}/error")


class CurrentUserView(View):

    serializer = UserSerializer()

    def get(self, request: HttpRequest) -> HttpResponse:
        token = request.COOKIES.get(settings.TOKEN_COOKIE_CONFIG["NAME"])
        if token is None:
            return HttpResponse(status=401)
        try:
            email = get_email_from_token(token)
            user = self.serializer.find_by_email(email)
            return JsonResponse({"user": self.serializer.to_dict(user)})
        except Exception as e:
            json_error = {"error": str(e)}
            return JsonResponse(json_error, status=401)
