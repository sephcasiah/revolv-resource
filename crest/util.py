# uncompyle6 version 3.3.4
# Python bytecode 2.7 (62211)
# Decompiled from: Python 2.7.18 (v2.7.18:8d21aa21f2, Apr 20 2020, 13:25:05) [MSC v.1500 64 bit (AMD64)]
# Embedded file name: d:\BuildAgent\work\f83b6632d72c7b5b\branches\release\EVE-TRANQUILITY\eve\common\modules\crest\util.py
# Compiled at: 2012-09-22 05:28:34
import time, datetime, crest.errors

def ParseDate(date):
    return datetime.datetime.strptime(date, '%Y-%m-%dT%H:%M:%S')


def FormatBlueDate(date):
    if date is None:
        return
    EPOCH_AS_FILETIME = 116444736000000000L
    HUNDREDS_OF_NANOSECONDS = 10000000
    timestamp, nanoseconds = divmod(date - EPOCH_AS_FILETIME, HUNDREDS_OF_NANOSECONDS)
    return FormatDate(datetime.datetime.utcfromtimestamp(timestamp))


def FormatDate(date):
    return date.strftime('%Y-%m-%dT%H:%M:%S')


def RetryWhileRaises(exceptions, method, *args, **kwargs):
    retries = kwargs.pop('retry', 3)
    sleep = kwargs.pop('sleep', 2)
    while retries > 0:
        retries -= 1
        try:
            return method(*args, **kwargs)
        except exceptions:
            time.sleep(sleep)
            continue

    raise RuntimeError('Timed out while waiting for exceptions: ' + str(exceptions))


def RetryWhileUnavailable(method, *args, **kwargs):
    exceptions = (
     crest.errors.HttpServiceUnavailableError,
     crest.errors.HttpBadGatewayError,
     crest.errors.HttpGatewayTimeoutError,
     crest.errors.CrestDisconnectionError)
    return RetryWhileRaises(exceptions, method, *args, **kwargs)