# uncompyle6 version 3.3.4
# Python bytecode 2.7 (62211)
# Decompiled from: Python 2.7.18 (v2.7.18:8d21aa21f2, Apr 20 2020, 13:25:05) [MSC v.1500 64 bit (AMD64)]
# Embedded file name: d:\BuildAgent\work\f83b6632d72c7b5b\branches\release\EVE-TRANQUILITY\eve\common\modules\crest\profiler.py
# Compiled at: 2012-09-22 05:28:34
import re, os
from collections import defaultdict
from datetime import datetime
import logging, urlparse, sys
PROFILING_PREFIX = 'crest-stat '
stats = defaultdict(list)
idRegex = re.compile('\\d+')
log = logging.getLogger(__name__)

def profile(func):
    if os.environ.has_key('DO_CLIENT_PROFILING'):

        def profiledFunc(self, *args, **kwargs):
            startTime = datetime.now()
            returnValue = func(self, *args, **kwargs)
            elapsedTime = datetime.now() - startTime
            try:
                length = int(returnValue.length)
            except TypeError:
                length = 0

            verb = args[0]
            url = args[1]
            anonymisedUrl = idRegex.sub('id', url)
            stats[(verb, anonymisedUrl)].append({'time': elapsedTime, 'length': length})
            resourcePath = urlparse.urlparse(anonymisedUrl).path
            statDict = {'verb': verb, 
               'resource': resourcePath, 
               'duration': elapsedTime.total_seconds(), 
               'length': length, 
               'timeStamp': startTime}
            if sys.platform == 'PS3':
                log.warn(PROFILING_PREFIX + str(statDict))
            else:
                log.info(PROFILING_PREFIX + str(statDict))
            return returnValue

        return profiledFunc
    return func