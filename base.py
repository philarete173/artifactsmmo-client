import json
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

    def _delete(self, url='', data=None):
        """Send DELETE request."""

        return self._do_request(method='delete', url=url, data=data)

    def _put(self, url='', data=None):
        """Send PUT request."""

        return self._do_request(method='put', url=url, data=data)

    def _do_request(self, method='get', url='', data=None, extra_headers=None):
        """Send request to game with simple reconnect on transient failures."""

        headers = dict(self.base_headers)
        if extra_headers:
            headers.update(extra_headers)

        params = {
            'method': method,
            'url': self.base_url + url,
            'headers': headers,
        }

        if method == 'get':
            if data:
                params['params'] = data
        else:
            if data:
                params['json'] = data

        attempts = 0
        max_attempts = 5
        while True:
            try:
                request = requests.request(**params)
                if request.status_code != 204:
                    request.json()
                break
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
                attempts += 1
                if attempts >= max_attempts:
                    raise
                sleep(1)
                continue
            except json.JSONDecodeError:
                attempts += 1
                if attempts >= max_attempts:
                    raise
                sleep(1)
                continue

        return request
