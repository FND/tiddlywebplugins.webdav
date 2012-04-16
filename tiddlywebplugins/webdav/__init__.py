"""
WebDAV extension for TiddlyWeb
"""

from __future__ import absolute_import

from itertools import chain
from collections import OrderedDict

from tiddlyweb.web.http import HTTP403
from tiddlywebplugins.utils import replace_handler

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
        handlers = { "OPTIONS": handshake, "PROPFIND": list_collection }
        for uri in ("/", "/bags", "/recipes"):
            replace_handler(config["selector"], uri, handlers) # XXX: we want to extend, not replace


def handshake(environ, start_response): # TODO: rename
    """
    WSGI application handling OPTIONS requests
    """
    headers = merge({}, DEFAULT_HEADERS, {
        "Allow": ", ".join(environ["selector.methods"]), # TODO: they say OS X Finder requires LOCK, even if faked
        "Content-Length": "0",
        "Date": rfc1123Time()
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
            "response": (_multistatus_response(uri, True) for uri in determine_entries(environ))
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


def determine_entries(environ):
    """
    returns descendant resources based on the WSGI environment
    """
    current_uri = environ["SCRIPT_NAME"] # XXX: don't we want PATH_INFO?
    current_route = environ["selector.matches"][0]

    descendant_candidates = { # XXX: hard-coded; ideally descendants should be determined via HATEOAS-y clues
        "/": ["/bags", "/recipes"],
        "/bags": ("/bags/%s" % entity for entity in ["default", "alpha"]), # hard-coded samples
        "/recipes": ("/recipes/%s" % entity for entity in ["default", "omega"]) # hard-coded samples
    }
    # TODO: prepend server_prefix

    descendants = descendant_candidates[current_route]
    return chain([current_uri], descendants)


def _multistatus_response(uri, collection=True):
    """
    generate XML for a single multistatus response
    """
    supported_methods = ["OPTIONS", "HEAD", "GET", "PUT", "DELETE", "PROPFIND"] # XXX: lies; use `selector.methods`
    return OrderedDict([ # apparently order matters, at least to some clients
        ("href", uri),
        ("propstat", {
            "status": "HTTP/1.1 200 OK", # XXX: if order matters, this should go below `prop`
            "prop": {
                "resourcetype": "collection" if collection else None, # TODO: only add this element if non-empty?
                "supported-live-property-set": {
                    "supported-live-property": {
                        "prop": { # TODO: support for other properties?
                            "ordering-type": None # XXX: is this actually desirable?
                        }
                    }
                },
                "supported-method-set": { # TODO: inefficient; use reference to avoid duplication
                    "supported-method": ({ "@name": meth } for meth in supported_methods)
                }
            }
        })
    ])
