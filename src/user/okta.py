from django.conf import settings
import requests
from jwt import (
    PyJWKClient,
    decode,
    )


# Initialize the JWK client
jwks_client = PyJWKClient(f"{settings.OKTA["DOMAIN"]}/oauth2/default/v1/keys")


def get_email_from_token(token: str) -> str:
  # Get the signing key
  signing_key = jwks_client.get_signing_key_from_jwt(token)

  # Decode and verify the token
  decoded_token = decode(
      token,
      signing_key.key,
      algorithms=["RS256"],
      audience="api://default",
      options={"verify_exp": True}
  )

  # Get the email
  email = decoded_token.get('sub')

  return email


def get_access_token(code: str) -> str:
  """Make a request to Okta to retrieve the access token based on the code"""
  url = f"{settings.OKTA["DOMAIN"]}/oauth2/default/v1/token"
  headers = {
    "Content-Type": "application/x-www-form-urlencoded",
    "Accept": "application/json",
  }
  payload = {
    "grant_type": "authorization_code",
    "code": code,
    "redirect_uri": settings.OKTA["LOGIN_REDIRECT"],
    "client_id": settings.OKTA["CLIENT_ID"],
    "client_secret": settings.OKTA["CLIENT_SECRET"],
  }
  response = requests.post(url, headers=headers, data=payload)
  response.raise_for_status()
  return response.json()["access_token"]
