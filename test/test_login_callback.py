from .utils import Helper
from . import static


def test_missing_code(tests_helper: Helper) -> None:
    """
    Test that the login endpoint returns 302 to the error page if the code
    is missing.
    """
    path = "/users/login-callback"
    response = tests_helper.get_request(path)
    assert response.status_code == 302
    assert response.headers['Location'] == f"{static.FRONT_END_URL}/error"
