#!/usr/bin/python3
"""
Download the extensions Mullvad Browser ships with from addons.mozilla.org
(the AMO-signed builds), verifying each file against the sha256 that AMO
publishes for it, and save them as <guid>.xpi -- the names
distribution/extensions/ expects.

usage: fetch-extensions.py <destdir> <guid>[?] ...
A trailing "?" marks an extension as optional: failing to fetch it only
prints a warning.
"""

import hashlib
import json
import sys
import urllib.parse
import urllib.request

API = "https://addons.mozilla.org/api/v5/addons/addon/{}/"


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "xbps-src"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return resp.read()


def fetch(destdir, guid):
    info = json.loads(get(API.format(urllib.parse.quote(guid, safe=""))))
    file = info["current_version"]["file"]
    algo, _, expected = file["hash"].partition(":")
    if algo != "sha256":
        raise RuntimeError(f"unexpected hash type {algo!r}")
    data = get(file["url"])
    actual = hashlib.sha256(data).hexdigest()
    if actual != expected:
        raise RuntimeError(f"checksum mismatch: {actual} != {expected}")
    with open(f"{destdir}/{guid}.xpi", "wb") as f:
        f.write(data)
    print(f"{guid}: {info['current_version']['version']} ({actual})")


def main():
    destdir, guids = sys.argv[1], sys.argv[2:]
    status = 0
    for guid in guids:
        optional = guid.endswith("?")
        guid = guid.rstrip("?")
        try:
            fetch(destdir, guid)
        except Exception as e:  # noqa: BLE001
            print(f"{'WARNING' if optional else 'ERROR'}: {guid}: {e}", file=sys.stderr)
            if not optional:
                status = 1
    return status


if __name__ == "__main__":
    sys.exit(main())
