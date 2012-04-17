from selector import Selector


class Router(Selector):
    """
    Selector variant which retains a mapping of original URI templates to the
    corresponding regular expressions and vice versa
    """

    def __init__(self, *args, **kwargs):
        self.routes = {}
        _super(self).__init__(*args, **kwargs)

    def add(self, path, *args, **kwargs):
        mapping = _super(self).add(path, *args, **kwargs)

        regex = mapping[0]
        self.routes[path] = regex
        self.routes[regex] = path

        return mapping


def _super(self):
    """
    convenience method for common `super` calls

    this essentially emulates Python 3 behavior
    """
    return super(self.__class__, self)
