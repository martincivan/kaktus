import uasyncio as asyncio


class ClientResponse:

    def __init__(self, reader):
        self.content = reader

    def read(self, sz=-1):
        return (yield from self.content.read(sz))

    def __repr__(self):
        # return "<ClientResponse %d %s>" % (self.status, self.headers)
        return "<ClientResponse %s %s>" % (self.status, self.headers)


class ChunkedClientResponse(ClientResponse):

    def __init__(self, reader):
        self.content = reader
        self.chunk_size = 0

    def read(self, sz=4*1024*1024):
        if self.chunk_size == 0:
            l = yield from self.content.readline()
            l = l.split(b";", 1)[0]
            self.chunk_size = int(l, 16)
            if self.chunk_size == 0:
                # End of message
                sep = yield from self.content.read(2)
                assert sep == b"\r\n"
                return b''
        data = yield from self.content.read(min(sz, self.chunk_size))
        self.chunk_size -= len(data)
        if self.chunk_size == 0:
            sep = yield from self.content.read(2)
            assert sep == b"\r\n"
        return data

    def __repr__(self):
        return "<ChunkedClientResponse %d %s>" % (self.status, self.headers)


def request_raw(method, url, data=None, timeout=None):
    try:
        proto, dummy, host, path = url.split("/", 3)
    except ValueError:
        proto, dummy, host = url.split("/", 2)
        path = ""
    if proto != "http:":
        raise ValueError("Unsupported protocol: " + proto)
    try:
        host, port = host.split(":", 2)
        port = int(port)
    except ValueError:
        port = 80
    if timeout:
        reader, writer = yield from asyncio.wait_for(asyncio.open_connection(host, port), timeout)
    else:
        reader, writer = yield from asyncio.run(asyncio.open_connection(host, port))
    # Use protocol 1.0, because 1.1 always allows to use chunked transfer-encoding
    # But explicitly set Connection: close, even though this should be default for 1.0,
    # because some servers misbehave w/o it.
    content_length = ''
    if data is not None:
        content_length = "content-length: %i\r\n" % (len(data))
    query = "%s /%s HTTP/1.0\r\nHost: %s:%i\r\n%sConnection: close\r\nUser-Agent: compat\r\n\r\n" % (method, path, host, port, content_length)
    yield from writer.awrite(query.encode('latin-1'))
    if data:
        yield from writer.awrite(data)

    return reader


def request(method, url, data=None, timeout=0):
    redir_cnt = 0
    redir_url = None
    while redir_cnt < 2:
        reader = yield from request_raw(method, url, data, timeout)
        headers = []
        status = yield from reader.readline()
        # sline = yield from reader.readline()
        # protover, status, msg = sline.split(None, 2)
        # status = int(status)
        chunked = False
        while True:
            line = yield from reader.readline()
            if not line or line == b"\r\n":
                break
            headers.append(line)
            if line.startswith(b"Transfer-Encoding:"):
                if b"chunked" in line:
                    chunked = True
            elif line.startswith(b"Location:"):
                url = line.rstrip().split(None, 1)[1].decode("latin-1")

        # if 301 <= status <= 303:
        #     redir_cnt += 1
        #     yield from reader.aclose()
        #     continue
        break

    if chunked:
        resp = ChunkedClientResponse(reader)
    else:
        resp = ClientResponse(reader)
    resp.status = status
    resp.headers = headers
    return resp
