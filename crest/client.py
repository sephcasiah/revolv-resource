# uncompyle6 version 3.3.4
# Python bytecode 2.7 (62211)
# Decompiled from: Python 2.7.18 (v2.7.18:8d21aa21f2, Apr 20 2020, 13:25:05) [MSC v.1500 64 bit (AMD64)]
# Embedded file name: d:\BuildAgent\work\f83b6632d72c7b5b\branches\release\EVE-TRANQUILITY\eve\common\modules\crest\client.py
# Compiled at: 2012-09-22 05:28:34
import httplib, json, logging, urllib, urlparse, socket, errno, profiler, os, re
from datetime import datetime
import crest.errors, math
try:
    from stacklesslib.main import sleep
except ImportError:
    from time import sleep

SAFE_RETRIES = (
 errno.ECONNRESET, errno.ENETRESET, errno.ECONNABORTED, errno.ETIMEDOUT, errno.EAGAIN)
log = logging.getLogger(__name__)
DEFAULT_MIMETYPE = 'application/json'
HEADER_ACCEPT_TYPE = 'Accept'
HEADER_USER_AGENT = 'User-Agent'
HEADER_CONTENT_TYPE = 'Content-Type'
HEADER_CONTENT_LENGTH = 'Content-Length'
HEADER_AUTHORIZATION = 'Authorization'
HEADER_IF_MODIFIED_SINCE = 'If-Modified-Since'
GET_RESPONSE_CODES = (
 httplib.OK, httplib.NOT_MODIFIED, httplib.FOUND)
MODIFY_RESPONSE_CODES = (httplib.OK, httplib.CREATED, httplib.ACCEPTED, httplib.NO_CONTENT, httplib.FOUND)
expectedCodes = {'GET': GET_RESPONSE_CODES, 
   'PUT': MODIFY_RESPONSE_CODES, 
   'POST': MODIFY_RESPONSE_CODES, 
   'DELETE': MODIFY_RESPONSE_CODES}
if os.environ.has_key('VERBOSE_HTTP_CONNECTION'):
    VERBOSE_HTTP_CONNECTION = True
else:
    VERBOSE_HTTP_CONNECTION = False

class Session(object):
    _sessions = {}
    default = None

    @classmethod
    def Get(cls, url):
        if url in Session._sessions:
            return Session._sessions[url]
        urlParts = urlparse.urlparse(url)
        if not urlParts.scheme or not urlParts.netloc:
            raise RuntimeError('Please provide full uris for Crest HTTP Sessions')
        host = '%s://%s' % (urlParts.scheme, urlParts.netloc)
        if host not in Session._sessions:
            Session._sessions[host] = Session(host)
        return Session._sessions[host]

    def __init__(self, url, headers=None, sleepFunction=sleep):
        if not headers:
            headers = {}
        self.headers = headers
        self.Sleep = sleepFunction
        parts = urlparse.urlparse(url)
        self.schemeHost = _GetSchemeAndHost(parts)
        hostPortParts = parts.netloc.split(':')
        port = None
        host = hostPortParts[0]
        if len(hostPortParts) == 2:
            port = int(hostPortParts[1])
        self.host = host
        self.port = port
        return

    def AddHeaders(self, headers):
        self.headers.update(headers)

    def ClearHeaders(self):
        self.headers = {}

    def AddAccessToken(self, accessToken, tokenType='Bearer'):
        self.AddHeaders({HEADER_AUTHORIZATION: '%s %s' % (tokenType, accessToken)})

    def GetConnection(self):
        if self.schemeHost.startswith('https'):
            return httplib.HTTPSConnection(self.host, self.port)
        return httplib.HTTPConnection(self.host, self.port)

    def Resource(self, uri):
        return Resource(uri, session=self)

    def NormalizePath(self, url):
        if url.startswith(self.schemeHost):
            return url[len(self.schemeHost):len(url)]
        return url

    def SetDefault(self):
        Session.default = self
        return Session.default


class Resource(object):

    def __init__(self, url, session=None):
        if not url or isinstance(url, dict):
            raise RuntimeError('URLs should always be strings, got %s' % url)
        self.url = url
        self.session = session

    def Get(self, parameters=None, accept=None, headers=False):
        if accept is None:
            log.warning('no accept type specified for GET %s', self.url)
        return self._ProcessRequest('GET', None, parameters, accept, None, headers)

    def Post(self, data, parameters=None, accept=None, content=None, headers=False):
        return self._ProcessRequest('POST', data, parameters, accept, content, headers)

    def Put(self, data, parameters=None, accept=None, content=None, headers=False):
        return self._ProcessRequest('PUT', data, parameters, accept, content, headers)

    def Delete(self, data=None, parameters=None, accept=None, headers=False):
        return self._ProcessRequest('DELETE', data, parameters, accept, None, headers)

    def _ProcessRequest(self, method, data, parameters, accept, content, headers):

        def retry_func():
            self.response = self._Request(method, self.url, data, parameters, accept=accept, content=content)
            try:
                result = ParseData(self.response.read())
                if headers:
                    headerList = self.response.getheaders()
                    headerDict = {k.lower():v for k, v in headerList}
                    result = (
                     result, headerDict)
                return result
            finally:
                self.response.close()

        return self._RetryIfFailed(retry_func, method, (method, self.url))

    @profiler.profile
    def _Request(self, method, url, data, params, accept, content, ifModifySince=None):
        log.debug('%s: %s ', method, url)
        CheckRequestMimetypes(method, accept, content)
        userAgent = 'CCPGamesCrestClient/1.0'
        sendHeaders = {HEADER_USER_AGENT: userAgent, 'X-CCP-User-Agent': userAgent}
        if accept:
            acceptType = 'application/%s+json' % accept
            sendHeaders.update({HEADER_ACCEPT_TYPE: acceptType})
        else:
            sendHeaders.update({HEADER_ACCEPT_TYPE: DEFAULT_MIMETYPE})
        if data and content:
            contentType = 'application/%s+json' % content
            sendHeaders.update({HEADER_CONTENT_TYPE: contentType})
        else:
            sendHeaders.update({HEADER_CONTENT_TYPE: DEFAULT_MIMETYPE})
        if ifModifySince:
            cacheTime = datetime.utcfromtimestamp(ifModifySince)
            cacheHeader = cacheTime.strftime('%a, %d %b %Y %H:%M:%S GMT')
            sendHeaders.update({HEADER_IF_MODIFIED_SINCE: cacheHeader})
        sendData = None
        if method in ('POST', 'PUT', 'DELETE'):
            contentSize = 0
            if data is not None:
                sendData = json.dumps(data)
                contentSize = len(sendData)
            sendHeaders.update({HEADER_CONTENT_LENGTH: str(contentSize)})
        urlParts = urlparse.urlparse(url)
        if params:
            url += '&' if urlParts.query else '?'
            url += urllib.urlencode(params)
        schemeHost = _GetSchemeAndHost(urlParts)
        if self.session:
            session = self.session
            if schemeHost and session.schemeHost != schemeHost:
                raise crest.errors.CrestWrongHostForSessionError(sessionHost=session.schemeHost, requestHost=schemeHost)
        else:
            if not schemeHost:
                session = Session.default
                if not session:
                    raise RuntimeError("You can't use relative paths when there is no default session set")
            else:
                session = Session.Get(url)
        sendHeaders.update(session.headers)
        conn = session.GetConnection()
        path = session.NormalizePath(url)
        if VERBOSE_HTTP_CONNECTION:
            conn.set_debuglevel(logging.DEBUG)
            log.setLevel(logging.INFO)
        conn.request(method, path, sendData, sendHeaders)
        response = conn.getresponse(buffering=True)
        CheckResponse(method, response, url)
        log.debug('CrestClient> %s: %s%s (Result: %s: %s)', method, schemeHost, path, response.status, response.reason)
        return response

    def _RetryIfFailed(self, func, method, description, retries=3, maxSleeptimeMs=250):
        if retries <= 0:
            raise ValueError('Retries must be a positive integer.  Got: %d', retries)
        if maxSleeptimeMs <= 0:
            raise ValueError('maxSleeptimeMs must be a positive integer.  Got: %d', maxSleeptimeMs)
        totalRetries = retries
        while True:
            try:
                return func()
            except (socket.timeout, socket.error, httplib.HTTPException) as e:
                if retries <= 0:
                    log.error('We ran out of retries and is now re-raising the error for %r', description)
                    raise
                if not (method == 'GET' or type(e) is socket.error and e.args[0] in SAFE_RETRIES):
                    raise
                sleepTime = maxSleeptimeMs * math.pow(retries, -1) / 1000.0
                log.debug('Scheduling retry %r with %d times left out of %d time because of %r in %s', description, retries, totalRetries, e, sleepTime)
                try:
                    if self.session is not None:
                        self.session.Sleep(sleepTime)
                    else:
                        sleep(sleepTime)
                except Exception:
                    log.exception('Exception in _RetryIfFailed::sleep')

                retries -= 1
                log.warning('Retrying %r with %d times left out of %d time because of %r', description, retries, totalRetries, e)

        return


_typedHttpExceptions = {httplib.PRECONDITION_FAILED: crest.errors.CrestUserError, 
   httplib.FORBIDDEN: crest.errors.CrestUserError, 
   httplib.SERVICE_UNAVAILABLE: crest.errors.HttpServiceUnavailableError, 
   httplib.UNAUTHORIZED: crest.errors.HttpUnauthorizedError, 
   httplib.NOT_FOUND: crest.errors.HttpNotFoundError, 
   httplib.BAD_REQUEST: crest.errors.HttpBadRequestError, 
   httplib.UNSUPPORTED_MEDIA_TYPE: crest.errors.HttpUnsupportedMediaType, 
   httplib.CONFLICT: crest.errors.HttpConflictError, 
   httplib.NOT_ACCEPTABLE: crest.errors.HttpMediaTypeError, 
   httplib.NOT_IMPLEMENTED: crest.errors.HttpMediaTypeError}

def CheckRequestMimetypes(method, accept, content, strict=False):
    ok = True
    if not accept and not content:
        log.warning('no accept or content declared.  Please fix.')
        ok = False
    if accept is not None and not isinstance(accept, basestring):
        accept = accept.name
        log.warning('accept=[%s] declared using object not string.  Please fix.', accept)
        ok = False
    if content is not None and not isinstance(content, basestring):
        content = content.name
        log.warning('content=[%s] declared using object not string.  Please fix.', content)
        ok = False
    if strict and not ok:
        raise RuntimeError('Mimetype not specified correctly!')
    return


def CheckResponse(method, response, url=None):
    if response.status not in expectedCodes[method]:
        kwargs = dict(status_code=response.status, reason=response.reason, body=response.read(), url=url, headers=dict(response.getheaders()))
        args = [
         kwargs['body']]
        if response.status not in _typedHttpExceptions:
            raise crest.errors.HttpError(*args, **kwargs)
        klass = _typedHttpExceptions[response.status]
        if klass is crest.errors.CrestUserError:
            try:
                data = json.loads(kwargs['body'])
                kwargs.update({'data': dict(title=data['title'], message=data['message'], type=data['type'])})
            except (ValueError, TypeError, KeyError):
                klass = crest.errors.HttpForbiddenError

        log.debug('crest.client:CheckResponse got status %s, raising error %s ', response.status, klass)
        raise klass(*args, **kwargs)


def ParseData(data):
    if len(data):
        if data == '{}':
            return {}
        try:
            return json.loads(data)
        except ValueError as e:
            raise crest.errors.JsonError('Client library could not extract JSON from response', e, data)


def _GetSchemeAndHost(urlParts):
    if urlParts.scheme and urlParts.netloc:
        return '%s://%s' % (urlParts.scheme, urlParts.netloc)


_http_regex = re.compile('https?://[^/]+')

def StripServerNameFromURI(uri):
    return _http_regex.sub('', uri)


def AreURIsEqual(uri0, uri1):
    uri0 = StripServerNameFromURI(uri0)
    uri1 = StripServerNameFromURI(uri1)
    return uri0 == uri1