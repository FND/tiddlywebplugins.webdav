from __future__ import absolute_import

from lxml import etree
from email.utils import formatdate


def dict2xml(dic, text_node="_text", attrib_prefix="@"):
    """
    generates an XML string from a dictionary

    if a value is a string, it will be used as
    * a text node on the current node if the key is `text_node`
    * an attribute on the current node if the key starts with `attrib_prefix`
    * a text node on a new sub-node otherwise

    >>> data = {
        "date": "2012-03-25",
        "source": {
            "@uri": "example.org",
            "_text": "Example"
        },
        "article": [{
            "title": "lipsum"
        }, {
            "title": "hello world",
            "author": {
                "name": "John Doe",
                "e-mail": "jdoe@example.org"
            }
        }]
    }
    >>> dict2xml(data)
    <date>2012-03-25</date>
    <source uri="example.org">Example</source>
    <article>
        <title>lipsum</title>
    </article>
    <article>
        <author>
          <e-mail>jdoe@example.org</e-mail>
          <name>John Doe</name>
        </author>
        <title>hello world</title>
    </article>
    """
    def process_node(dic, parent):
        for tag, value in dic.items():
            if value is None:
                etree.SubElement(parent, tag)
            elif isinstance(value, basestring):
                if tag == text_node:
                    parent.text = value
                elif tag.startswith(attrib_prefix):
                    parent.set(tag[1:], value)
                else:
                    node = etree.SubElement(parent, tag)
                    node.text = value
            elif hasattr(value, "items"): # dictionary
                node = etree.SubElement(parent, tag)
                process_node(value, node)
            else: # list
                for item in value:
                    node = etree.SubElement(parent, tag)
                    process_node(item, node)

    root = etree.Element("root")
    process_node(dic, root)

    return "\n".join(etree.tostring(node) for node in root.getchildren())


def prettify(data, content_type):
    """
    pretty-print data based on content type
    """
    content_type = content_type.split(";")[0] # ignore charset

    if content_type == "application/xml":
        from lxml import etree
        from StringIO import StringIO
        xml = etree.parse(StringIO(data))
        return etree.tostring(xml, pretty_print=True)
        # alternative prettification
        #from xml.dom import minidom
        #from xml.parsers.expat import ExpatError
        #xml = minidom.parseString(body).toprettyxml()
    else:
        return data # XXX: silent failure?


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


def _super(self):
    """
    convenience method for common `super` calls

    this essentially emulates Python 3 behavior
    """
    return super(self.__class__, self)
