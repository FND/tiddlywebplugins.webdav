"""
WebDAV extension for TiddlyWeb
"""

from tiddlywebplugins.utils import replace_handler


def root(environ, start_response):
    start_response("200 OK", [])
    return ""


def init(config):
    if "selector" in config: # system plugin
        replace_handler(config["selector"], "/", dict(OPTIONS=root)) # XXX: we want to extend, not replace
