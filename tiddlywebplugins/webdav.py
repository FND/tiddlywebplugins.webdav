"""
WebDAV extension for TiddlyWeb
"""

from email.utils import formatdate

from tiddlywebplugins.utils import replace_handler


DEFAULT_HEADERS = {
    "DAV": "1",
    "MS-Author-Via": "DAV" # this seems necessary for Windows
}


def init(config):
    if "selector" in config: # system plugin
        replace_handler(config["selector"], "/", dict(OPTIONS=root)) # XXX: we want to extend, not replace


def root(environ, start_response):
    headers = _merge({}, DEFAULT_HEADERS, {
        "Allow": "OPTIONS, HEAD, GET, PROPFIND", # XXX: lies? -- TODO: they say OS X Finder requires LOCK, even if faked
        "Content-Length": "0",
        "Date": rfc1123Time()
    })
    start_response("200 OK", headers.items())
    return ""


def rfc1123Time(secs=None):
    """
    returns seconds in RFC 1123 date/time format

    if `secs` is None, the current date is used

    (adapted from WsgiDAV; http://code.google.com/p/wsgidav/)
    """
    return formatdate(timeval=secs, localtime=False, usegmt=True)


def _merge(target, *args):
    """
    shallowly merges dictionaries into `target`

    NB: this goes somewhat against Python conventions by modifying and also
    returning `target` (rather than `None`; cf. `sort`)
    """
    for dic in args:
        target.update(dic)
    return target
