import httplib2

from wsgi_intercept import httplib2_intercept, add_wsgi_intercept
from pytest import mark

from tiddlyweb.config import config
from tiddlyweb.web import serve


HOSTNAME = "0.0.0.0"
PORT = 8080
HOST = "http://%s:%s" % (HOSTNAME, PORT)


def setup_module(module):
    module.environ = { "tiddlyweb.config": config }
    config["system_plugins"].append("tiddlywebplugins.webdav")

    httplib2_intercept.install()
    add_wsgi_intercept(HOSTNAME, PORT, _app)


@mark.xfail
def test_nondestructive():
    http = httplib2.Http()

    # ensure original root is not overridden
    response, content = http.request("%s/" % HOST, "GET")
    assert response["status"] == "200"


def test_handshake():
    http = httplib2.Http()

    response, content = http.request("%s/" % HOST, "OPTIONS")
    assert response["status"] == "200"
    assert response["dav"] == "1"
    assert response["ms-author-via"] == "DAV"


def _app():
    return serve.load_app()
