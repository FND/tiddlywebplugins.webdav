from __future__ import absolute_import

from itertools import chain
from collections import OrderedDict

from tiddlyweb.model.bag import Bag
from tiddlywebplugins.utils import get_store

from .router import Router
from .util import _super


def determine_entries(environ):
    """
    returns descendant resources based on the WSGI environment
    """
    candidates = { # XXX: hard-coded; ideally descendants should be determined via HATEOAS-y clues
        "[/]": lambda *args: [Collection("/bags"), Collection("/recipes")],
        "/bags[.{format}]": _bags,
        "/recipes[.{format}]": _recipes,
        "/bags/{bag_name:segment}/tiddlers[.{format}]": _tiddlers
    }

    current_uri = environ["SCRIPT_NAME"]
    config = environ["tiddlyweb.config"]
    store = get_store(config)
    router = Router(mapfile=config["urls_map"], prefix=config["server_prefix"]) # XXX: does not support extensions

    for regex, supported_methods in router.mappings:
        if regex.search(current_uri): # matching route
            pattern = router.routes[regex]
            descendants = candidates[pattern]
            routing_args = environ["wsgiorg.routing_args"]
            descendants = descendants(store, *routing_args[0], **routing_args[1])
            break

    return chain([Collection(current_uri)], descendants)


def multistatus_response(entry):
    """
    generate XML for a single multistatus response
    """
    return OrderedDict([ # apparently order matters, at least to some clients
        ("href", entry.uri),
        ("propstat", {
            "status": "HTTP/1.1 200 OK", # XXX: if order matters, this should go below `prop`
            "prop": {
                "resourcetype": "collection" if entry.collection else None, # TODO: only add this element if non-empty?
                "supported-live-property-set": {
                    "supported-live-property": {
                        "prop": { # TODO: support for other properties?
                            "ordering-type": None # XXX: is this actually desirable?
                        }
                    }
                },
                "supported-method-set": { # TODO: inefficient; use reference to avoid duplication
                    "supported-method": ({ "@name": meth } for meth in entry.supported_methods)
                }
            }
        })
    ])


def _bags(store, *routing_args, **routing_kwargs):
    return (Collection("/bags/%s/tiddlers" % bag.name)
            for bag in store.list_bags())


def _recipes(store, *routing_args, **routing_kwargs):
    return (Collection("/recipes/%s/tiddlers" % recipe.name)
            for recipe in store.list_recipes())


def _tiddlers(store, *routing_args, **routing_kwargs):
    bag_name = routing_kwargs["bag_name"]
    bag = Bag(bag_name)
    return (Entry("/bags/%s/tiddlers/%s" % (bag_name, tiddler.title))
            for tiddler in store.list_bag_tiddlers(bag))


class Entry(object):

    def __init__(self, uri, collection=False):
        self.uri = uri
        self.collection = collection
        self.supported_methods = ["OPTIONS", "HEAD", "GET", "PUT", "DELETE", "PROPFIND"] # XXX: lies; use `selector.methods`


class Collection(Entry):
    """
    convenience wrapper for readability
    """

    def __init__(self, uri):
        _super(self).__init__(uri, collection=True)
