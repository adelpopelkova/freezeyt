import xml.dom.minidom
from urllib.parse import urljoin

import html5lib
from werkzeug.datastructures import Headers
from werkzeug.http import parse_options_header

from freezeyt.encoding import decode_input_path


def get_all_links(
    page_content: bytes, base_url, headers: Headers = None
) -> list:
    """Get all links from "page_content".

    Return an iterable of strings.

    base_url is the URL of the page.
    """
    if headers == None:
        cont_charset = None
    else:
        content_type_header = headers.get('Content-Type')
        cont_type, cont_options = parse_options_header(content_type_header)
        cont_charset = cont_options.get('charset')
    document = html5lib.parse(page_content, transport_encoding=cont_charset)
    return get_links_from_node(document, base_url)


def get_links_from_node(node: xml.dom.minidom.Node, base_url) -> list:
    """Get all links from xml.dom.minidom Node."""
    result = []
    if 'href' in node.attrib:
        href = decode_input_path(node.attrib['href'])
        full_url = urljoin(base_url, href)
        result.append(full_url)
    if 'src' in node.attrib:
        href = decode_input_path(node.attrib['src'])
        full_url = urljoin(base_url, href)
        result.append(full_url)
    for child in node:
        result.extend(get_links_from_node(child, base_url))
    return result
