

class ClientResponse:

    def __init__(self, reader):
        self.content = reader

    async def read(self, sz=-1):
        result = await self.content.read(sz)
        self.content.aclose()
        return result

    def __repr__(self):
        # return "<ClientResponse %d %s>" % (self.status, self.headers)
        return "<ClientResponse %s %s>" % (self.status, self.headers)


class ChunkedClientResponse(ClientResponse):

    def __init__(self, reader):
        self.content = reader
        self.chunk_size = 0

    async def read(self, sz=4*1024*1024):
        if self.chunk_size == 0:
            l = await self.content.readline()
            l = l.split(b";", 1)[0]
            self.chunk_size = int(l, 16)
            if self.chunk_size == 0:
                # End of message
                sep = await self.content.read(2)
                assert sep == b"\r\n"
                self.content.aclose()
                return b''
        data = await self.content.read(min(sz, self.chunk_size))
        self.chunk_size -= len(data)
        if self.chunk_size == 0:
            sep = await self.content.read(2)
            assert sep == b"\r\n"
        return data

    def __repr__(self):
        return "<ChunkedClientResponse %d %s>" % (self.status, self.headers)


async def request_raw(method, url, data=None, timeout=None):
    import uasyncio as asyncio
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
    # reader, writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout)
    reader, writer = await asyncio.open_connection(host, port)
    # reader, writer = await asyncio.run(asyncio.open_connection(host, port))
    # Use protocol 1.0, because 1.1 always allows to use chunked transfer-encoding
    # But explicitly set Connection: close, even though this should be default for 1.0,
    # because some servers misbehave w/o it.
    content_length = ''
    if data is not None:
        content_length = "content-length: %i\r\n" % (len(data))
    query = "%s /%s HTTP/1.0\r\nHost: %s:%i\r\n%sConnection: close\r\nUser-Agent: compat\r\n\r\n%s" % (method, path, host, port, content_length, data)
    await writer.awrite(query.encode('latin-1'))
    return reader, writer


async def request(method, url, data=None, timeout=0):
    redir_cnt = 0
    redir_url = None
    chunked = False
    while redir_cnt < 2:
        (reader, writer) = await request_raw(method, url, data, timeout)
        headers = []
        sline = await reader.readline()
        data = sline.split(None, 2)
        protocol = data[0]
        try:
            status = int(data[1])
        except ValueError:
            status = 0
        try:
            message = data[2]
        except IndexError:
            message = ""
        while True:
            line = await reader.readline()
            if not line or line == b"\r\n":
                break
            headers.append(line)
            if line.startswith(b"Transfer-Encoding:"):
                if b"chunked" in line:
                    chunked = True
            elif line.startswith(b"Location:"):
                url = line.rstrip().split(None, 1)[1].decode("latin-1")

        if 301 <= status <= 303:
            redir_cnt += 1
            await reader.aclose()
            continue
        break

    if chunked:
        resp = ChunkedClientResponse(reader)
    else:
        resp = ClientResponse(reader)
    resp.status = status
    resp.headers = {}
    for i in map(lambda x: x.decode("ascii").rstrip(), headers):
        split = i.split(":", 1)
        resp.headers[split[0]] = split[1]
    resp.message = message
    resp.protocol = protocol
    return resp, writer


async def run(method, url, data=None):
    resp, writer = await request(method=method, url=url, data=data, timeout=30)
    text = await resp.read()
    writer.aclose()
    text = text.decode("ascii")
    resp.text = text
    return resp