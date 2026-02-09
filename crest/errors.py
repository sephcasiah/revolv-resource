# uncompyle6 version 3.3.4
# Python bytecode 2.7 (62211)
# Decompiled from: Python 2.7.18 (v2.7.18:8d21aa21f2, Apr 20 2020, 13:25:05) [MSC v.1500 64 bit (AMD64)]
# Embedded file name: d:\BuildAgent\work\f83b6632d72c7b5b\branches\release\EVE-TRANQUILITY\eve\common\modules\crest\errors.py
# Compiled at: 2012-09-22 05:28:34
from httplib import NOT_FOUND, BAD_REQUEST, UNAUTHORIZED, FORBIDDEN, INTERNAL_SERVER_ERROR, SERVICE_UNAVAILABLE, UNSUPPORTED_MEDIA_TYPE, CONFLICT, BAD_GATEWAY, GATEWAY_TIMEOUT, NOT_ACCEPTABLE

class Error(Exception):
    pass


class JsonError(Error):
    pass


class HttpError(Error):

    def __init__(self, *args, **kwargs):
        super(HttpError, self).__init__(*args)
        self.headers = kwargs.get('headers', {})
        if 'status_code' in kwargs:
            self.status_code = kwargs['status_code']
        else:
            self.status_code = INTERNAL_SERVER_ERROR
        if 'reason' in kwargs:
            self.reason = kwargs['reason']
        if 'body' in kwargs:
            self.body = kwargs['body']


def _add_status(kwargs, status):
    if 'status_code' not in kwargs:
        kwargs['status_code'] = status
    return kwargs


class HttpNotFoundError(HttpError):

    def __init__(self, *args, **kwargs):
        kwargs = _add_status(kwargs, NOT_FOUND)
        super(HttpNotFoundError, self).__init__(*args, **kwargs)


class HttpBadRequestError(HttpError):

    def __init__(self, *args, **kwargs):
        kwargs = _add_status(kwargs, BAD_REQUEST)
        super(HttpBadRequestError, self).__init__(*args, **kwargs)


class HttpServiceUnavailableError(HttpError):

    def __init__(self, *args, **kwargs):
        kwargs = _add_status(kwargs, SERVICE_UNAVAILABLE)
        super(HttpServiceUnavailableError, self).__init__(*args, **kwargs)


class HttpBadGatewayError(HttpError):

    def __init__(self, *args, **kwargs):
        kwargs = _add_status(kwargs, BAD_GATEWAY)
        super(HttpBadGatewayError, self).__init__(*args, **kwargs)


class HttpGatewayTimeoutError(HttpError):

    def __init__(self, *args, **kwargs):
        kwargs = _add_status(kwargs, GATEWAY_TIMEOUT)
        super(HttpGatewayTimeoutError, self).__init__(*args, **kwargs)


class HttpUnauthorizedError(HttpError):

    def __init__(self, *args, **kwargs):
        kwargs = _add_status(kwargs, UNAUTHORIZED)
        super(HttpUnauthorizedError, self).__init__(*args, **kwargs)


class HttpForbiddenError(HttpError):

    def __init__(self, *args, **kwargs):
        kwargs = _add_status(kwargs, FORBIDDEN)
        super(HttpForbiddenError, self).__init__(*args, **kwargs)


class HttpUnsupportedMediaType(HttpError):

    def __init__(self, *args, **kwargs):
        kwargs = _add_status(kwargs, UNSUPPORTED_MEDIA_TYPE)
        super(HttpUnsupportedMediaType, self).__init__(*args, **kwargs)


class HttpConflictError(HttpError):

    def __init__(self, *args, **kwargs):
        kwargs = _add_status(kwargs, CONFLICT)
        super(HttpConflictError, self).__init__(*args, **kwargs)


class CrestDisconnectionError(HttpError):

    def __init__(self, *args, **kwargs):
        super(CrestDisconnectionError, self).__init__(*args, **kwargs)


class CrestNotificationMissedError(CrestDisconnectionError):

    def __init__(self, *args, **kwargs):
        super(CrestNotificationMissedError, self).__init__(*args, **kwargs)


class CrestUserError(HttpForbiddenError):

    def __init__(self, *args, **kwargs):
        super(CrestUserError, self).__init__(*args, **kwargs)
        data = kwargs['data']
        self.errorTitle = data.get('title', '')
        self.errorMessage = data.get('message', '')
        self.errorType = data.get('type', '')

    def __str__(self):
        return 'HttpRepsonse: %s. Reason <UserError type=%s reason=%s message=%s>' % (
         HttpForbiddenError.__str__(self), self.errorType, self.errorTitle, self.errorMessage)


class HttpMediaTypeError(HttpError):

    def __init__(self, *args, **kwargs):
        kwargs = _add_status(kwargs, NOT_ACCEPTABLE)
        super(HttpMediaTypeError, self).__init__(*args, **kwargs)


class CrestWrongHostForSessionError(Error):

    def __init__(self, sessionHost, requestHost):
        self.sessionHost = sessionHost
        self.requestHost = requestHost