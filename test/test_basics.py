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

    module.client = httplib2.Http()


@mark.xfail
def test_nondestructive():
    # ensure original root is not overridden
    response, content = client.request("%s/" % HOST, "GET")
    assert response["status"] == "200", content


def test_handshake():
    response, content = client.request("%s/" % HOST, "OPTIONS")
    assert response["status"] == "200", content
    assert response["dav"] == "1", content
    assert response["ms-author-via"] == "DAV", content


def test_directory_listing():
    response, content = client.request("%s/" % HOST, "PROPFIND")
    assert response["status"] == "207", content
    assert response["content-type"] == "application/xml", content
    assert "<?xml " in content
    assert "<href>/bags</href>" in content
    assert "<href>/recipes</href>" in content


def _app():
    return serve.load_app()
