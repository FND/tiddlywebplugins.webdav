from __future__ import absolute_import

from itertools import chain
from collections import OrderedDict

from tiddlyweb.model.bag import Bag
from tiddlywebplugins.utils import replace_handler, get_store

from .router import Router


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


def multistatus_response(uri, collection=True):
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
