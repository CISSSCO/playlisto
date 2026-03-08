import sys
import urllib.parse

import xbmcplugin
import xbmcgui
import xbmcaddon

import api


addon = xbmcaddon.Addon()
addon_handle = int(sys.argv[1])


params = dict(
    urllib.parse.parse_qsl(sys.argv[2][1:])
)

action = params.get("action")


def play_active():

    data = api.post("/api/load-folder")

    files = data.get("files", [])

    for file in files:

        stream = (
            addon.getSetting("server")
            + "/api/stream/"
            + file["id"]
            + "?filename="
            + urllib.parse.quote(file["name"])
        )

        li = xbmcgui.ListItem(label=file["name"])
        li.setProperty("IsPlayable", "true")

        xbmcplugin.addDirectoryItem(
            handle=addon_handle,
            url=stream,
            listitem=li,
            isFolder=False
        )

    xbmcplugin.endOfDirectory(addon_handle)


def add_provider():

    dialog = xbmcgui.Dialog()

    name = dialog.input("Provider Name")

    api_key = dialog.input("Google Drive API Key")

    api.post(
        "/api/providers",
        {"name": name, "api_key": api_key}
    )

    dialog.notification("Playlisto", "Provider added")


def list_providers():

    data = api.get("/api/providers")

    names = [p["name"] for p in data]

    dialog = xbmcgui.Dialog()

    i = dialog.select("Activate Provider", names)

    if i >= 0:

        api.post("/api/providers/activate/" + data[i]["id"])

        dialog.notification("Playlisto", "Provider activated")


def add_source():

    dialog = xbmcgui.Dialog()

    name = dialog.input("Source Name")

    url = dialog.input("Google Drive Folder URL")

    providers = api.get("/api/providers")

    provider_names = [p["name"] for p in providers]

    i = dialog.select("Select Provider", provider_names)

    if i < 0:
        return

    api.post(
        "/api/sources",
        {
            "name": name,
            "url": url,
            "provider_id": providers[i]["id"]
        }
    )

    dialog.notification("Playlisto", "Source added")


def list_sources():

    data = api.get("/api/sources")

    names = [s["name"] for s in data["sources"]]

    dialog = xbmcgui.Dialog()

    i = dialog.select("Activate Source", names)

    if i >= 0:

        api.post(
            "/api/sources/activate/"
            + data["sources"][i]["id"]
        )

        dialog.notification("Playlisto", "Source activated")


if action == "add_provider":
    add_provider()

elif action == "list_providers":
    list_providers()

elif action == "add_source":
    add_source()

elif action == "list_sources":
    list_sources()

else:
    play_active()
