def test_compile():
    try:
        import tiddlywebplugins.webdav
        assert True
    except ImportError, exc:
        assert False, exc
