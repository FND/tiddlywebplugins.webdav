"""
WebDAV extension for TiddlyWeb
"""

from __future__ import absolute_import

from collections import OrderedDict

from tiddlyweb.web.http import HTTP403
from tiddlywebplugins.utils import replace_handler

from .util import dict2xml, rfc1123Time, merge


DEFAULT_HEADERS = {
    "DAV": "1",
    "MS-Author-Via": "DAV" # this seems necessary for Windows
}


def init(config):
    if "selector" in config: # system plugin
        replace_handler(config["selector"], "/", # XXX: we want to extend, not replace
                { "OPTIONS": handshake, "PROPFIND": index })


def handshake(environ, start_response):
    headers = merge({}, DEFAULT_HEADERS, {
        "Allow": "OPTIONS, HEAD, GET, PROPFIND", # XXX: lies? -- TODO: they say OS X Finder requires LOCK, even if faked
        "Content-Length": "0",
        "Date": rfc1123Time()
    })
    start_response("200 OK", headers.items())
    return ""


def index(environ, start_response):
    if environ.get("HTTP_DEPTH", "0") not in ("0", "1"):
        raise HTTP403("excessive depth requested")

    uri = environ["selector.matches"][0] # XXX: srsly?
    if uri == "/":
        uris = ["/bags", "/recipes"] # TODO: generate automatically (e.g. to include extensions)
    elif uri in ("/bags", "/recipes"):
        uris = ["%s/%s" % (uri, entity) for entity in ["default", "foo"]] # TODO: generate automatically
    uris.insert(0, uri)

    properties = {
        "resourcetype": None,
        "creationdate": "2012-03-25T07:25:06Z", # TODO: use created
        "getlastmodified": "Sun, 25 Mar 2012 07:25:06 GMT", # TODO: use modified
        "getetag": None, # TODO
        "getcontentlength": None, # TODO?
        "{http://apache.org/dav/props/}executable": None # TODO: declare namespace at root level
    }

    doc = {
        "multistatus": {
            "@xmlns": "DAV:",
            "response": (_prop_response(uri, properties, True)
                    for uri in uris)
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


def _prop_response(uri, properties, collection=False):
    collection = True # XXX: DEBUG
    if collection:
        properties["resourcetype"] = "collection" # XXX: modifying mutable argument

    return OrderedDict([ # apparently order matters, at least to some clients
        ("href", uri),
        ("propstat", [{
            "status": "HTTP/1.1 200 OK",
            "prop": properties
        }])
    ])
