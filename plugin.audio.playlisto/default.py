import sys
import json
import urllib.request
import urllib.parse

import xbmcplugin
import xbmcgui
import xbmcaddon

addon = xbmcaddon.Addon()
addon_handle = int(sys.argv[1])

BASE_URL = addon.getSetting("server")

xbmcplugin.setContent(addon_handle, "songs")


def fetch_playlist():

    url = BASE_URL + "/api/load-folder"

    req = urllib.request.Request(url, method="POST")

    try:
        response = urllib.request.urlopen(req)
        data = json.loads(response.read().decode())

        return data.get("files", [])

    except Exception:

        xbmcgui.Dialog().notification(
            "Playlisto",
            "Failed to load source",
            xbmcgui.NOTIFICATION_ERROR,
            4000
        )

        return []


def list_songs():

    songs = fetch_playlist()

    for file in songs:

        stream_url = (
            BASE_URL
            + "/api/stream/"
            + file["id"]
            + "?filename="
            + urllib.parse.quote(file["name"])
        )

        li = xbmcgui.ListItem(label=file["name"])
        li.setProperty("IsPlayable", "true")

        xbmcplugin.addDirectoryItem(
            handle=addon_handle,
            url=stream_url,
            listitem=li,
            isFolder=False
        )

    xbmcplugin.endOfDirectory(addon_handle)


if __name__ == "__main__":
    list_songs()
