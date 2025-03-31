from .utils import Helper
from . import static
import json
from .factories.user import user_factory


def test_missing_code(tests_helper: Helper) -> None:
    """
    Test that the login endpoint returns 302 to the error page if the code
    is missing.
    """
    path = "/users/login-callback"
    response = tests_helper.get_request(path)
    assert response.status_code == 302
    assert response.headers['Location'] == f"{static.FRONT_END_URL}/error"


def test_error_from_okta(tests_helper: Helper) -> None:
    """
    Test that the login endpoint returns 302 to the error page if Okta
    returns an error.
    """
    path = "/users/login-callback?code=123"
    tests_helper.mock_okta_token_response(
        response_body={
            "error": "invalid_grant",
            "error_description": "Invalid code",
        },
        response_status=400,
    )
    response = tests_helper.get_request(path)
    assert response.status_code == 302
    assert response.headers['Location'] == f"{static.FRONT_END_URL}/error"


def test_user_does_not_exist(tests_helper: Helper) -> None:
    """
    Test that the login endpoint creates a new user and returns 302 to the
    profiles page if the user does not exist.
    """
    user_email = "not.existing.user@email.net"
    path = "/users/login-callback?code=123"
    access_token = json.dumps({
        "sub": user_email
    })
    tests_helper.mock_okta_token_response(
        response_body={
            "access_token": access_token,
        },
        response_status=200,
    )
    response = tests_helper.get_request(path)
    assert response.status_code == 302
    assert response.headers['Location'] == f"{static.FRONT_END_URL}/profiles"
    stored_user = tests_helper.find_user_by_email(
        user_email,
    )
    assert stored_user is not None


def test_user_exists(tests_helper: Helper) -> None:
    """
    Test that the login endpoint returns 302 to the profiles page if the
    user exists.
    """
    user_email = "existing.user@email.net"
    user = user_factory(
        {
            "email": user_email,
        }
    )
    tests_helper.insert_user(user)
    path = "/users/login-callback?code=123"
    access_token = json.dumps({
        "sub": user_email
    })
    tests_helper.mock_okta_token_response(
        response_body={
            "access_token": access_token,
        },
        response_status=200,
    )
    response = tests_helper.get_request(path)
    assert response.status_code == 302
    assert response.headers['Location'] == f"{static.FRONT_END_URL}/profiles"
