"""
WebDAV extension for TiddlyWeb
"""

from __future__ import absolute_import

import re

from tiddlyweb.web.http import HTTP403
from tiddlyweb.web.query import Query
from tiddlywebplugins.utils import replace_handler

from .middleware import Slasher
from .collections import determine_entries, multistatus_response
from .util import dict2xml, rfc1123Time, merge


DEFAULT_HEADERS = {
    "DAV": "1",
    "MS-Author-Via": "DAV" # this seems necessary for Windows
}


def init(config):
    """
    TiddlyWeb plugin initialization
    """
    if "selector" in config: # system plugin
        # inject middleware
        if Slasher not in config["server_request_filters"]: # XXX: unnecessary?
            index = config["server_request_filters"].index(Query) + 1
            config["server_request_filters"].insert(index, Slasher)
        # add/augment URI handlers
        handlers = { "OPTIONS": handshake, "PROPFIND": list_collection }
        for uri in ("/", "/bags", "/recipes", "/bags/.../tiddlers"): # TODO: reuse determine_entries:candidates
            replace_handler(config["selector"], uri, handlers) # XXX: we want to extend, not replace


def handshake(environ, start_response): # TODO: rename
    """
    WSGI application handling OPTIONS requests
    """
    headers = merge({}, DEFAULT_HEADERS, {
        "Allow": ", ".join(environ["selector.methods"]), # TODO: they say OS X Finder requires LOCK, even if faked
        "Content-Length": "0",
        "Date": rfc1123Time() # XXX: unnecessary
    })
    start_response("200 OK", headers.items())
    return ""


def list_collection(environ, start_response):
    """
    WSGI application handling PROPFIND requests
    """
    if environ.get("HTTP_DEPTH", "0") not in ("0", "1"):
        raise HTTP403("excessive depth requested")

    doc = {
        "multistatus": {
            "@xmlns": "DAV:",
            "response": (multistatus_response(uri, True) for uri in determine_entries(environ))
        }
    }
    doc = """<?xml version="1.0" encoding="utf-8" ?>\n%s""" % dict2xml(doc)

    # XXX: DEBUG
    from .util import prettify
    print "%s\n%s\n%s" % ("=" * 80, prettify(doc, "application/xml"), "-" * 80)

    headers = merge({}, DEFAULT_HEADERS, {
        "Content-Type": "application/xml", # XXX: charset?
        "Content-Length": "%s" % len(doc)
    })
    start_response("207 Multi-Status", headers.items())
    return doc
