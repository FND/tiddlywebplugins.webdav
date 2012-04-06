from email.utils import formatdate


def rfc1123Time(secs=None):
    """
    returns seconds in RFC 1123 date/time format

    if `secs` is None, the current date is used

    (adapted from WsgiDAV; http://code.google.com/p/wsgidav/)
    """
    return formatdate(timeval=secs, localtime=False, usegmt=True)


def merge(target, *args):
    """
    shallowly merges dictionaries into `target`

    NB: this goes somewhat against Python conventions by modifying and also
    returning `target` (rather than `None`; cf. `sort`)
    """
    for dic in args:
        target.update(dic)
    return target
