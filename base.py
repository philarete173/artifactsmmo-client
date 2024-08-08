import requests


class BaseClient:
    """Basic client for sending requests."""

    def __init__(self):
        self.base_url = "https://api.artifactsmmo.com"

        self.base_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _post(self, url='', data=None):
        """Send POST request."""

        return requests.post(url=self.base_url + url, json=data or {}, headers=self.base_headers)

    def _get(self, url='', data=None):
        """Send GET request."""

        return requests.get(url=self.base_url + url, params=data or {}, headers=self.base_headers)
