import json
import os
import time
import urllib.parse as urlparse

import urequests as requests


def _exists(path):
    '''
    Return True if the path exists.
    '''

    try:
        os.stat(path)
        return True
    except OSError:
        return False


class DeviceAuth:
    '''
    Helps with authenticating devices with limited input capabilities
    per the OAuth2 device flow specification.
    '''

    def __init__(
        self,
        client_id,
        client_secret,
        discovery_endpoint,
        scopes=list(),
        saved_location=None
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.discovery_endpoint = discovery_endpoint
        self.scopes = scopes
        self.saved_location = saved_location

        self.user_code = None
        self.verification_url = None

        self._discovered = False
        self._authorization_started = False
        self._authorization_completed = False

        self._device_auth_endpoint = None
        self._token_endpoint = None
        self._device_code = None
        self._interval = None
        self._code_expires_in = None

        self._access_token = None
        self._token_acquired_at = None
        self._token_expires_in = None
        self._token_scope = None
        self._token_type = None
        self._refresh_token = None

    def discover(self):
        '''
        Performs OAuth2 device endpoint discovery.
        '''

        if not self._discovered:
            r = requests.request('GET', self.discovery_endpoint)
            j = r.json()
            self._device_auth_endpoint = j['device_authorization_endpoint']
            self._token_endpoint = j['token_endpoint']
            self._discovered = True
            r.close()

        saved = self.save()
        if not saved:
            print('Unable to save auth state.')

    def authorize(self):
        '''
        Makes an authorization request.
        '''

        if not self._discovered:
            print('Need to discover authorization and token endpoints.')
            return

        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        payload = {
            'client_id': self.client_id,
            'scope': ' '.join(self.scopes)
        }
        encoded = urlparse.urlencode(payload)
        r = requests.request(
            'POST',
            self._device_auth_endpoint,
            data=encoded,
            headers=headers
        )
        j = r.json()
        r.close()

        if 'error' in j:
            raise RuntimeError(j['error'])

        self._device_code = j['device_code']
        self.user_code = j['user_code']
        self.verification_url = j['verification_url']
        self._interval = j['interval']
        self._code_expires_in = j['expires_in']
        self._authorization_started = True
        message = 'Use code %s at %s to authorize the device.' % (
            self.user_code,
            self.verification_url
        )
        print(message)

    def check_authorization_complete(self, sleep_duration_seconds=5, max_attempts=10):
        '''
        Polls until completion of an authorization request.
        '''

        if not self._authorization_started:
            print('Start an authorization request.')
            return

        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        payload = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'device_code': self._device_code,
            'grant_type': 'urn:ietf:params:oauth:grant-type:device_code'
        }
        encoded = urlparse.urlencode(payload)

        current_attempt = 0
        while not self.authorized and current_attempt < max_attempts:
            current_attempt = current_attempt + 1
            r = requests.request(
                'POST',
                self._token_endpoint,
                data=encoded,
                headers=headers
            )
            j = r.json()
            r.close()
            if 'error' in j:
                if j['error'] == 'authorization_pending':
                    print('Pending authorization. ')
                    time.sleep(sleep_duration_seconds)
                elif j['error'] == 'access_denied':
                    print('Access denied')
                    raise RuntimeError(j['error'])
            else:
                self._access_token = j['access_token']
                self._token_acquired_at = int(time.time())
                self._token_expires_in = j['expires_in']
                self._token_scope = j['scope']
                self._token_type = j['token_type']
                self._refresh_token = j['refresh_token']
                print('Completed authorization')
                self._authorization_completed = True
                saved = self.save()
                if not saved:
                    print('Unable to save auth state.')

    @property
    def authorized(self):
        return self._authorization_completed

    def token(self, force_refresh=False):
        '''
        Fetches a valid access token.
        '''

        if not self._authorization_completed:
            print('Complete an authorization request')
            return

        buffer = 10 * 60 * -1  # 10 min in seconds
        now = int(time.time())
        is_valid = now < (
            self._token_acquired_at +
            self._token_expires_in +
            buffer
        )
        if not is_valid or force_refresh:
            print('Token expired. Refreshing access tokens.')
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}
            payload = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'refresh_token': self._refresh_token,
                'grant_type': 'refresh_token'
            }
            encoded = urlparse.urlencode(payload)
            r = requests.request(
                'POST',
                self._token_endpoint,
                data=encoded,
                headers=headers
            )
            status_code = r.status_code
            j = r.json()
            r.close()

            if status_code == 400:
                print('Unable to refresh tokens.')
                raise(RuntimeError('Unable to refresh tokens.'))

            print('Updated access tokens.')
            self._access_token = j['access_token']
            self._token_acquired_at = int(time.time())
            self._token_expires_in = j['expires_in']
            self._token_scope = j['scope']
            self._token_type = j['token_type']

            saved = self.save()
            if not saved:
                print('Unable to store auth state.')

        return self._access_token

    def save(self):
        '''
        Serializes the auth state to a JSON payload and saves it in `location`.
        '''

        if not self.saved_location:
            return True

        payload = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'discovery_endpoint': self.discovery_endpoint,
            'scopes': self.scopes
        }

        if self.saved_location:
            payload['saved_location'] = self.saved_location

        if self._discovered:
            payload['discovered'] = True
            payload['device_auth_endpoint'] = self._device_auth_endpoint
            payload['token_endpoint'] = self._token_endpoint

        if self.authorized:
            payload['authorized'] = True
            payload['refresh_token'] = self._refresh_token
            payload['access_token'] = self._access_token
            payload['token_acquired_at'] = self._token_acquired_at
            payload['token_expires_in'] = self._token_expires_in

        try:
            with open(self.saved_location, 'w') as handle:
                json.dump(payload, handle)
                print('Saved auth state.')

            return True
        except OSError as error:
            print('Error saving authentication state.', error)
            return False

    @classmethod
    def from_file(cls, location):
        '''
        Loads authentication state from a given location.
        '''
        if not _exists(location):
            print('No serialized state.')
            return None

        try:
            with open(location, 'r') as handle:
                payload = json.load(handle)
                client_id = payload['client_id']
                client_secret = payload['client_secret']
                discovery_endpoint = payload['discovery_endpoint']
                scopes = payload['scopes']
                device_auth = DeviceAuth(
                    client_id=client_id,
                    client_secret=client_secret,
                    discovery_endpoint=discovery_endpoint,
                    scopes=scopes
                )

                if 'saved_location' in payload:
                    saved_location = payload['saved_location']
                    device_auth.saved_location = saved_location

                if 'discovered' in payload:
                    device_auth_endpoint = payload['device_auth_endpoint']
                    token_endpoint = payload['token_endpoint']
                    device_auth._discovered = True
                    device_auth._device_auth_endpoint = device_auth_endpoint
                    device_auth._token_endpoint = token_endpoint

                if 'authorized' in payload:
                    refresh_token = payload['refresh_token']
                    access_token = payload['access_token']
                    token_acquired_at = payload['token_acquired_at']
                    token_expires_in = payload['token_expires_in']
                    device_auth._authorization_completed = True
                    device_auth._refresh_token = refresh_token
                    device_auth._access_token = access_token
                    device_auth._token_acquired_at = token_acquired_at
                    device_auth._token_expires_in = token_expires_in

                return device_auth
        except Exception as error:
            print('Unable to create an instance of DeviceAuth.', error)
            try:
                os.remove(location)
            except OSError as error:
                # Do nothing
                pass

            return None
