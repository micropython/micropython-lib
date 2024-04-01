import requests
import email.utils

# Configurable settings
server_url = 'http://tzdata.net/api/1/'
dataset = '1-15'


def fetch(url, last_modified, timeout=None):
    headers = {}
    if last_modified:
        headers['if-modified-since'] = email.utils.formatdate(last_modified, False, True)

    resp = requests.request('GET', url, headers=headers, timeout=timeout, parse_headers=True)

    if resp.status_code == 304:
        # Not modified
        resp.close()
        return None
    if resp.status_code != 200:
        resp.close()
        raise Exception()

    content = resp.content

    last_modified = resp.get_date_as_int('last-modified') or 0

    return (last_modified, content)


def fetch_zone(zone_name, last_modified, timeout=None):
    url = server_url + dataset + '/zones-minitzif/' + zone_name
    return fetch(url, last_modified, timeout)


def fetch_all(last_modified, timeout=None):
    url = server_url + dataset + '/minitzdb'
    return fetch(url, last_modified, timeout)


def fetch_names(last_modified, timeout=None):
    url = server_url + 'zone-names-mini'
    return fetch(url, last_modified, timeout)
