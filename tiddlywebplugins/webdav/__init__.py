"""
WebDAV extension for TiddlyWeb
"""

from __future__ import absolute_import

from tiddlywebplugins.utils import replace_handler

from .util import rfc1123Time, merge


DEFAULT_HEADERS = {
    "DAV": "1",
    "MS-Author-Via": "DAV" # this seems necessary for Windows
}


def init(config):
    if "selector" in config: # system plugin
        replace_handler(config["selector"], "/", dict(OPTIONS=root)) # XXX: we want to extend, not replace


def root(environ, start_response):
    headers = merge({}, DEFAULT_HEADERS, {
        "Allow": "OPTIONS, HEAD, GET, PROPFIND", # XXX: lies? -- TODO: they say OS X Finder requires LOCK, even if faked
        "Content-Length": "0",
        "Date": rfc1123Time()
    })
    start_response("200 OK", headers.items())
    return ""
