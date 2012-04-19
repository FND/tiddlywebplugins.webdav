"""
WebDAV extension for TiddlyWeb
"""

from __future__ import absolute_import

import re

from itertools import chain
from collections import OrderedDict

from tiddlyweb.model.bag import Bag
from tiddlyweb.web.http import HTTP403
from tiddlyweb.web.query import Query
from tiddlywebplugins.utils import replace_handler, get_store

from .router import Router
from .middleware import Slasher
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
    current_uri = environ["SCRIPT_NAME"]
    config = environ["tiddlyweb.config"]
    store = get_store(config)

    candidates = { # XXX: hard-coded; ideally descendants should be determined via HATEOAS-y clues
        "[/]": ["/bags", "/recipes"],
        "/bags[.{format}]": ("/bags/%s" % bag.name for bag in store.list_bags()),
        "/recipes[.{format}]": ("/recipes/%s" % recipe.name for recipe in store.list_recipes()),
        "/bags/{bag_name:segment}/tiddlers[.{format}]": lambda *args, **kwargs: ("/bags/%s/tiddlers/%s" %
                (kwargs["bag_name"], tiddler.title) for tiddler in
                store.list_bag_tiddlers(Bag(kwargs["bag_name"])))
    }

    for regex, supported_methods in config["selector"].mappings:
        if regex.search(current_uri): # matching route
            routes = Router(mapfile=config["urls_map"], prefix=config["server_prefix"]).routes # XXX: does not support extensions
            pattern = routes[regex]
            descendants = candidates[pattern]
            try: # deferred evaluation
                descendants = descendants(*environ["wsgiorg.routing_args"][0], **environ["wsgiorg.routing_args"][1])
            except TypeError:
                pass
            break

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
