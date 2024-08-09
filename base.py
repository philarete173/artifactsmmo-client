from time import sleep

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

        return self._do_request(method='post', url=url, data=data)

    def _get(self, url='', data=None):
        """Send GET request."""

        return self._do_request(method='get', url=url, data=data)

    def _do_request(self, method='get', url='', data=None):
        """Send request to game."""

        params = {
            'method': method,
            'url': self.base_url + url,
            'headers': self.base_headers,
        }

        if method == 'get':
            params.update(params=data or {})
        elif method == 'post':
            params.update(json=data or {})

        while True:
            try:
                request = requests.request(**params)
                request.json()
                break
            except (requests.exceptions.ConnectionError, requests.exceptions.JSONDecodeError):
                sleep(1)
                continue

        return request
