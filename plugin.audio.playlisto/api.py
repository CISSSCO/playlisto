import json
import urllib.request
import urllib.parse
import xbmcaddon

addon = xbmcaddon.Addon()

def base():

    return addon.getSetting("server")


def get(url):

    response = urllib.request.urlopen(base() + url)
    return json.loads(response.read().decode())


def post(url, data=None):

    if data:
        data = json.dumps(data).encode()

    req = urllib.request.Request(
        base() + url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    response = urllib.request.urlopen(req)
    return json.loads(response.read().decode())


def delete(url):

    req = urllib.request.Request(
        base() + url,
        method="DELETE"
    )

    urllib.request.urlopen(req)
