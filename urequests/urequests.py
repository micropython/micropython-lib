import usocket
import ure
from parse import urlencode

class Response:

    def __init__(self, f):
        self.raw = f
        self.encoding = "utf-8"
        self._cached = None
        self.status_code = None
        self.reason = None
        self.headers = None
        # cookie support as dict
        self.cookies = None
        # url to see redirect targets
        self.url = None

    def close(self):
        if self.raw:
            self.raw.close()
            self.raw = None
        self._cached = None

    # extracts data from a stream, if the direct conversion of the result to a string consumes too much memory
    # result is an array with the results startStr+found between+endstring
    def extract(self, _startStr, _endStr):
        # we prepare an array to store
        results = []
        # prepare regex to reduces spaces to on space
        # and remove cr/linefeeds
        removeWhiteSpaces = ure.compile("(  )+")
        removeCR = ure.compile("[\r\n]")
        endOfStream = False
        _startStrBytes = bytes(_startStr, 'utf-8')
        _endStrBytes = bytes(_endStr, 'utf-8')
        # start with mininum length of the search String
        # if it is smaller than the start - end
        pageStreamBytes = self.raw.read(len(_startStr))
        if len(pageStreamBytes) < len(_startStr):
            endOfStream = True
        # we must convert the searchstring to bytes als not for all charcters uft-8 encoding is working
        # like in Curacao (special c)
        while not endOfStream:
            if pageStreamBytes == _startStrBytes:
                # we found a matching string
                # print('Start found %s ' % pageStreamBytes.decode('utf-8'))
                # we need to find the end
                endOfTag = False
                read = self.raw.read(len(_endStr))
                if len(read) == 0:
                    endOfStream = True
                pageStreamBytes += read
                while ((not endOfStream) and (not endOfTag)):
                    # comparing the string with the find method is easier
                    # than comparing the bytes
                    if (pageStreamBytes.decode('utf-8')).find(_endStr) > 0:
                        endOfTag = True
                        result = removeWhiteSpaces.sub('', pageStreamBytes.decode('utf-8'))
                        result = removeCR.sub('', result)
                        results.append(result)
                        # print('Result: %s' % result)
                    else:
                        # read and Append
                        read = self.raw.read(1)
                        if len(read) == 0:
                            endOfStream = True
                        else:
                            pageStreamBytes += read
                            # print('End not Found %s' % pageStreamBytes.decode('utf-8'))
            else:
                # we did not find a matching string
                # and reduce by one character before we add the next
                # print('not found %s' % pageStream)
                pageStreamBytes = pageStreamBytes[1:len(_startStrBytes)]
            read = self.raw.read(1)
            if len(read) == 0:
                endOfStream = True
            pageStreamBytes = pageStreamBytes + read
        self.close()
        return results
        
    @property
    def content(self):
        if self._cached is None:
            try:
                self._cached = self.raw.read()
            finally:
                self.raw.close()
                self.raw = None
        return self._cached

    @property
    def text(self):
        return str(self.content, self.encoding)

    def json(self):
        import ujson
        return ujson.loads(self.content)

""" method = head, get, put, patch, post, delete
url (with our without parameters)
params, cookies, headers - each as dict
if cookies are supplied, new cookies will be added to the supplied ones. domain attribute is not stored (yet)
if parse_headers is false -> no cookies are returned as they are part of the header
if followRedirect = false -> the redirect URL is stored in URL
"""
def request(method, url, params=None, cookies=None, data=None, json=None, headers={}, parse_headers=True, followRedirect=True):
    if params is not None:
        if params != {}:
            url = url.rstrip('?') + '?' + urlencode(params, doseq=True)
    redir_cnt = 1
    while True:
        try:
            proto, dummy, host, path = url.split("/", 3)
        except ValueError:
            proto, dummy, host = url.split("/", 2)
            path = ""
        if proto == "http:":
            port = 80
        elif proto == "https:":
            import ussl
            port = 443
        else:
            raise ValueError("Unsupported protocol: " + proto)

        if ":" in host:
            host, port = host.split(":", 1)
            port = int(port)

        ai = usocket.getaddrinfo(host, port, 0, usocket.SOCK_STREAM)
        ai = ai[0]

        resp_d = None
        if parse_headers is not False:
            resp_d = {}

        # print('Socket create')
        s = usocket.socket(ai[0], ai[1], ai[2])
        # 60sec timeout on blocking operations
        s.settimeout(60.0)
        try:
            # print('Socket connect')
            s.connect(ai[-1])
            if proto == "https:":
                s = ussl.wrap_socket(s, server_hostname=host)
            # print('Socket wrapped')
            s.write(b"%s /%s HTTP/1.0\r\n" % (method, path))
            # print('Socket write: ')
            # print(b"%s /%s HTTP/1.0\r\n" % (method, path))
            if "Host" not in headers:
                s.write(b"Host: %s\r\n" % host)
            # Iterate over keys to avoid tuple alloc
            for k in headers:
                s.write(k)
                s.write(b": ")
                s.write(headers[k])
                s.write(b"\r\n")
                # print(k, b": ".decode('utf-8'), headers[k], b"\r\n".decode('utf-8'))
            if cookies is not None:
                for cookie in cookies:
                    s.write(b"Cookie: ")
                    s.write(cookie)
                    s.write(b"=")
                    s.write(cookies[cookie])
                    s.write(b"\r\n")
            if json is not None:
                assert data is None
                import ujson
                data = ujson.dumps(json)
                s.write(b"Content-Type: application/json\r\n")
            if data:
                s.write(b"Content-Length: %d\r\n" % len(data))
                # print("Content-Length: %d\r\n" % len(data))
            s.write(b"Connection: close\r\n\r\n")
            if data:
                s.write(data)
                # print(data)
            # print('Start reading http')
            l = s.readline()
            #print('Received protocoll and resultcode %s' % l.decode('utf-8'))
            l = l.split(None, 2)
            status = int(l[1])
            reason = ""
            if len(l) > 2:
                reason = l[2].rstrip()
            # Loop to read header data
            while True:
                l = s.readline()
                #print('Received Headerdata %s' % l.decode('utf-8'))
                if not l or l == b"\r\n":
                    break
                # Header data
                if l.startswith(b"Transfer-Encoding:"):
                    if b"chunked" in l:
                        # decode added, can't cast implicit from bytes to string
                        raise ValueError("Unsupported " + l.decode('utf-8'))
                elif l.startswith(b"Location:") and 300 <= status <= 399:
                    if not redir_cnt:
                        raise ValueError("Too many redirects")
                    redir_cnt -= 1
                    url = l[9:].decode().strip()
                    #print("Redirect to: %s" % url)
                    # set status as signal for loop
                    status = 302
                if parse_headers is False:
                    pass
                elif parse_headers is True:
                    l = l.decode()
                    # print('Headers: %s ' % l)
                    k, v = l.split(":", 1)
                    # adding cookie support (cookies are overwritten as they have the same key in dict)
                    # not supported is the domain attribute of cookies, this is not set
                    # new cookies are added to the supplied cookies
                    if cookies is None:
                        cookies = {}
                    if k == 'Set-Cookie':
                        ck, cv = v.split("=", 1)
                        cookies[ck.strip()] = cv.strip()
                    # else it is not a cookie, just normal header
                    else:
                        resp_d[k] = v.strip()
                else:
                    parse_headers(l, resp_d)
        except OSError:
            s.close()
            print('Socket closed')
            raise
        # if redirect repeat else leave loop
        if status != 302:
            break
        # if redirect false leave loop
        if (status == 302) and not followRedirect:
            break
        # if 302 and redirect = true then loop
    resp = Response(s)
    resp.url = url
    resp.status_code = status
    resp.reason = reason
    if resp_d is not None:
        resp.headers = resp_d
    # adding cookie support
    resp.cookies = cookies
    return resp

def head(url, **kw):
    return request("HEAD", url, **kw)

def get(url, **kw):
    return request("GET", url, **kw)

def post(url, **kw):
    return request("POST", url, **kw)

def put(url, **kw):
    return request("PUT", url, **kw)

def patch(url, **kw):
    return request("PATCH", url, **kw)

def delete(url, **kw):
    return request("DELETE", url, **kw)
