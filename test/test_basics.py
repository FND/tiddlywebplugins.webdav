import httplib2

from wsgi_intercept import httplib2_intercept, add_wsgi_intercept
from pytest import mark

from tiddlyweb.config import config
from tiddlyweb.web import serve


HOSTNAME = "0.0.0.0"
PORT = 8080
HOST = "http://%s:%s" % (HOSTNAME, PORT)


def setup_module(module):
    from .fixtures import populate_store

    module.environ = { "tiddlyweb.config": config }
    config["system_plugins"].append("tiddlywebplugins.webdav")
    populate_store()

    httplib2_intercept.install()
    add_wsgi_intercept(HOSTNAME, PORT, _app)

    module.client = httplib2.Http()


@mark.xfail
def test_nondestructive():
    # ensure original URI handlers are not overridden
    for uri in ("/", "/bags", "/recipes"):
        response, content = client.request(HOST + uri, "GET")
        assert response["status"] == "200", content


def test_handshake():
    for uri in ("/", "/bags", "/recipes"):
        response, content = client.request("%s/" % HOST, "OPTIONS")
        supported_methods = response["allow"].split(", ")
        assert response["status"] == "200", content
        assert response["dav"] == "1", content
        assert response["ms-author-via"] == "DAV", content
        assert len(supported_methods) > 1
        assert "OPTIONS" in supported_methods


def test_directory_listing():
    response, content = client.request("%s/" % HOST, "PROPFIND")
    assert response["status"] == "207", content
    assert response["content-type"] == "application/xml", content
    assert "<?xml " in content
    assert "<href>/</href>" in content # XXX: is this necessary/desirable?
    assert "<href>/bags</href>" in content
    assert "<href>/recipes</href>" in content

    response, content = client.request("%s/bags" % HOST, "PROPFIND")
    assert response["status"] == "207", content
    assert response["content-type"] == "application/xml", content
    assert "<?xml " in content
    assert "<href>/bags</href>" in content # XXX: is this necessary/desirable?
    assert "<href>/bags/alpha</href>" in content
    assert "<href>/bags/bravo</href>" in content

    response, content = client.request("%s/recipes" % HOST, "PROPFIND")
    assert response["status"] == "207", content
    assert response["content-type"] == "application/xml", content
    assert "<?xml " in content
    assert "<href>/recipes</href>" in content # XXX: is this necessary/desirable?
    assert "<href>/recipes/omega</href>" in content


def _app():
    return serve.load_app()
