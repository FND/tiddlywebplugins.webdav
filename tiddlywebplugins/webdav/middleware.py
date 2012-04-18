import logging


class Slasher(object): # TODO: move elsewhere
    """
    WSGI middleware that doctors the environment to ignore trailing slashes in
    request URIs
    """

    def __init__(self, application):
        self.application = application

    def __call__(self, environ, start_response):
        for key in ("REQUEST_URI", "SCRIPT_NAME", "PATH_INFO"):
            uri = environ.get(key, None)
            # strip trailing slash if present
            if uri and uri[-1] == "/":
                environ[key] = uri[:-1]
                logging.debug("removed trailing slash from %s: %s", key, uri)

        return self.application(environ, start_response)

