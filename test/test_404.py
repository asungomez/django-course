import requests


def test_404(api_url: str) -> None:
    """Test that unknown routes return 404."""
    path = "/unknown"
    url = f"{api_url}{path}"
    response = requests.get(url)
    assert response.status_code == 404
