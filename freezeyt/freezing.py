from urllib.parse import urlparse, urljoin
from pathlib import Path
import xml.dom.minidom
import html5lib


def url_to_filename(base, url):
    """Return the filename to which the page is frozen.

    Parameters:
    base - Filesystem base path (eg. /tmp/)
    url - Absolute or relative URL (eg. http://localhost:8000/ or /second/second.html)
    """
    url_parse = urlparse(url)

    if url_parse.scheme:
        if url_parse.scheme not in ('http', 'https'):
            raise ValueError("got URL that is not http")

    if url_parse.netloc == '' or url_parse.netloc == 'localhost:8000':
        url_path = url_parse.path
    else:
        raise ValueError("got external URL instead of localhost")

    if url_path.endswith('/'):
        url_path = url_path + 'index.html'

    return base / url_path.lstrip('/')


def freeze(app, path):
    """Freeze (create files of) all pages from a WSGI server.

    Parameters:
    app -- web app you want to freeze
    path -- path to the file
    """
    path = Path(path)

    def start_response(status, headers):
        print('status', status)
        print('headers', headers)

    links = ['http://localhost:8000/']

    visited_links = set()

    while links:
        link = links.pop()

        if link in visited_links:
            continue

        visited_links.add(link)

        try:
            filename = url_to_filename(path, link)
        except ValueError:
            print('skipping', link)
            continue

        print('link:', link)

        path_info = urlparse(link).path

        print('path_info:', path_info)

        environ = {
            'SERVER_NAME': 'localhost',
            'wsgi.url_scheme': 'http',
            'SERVER_PORT': '8000',
            'REQUEST_METHOD': 'GET',
            'PATH_INFO': path_info,
            # ...
        }

        result = app(environ, start_response)

        print(f'Saving to {filename}')

        filename.parent.mkdir(parents=True, exist_ok=True)

        with open(filename, "wb") as f:
            for item in result:
                f.write(item)

        with open(filename, "rb") as f:
            links.extend(get_all_links(f, link))


def get_all_links(page_content: bytes, base_url) -> list:
    """Get all links from "page_content".

    Return an iterable of strings.

    base_url is the URL of the page.
    """
    document = html5lib.parse(page_content)
    return get_links_from_node(document, base_url)


def get_links_from_node(node: xml.dom.minidom.Node, base_url) -> list:
    """Get all links from xml.dom.minidom Node."""
    result = []
    if 'href' in node.attrib:
        href = node.attrib['href']
        full_url = urljoin(base_url, href)
        result.append(full_url)
    for child in node:
        result.extend(get_links_from_node(child, base_url))
    return result