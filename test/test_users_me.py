from .utils import Helper
from .factories.user import user_factory


def test_without_auth_data(tests_helper: Helper) -> None:
    """
    Test that the current user endpoint returns 401 if there's no
    authentication data (header or cookies) in the request.
    """
    path = "/users/me"
    response = tests_helper.get_request(path)
    assert response.status_code == 401


def test_authenticated_as_non_existent_user(tests_helper: Helper) -> None:
    """
    Test that the current user endpoint returns 401 if the user does not
    exist in the database.
    """
    path = "/users/me"
    email = "not.existing.email@email.net"
    response = tests_helper.get_request(
        path,
        authenticated_as=email,
    )
    assert response.status_code == 401


def test_authenticated_as_existent_user(tests_helper: Helper) -> None:
    """
    Test that the current user endpoint returns 200 if the user exists
    in the database.
    """
    path = "/users/me"
    email = "existing.email@email.net"
    user = user_factory({
        "email": email,
    })
    tests_helper.insert_user(user)
    response = tests_helper.get_request(
        path,
        authenticated_as=email,
    )
    assert response.status_code == 200
