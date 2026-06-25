import configparser
import json
from time import sleep

import requests


class _EnumMeta(type):
    """Metaclass to make enum classes iterable over their string values."""

    def __iter__(cls):
        for attr_name, attr_value in cls.__dict__.items():
            if attr_name.startswith('_'):
                continue

            if isinstance(attr_value, str):
                yield attr_value


class BaseEnumerate(metaclass=_EnumMeta):
    """Basic enumerate functionality."""


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


class BaseGameClient(BaseClient):
    """Basic client for sending requests with authorization token."""

    CONFIG_PATH = 'config.ini'
    CONFIG_SECTION = 'General'
    CONFIG_TOKEN_KEY = 'TOKEN'

    def __init__(self):
        super().__init__()

        self.config = self._get_config()
        self._apply_token(self.config.get(self.CONFIG_SECTION, self.CONFIG_TOKEN_KEY, fallback=''))

    def _get_config(self):
        """Open config file."""

        config = configparser.ConfigParser()
        config.optionxform = str
        config.read(self.CONFIG_PATH)

        return config

    def _save_config(self):
        """Persist the current in-memory config back to disk."""

        with open(self.CONFIG_PATH, 'w') as fh:
            self.config.write(fh)

    def _apply_token(self, token=''):
        """Update the in-memory Authorization header with a new token."""

        self.config.set(self.CONFIG_SECTION, self.CONFIG_TOKEN_KEY, token)
        self.base_headers['Authorization'] = f'Bearer {token}'

    def set_token(self, token=''):
        """Update the bearer token both in memory and on disk."""

        self._apply_token(token)
        self._save_config()

    def is_invalid_token_error(self, response):
        """Detect the API's 'Invalid token' error in a response object."""

        if response.status_code in (401, 403, 452):
            return True

        try:
            error_block = response.json().get('error', {}) or {}
        except ValueError:
            error_block = {}

        message = (error_block.get('message') or '').lower()
        keywords = (
            'invalid token',
            'token',
            'unauthorized',
            'unauthenticated',
            'not authenticated',
            'authentication',
        )
        has_keyword = any(keyword in message for keyword in keywords)

        return has_keyword

    def request_new_token(self):
        """Ask the user for username/password, fetch a new token via /token
        and persist it to the config file. Keeps prompting until the user
        authenticates successfully or explicitly cancels. Returns True on
        success, False if the user cancels."""

        result = self._run_login_loop()

        return result

    def _run_login_loop(self):
        result = False
        attempt = 0
        done = False

        while not done:
            attempt += 1

            if attempt > 1:
                print('Please try again (or press Enter on the username prompt to cancel).')

            success, cancelled = self._try_login_once()
            if success:
                result = True
                done = True
            elif cancelled:
                result = False
                done = True

        return result

    def _try_login_once(self):
        """Return (success, cancelled) tuple for one login attempt."""
        import base64
        from getpass import getpass

        username = input('Username: ').strip()

        if not username:
            print('Login cancelled.')
            return False, True

        password = getpass('Password: ')
        credentials = base64.b64encode(
            f'{username}:{password}'.encode('utf-8')
        ).decode('ascii')

        response = self._do_request(
            method='post',
            url='/token',
            extra_headers={'Authorization': f'Basic {credentials}'},
        )

        if response.status_code == 200:
            token = response.json().get('token')
            if not token:
                print('Server returned an empty token.')
                return False, False
            self.set_token(token)
            print('New token saved to config.ini.')
            return True, False

        message, code = self._extract_error(response)
        print(f'Authentication failed: {message} (code {code})')

        return False, False

    def _prompt_yes_no(self, prompt, default=False):
        """Loop on a y/n prompt until a valid answer is given.

        Empty input is treated as `default`. The function appends
        a `[Y/n]` or `[y/N]` hint so callers don't have to include
        it manually."""
        default_label = 'Y/n' if default else 'y/N'
        result = default
        done = False

        while not done:
            answer = input(f'{prompt} [{default_label}]: ').strip().lower()
            if answer == '':
                result = default
                done = True
            elif answer in ('y', 'yes'):
                result = True
                done = True
            elif answer in ('n', 'no'):
                result = False
                done = True
            else:
                print('Please answer y or n.')

        return result

    @staticmethod
    def _extract_error(response):
        try:
            err = response.json().get('error', {}) or {}
            return err.get('message', f'HTTP {response.status_code}'), err.get('code', '?')
        except ValueError:
            return f'HTTP {response.status_code}', '?'

    def ensure_valid_token(self, probe_response=None):
        """If the most recent auth call failed because of an invalid token,
        offer the user a chance to log in again. Returns True if the token
        is now valid (either it already was, or the user re-authed)."""

        if probe_response is not None and not self.is_invalid_token_error(probe_response):
            return True

        print('The configured token is invalid or rejected by the server.')
        wants_login = self._prompt_yes_no('Do you want to log in with username and password now?')

        if wants_login:
            return self.request_new_token()

        return False

    @staticmethod
    def _get_data(response):
        """Return data block from a JSON response or an empty container."""

        try:
            payload = response.json()
        except ValueError:
            return {}

        if response.status_code >= 400:
            return {}

        return payload.get('data', {} if response.status_code == 204 else {})
