# uncompyle6 version 3.3.4
# Python bytecode 2.7 (62211)
# Decompiled from: Python 2.7.18 (v2.7.18:8d21aa21f2, Apr 20 2020, 13:25:05) [MSC v.1500 64 bit (AMD64)]
# Embedded file name: d:\BuildAgent\work\f83b6632d72c7b5b\branches\release\EVE-TRANQUILITY\eve\common\modules\crest\file.py
# Compiled at: 2012-09-22 05:28:34
import crest.client, logging

class Resource(crest.client.Resource):

    def __init__(self, url, chunkSize=None, session=None, localTimeStamp=None):
        super(Resource, self).__init__(url, session=session)
        self.chunkSize = chunkSize
        logging.info('FILE GET: %s ', url)
        self.response = self._Request('GET', url, None, None, None, None, localTimeStamp)
        self.fileSize = 0
        try:
            self.fileSize = int(self.response.getheader('Content-Length', 0))
        except ValueError:
            pass

        logging.info('FILE GET: %s (Result: %s: %s)', url, self.response.status, self.response.reason)
        return

    def Read(self):
        if self.response is False:
            return ''
        if self.chunkSize is None or self.chunkSize <= 0:
            result = self.response.read()
        else:
            result = self.response.read(self.chunkSize)
        if not result:
            self.response = False
        return result

    def __iter__(self):
        return self

    def next(self):
        chunk = self.Read()
        if not len(chunk):
            raise StopIteration
        return chunk