import requests


class Helper:
    """
    Helper class with utilities for tests: requests to the API, creating
    mocks, etc.
    """

    api_url: str = None

    def __init__(self, api_url):
        self.api_url = api_url

    def get_request(self, path: str) -> requests.Response:
        """Make a request to the API."""
        url = f"{self.api_url}{path}"
        response = requests.get(url, allow_redirects=False)
        return response
