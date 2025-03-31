from .utils import Helper


def test_404(tests_helper: Helper) -> None:
    """Test that unknown routes return 404."""
    path = "/unknown"
    response = tests_helper.get_request(path)
    assert response.status_code == 404
