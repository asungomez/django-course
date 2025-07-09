from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.views import View

from core.auth import TokenManager

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
            at, rt = token_manager.get_tokens_from_provider(code)
            email, at, rt = token_manager.authenticate(at, rt)
            try:
                self.serializer.find_by_email(email)
            except User.DoesNotExist:
                self.serializer.create({"email": email})

            response = redirect(f"{settings.FRONT_END_URL}/profiles")
            token_manager.set_credentials_as_cookie(response, at, rt)
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
