# uncompyle6 version 3.3.4
# Python bytecode 2.7 (62211)
# Decompiled from: Python 2.7.18 (v2.7.18:8d21aa21f2, Apr 20 2020, 13:25:05) [MSC v.1500 64 bit (AMD64)]
# Embedded file name: d:\BuildAgent\work\f83b6632d72c7b5b\branches\release\EVE-TRANQUILITY\eve\common\modules\crest\notifications.py
# Compiled at: 2012-09-22 05:28:34
import httplib, json, logging, socket, random, crest.errors, crest.client, sys, os
_STATUS_NOT_CONNECTED = 0
_STATUS_CONNECTED = 1
log = logging.getLogger(__name__)
if True:
    log.setLevel(logging.INFO)

class Notifications(object):

    def __init__(self, url, sleepFunction, callbackFunction, disconnectCallback=None, session=None, accept=None):
        self.accept = (', ').join(accept) if accept else 'application/json'
        self.notificationUrl = url
        self.Sleep = sleepFunction
        self.handler = callbackFunction
        self.disconnectCallback = disconnectCallback
        self.session = session
        self.Reset()

    def Reset(self):
        self.status = _STATUS_NOT_CONNECTED
        self.disconnect = False
        self.connectionError = None
        self.httpResponse = None
        self.httpConnection = None
        self.sequenceNumber = -1
        return

    def Stop(self):
        self.disconnect = True
        if self.httpResponse:
            self.httpResponse.close()
        if self.httpConnection:
            self.httpConnection.close()

    def WaitUntilConnected(self):
        waitCount = 0
        while waitCount < 200 and not self.IsConnected():
            if waitCount % 10 == 0:
                log.debug('Waiting to be connected')
            if self.HasError():
                e = self.GetConnectionError()
                self.Reset()
                raise e
            waitCount += 1
            self.Sleep(0.1)

        if waitCount >= 200:
            raise RuntimeError('Did not connect in time')
        log.debug('We have connected!')
        return True

    def Run(self):
        self.Reset()
        if self.session:
            session = self.session
        else:
            session = crest.client.Session.Get(self.notificationUrl)
        path = session.NormalizePath(self.notificationUrl)
        sendHeaders = {}
        sendHeaders.update(session.headers)
        sendHeaders['Accept'] = self.accept
        maxNumberOfRetries = 3
        currentAttempt = 0
        retryBackoffStep = 0.5
        retryBackoffFuzz = 1.0
        while currentAttempt <= maxNumberOfRetries and not self.disconnect:
            sleepFor = currentAttempt * retryBackoffStep
            if sleepFor > 0:
                try:
                    sleepFor += random.random() * retryBackoffFuzz
                    log.warning('NotificationThread sleeping before reconnection. Sleeping for %s', sleepFor)
                    self.Sleep(sleepFor)
                except Exception as e:
                    log.exception('NotificationThread exception in sleep')

            currentAttempt += 1
            log.debug('NotificationThread starting long poll on %s', self.notificationUrl)
            try:
                self.httpConnection = session.GetConnection()
                try:
                    self.httpConnection.reuse_connection(False)
                except AttributeError:
                    pass

                self.httpConnection.request('GET', path, headers=sendHeaders)
                self.httpResponse = self.httpConnection.getresponse()
                crest.client.CheckResponse('GET', self.httpResponse, self.notificationUrl)
            except Exception as e:
                self.connectionError = e
                log.error('NotificationThread terminated - Exception while connecting: %s', str(e))
                continue
            else:
                readBuffer = []
                while not self.disconnect:
                    try:
                        if sys.platform == 'PS3':
                            log.debug('NotificationRead: about to read line')
                            chunk = self.httpResponse.readline()
                        else:
                            if self.httpResponse.chunk_left is None or self.httpResponse.chunk_left == 'UNKNOWN':
                                log.debug('NotificationRead: about to read 1 char %s', self.httpResponse.chunk_left)
                                chunk = self.httpResponse.read(1)
                            else:
                                log.debug('NotificationRead: about to read chunk %s', self.httpResponse.chunk_left)
                                chunk = self.httpResponse.read(self.httpResponse.chunk_left)
                        log.debug('NotificationRead: after read read:%s', len(chunk))
                        currentAttempt = 1
                        if chunk == '':
                            self.status = _STATUS_NOT_CONNECTED
                            log.debug('NotificationThread terminated correctly')
                            if self.disconnectCallback:
                                self.disconnectCallback(self)
                            return
                        for data in chunk:
                            if data == '\n':
                                notification = ('').join(readBuffer).strip()
                                readBuffer = []
                                if notification:
                                    log.debug('NotificationRead: Finished reading a notification')
                                    self._HandleNotification(notification)
                                else:
                                    log.debug('NotificationRead: Client receiving keep-alive from %s', self.notificationUrl)
                            else:
                                if len(readBuffer) == 0:
                                    log.debug('NotificationRead: Starting to read a notification')
                                readBuffer.append(data)

                    except crest.errors.CrestNotificationMissedError as e:
                        log.exception('got a CrestNotificationMissedError error in the notification thread')
                        self.connectionError = e
                        currentAttempt = 9999999
                        break
                    except (socket.error, httplib.IncompleteRead, AttributeError, crest.errors.CrestDisconnectionError) as e:
                        if isinstance(e, socket.timeout):
                            e.args = e.args + (currentAttempt,)
                        log.exception('got another error in the notification thread')
                        self.connectionError = e
                        break
                    except Exception as e:
                        self.connectionError = e
                        log.exception('Unexpected Exception in notification thread')
                        break

                try:
                    self.httpResponse.close()
                except:
                    log.exception('Unexpected Exception in notification thread calling httpResponse.close')

        log.debug('NotificationThread exiting')
        self.status = _STATUS_NOT_CONNECTED
        if self.disconnectCallback:
            self.disconnectCallback(self)
        if not self.disconnect:
            log.error('NotificationThread exited in error')
            raise crest.errors.CrestDisconnectionError('Unable to reconnect, max retry exceeded')
        return

    def GetConnectionError(self):
        return self.connectionError

    def HasError(self):
        return self.connectionError is not None

    def IsConnected(self):
        return self.status == _STATUS_CONNECTED

    def _HandleNotification(self, notification):
        try:
            notification = json.loads(notification)
        except (ValueError, TypeError):
            log.error('Non json notification: %s' % notification)
            raise crest.errors.CrestDisconnectionError(e)

        seqNo = notification.get('sequenceNumber', None)
        data = notification.get('data', None)
        log.debug('Got notification #%s (expecting %s) data=%s', seqNo, self.sequenceNumber, data)
        if seqNo is None or data is None:
            log.error('Invalid notification: %s' % notification)
            raise crest.errors.CrestDisconnectionError('Invalid notification received')
        if self.sequenceNumber > seqNo - 1:
            if data != 'CCP_HELLO':
                log.warning('Got a previously seen notification  Received: %d, Expecting: %d' % (seqNo, self.sequenceNumber))
                return
        else:
            if self.sequenceNumber < seqNo - 1:
                raise crest.errors.CrestNotificationMissedError('Wrong sequence number, missed notification?')
            else:
                self.sequenceNumber = seqNo
        if data == 'CCP_HELLO':
            log.debug('NotificationThread Connected')
            self.status = _STATUS_CONNECTED
        else:
            if self.handler:
                try:
                    self.handler(data)
                except:
                    log.exception('Got exception in handler, silencing it to keep on going')

            else:
                log.warning('Ignoring notification (no callback) %s: %s', seqNo, data)
        return