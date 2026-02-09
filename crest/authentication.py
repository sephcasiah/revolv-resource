# uncompyle6 version 3.3.4
# Python bytecode 2.7 (62211)
# Decompiled from: Python 2.7.18 (v2.7.18:8d21aa21f2, Apr 20 2020, 13:25:05) [MSC v.1500 64 bit (AMD64)]
# Embedded file name: d:\BuildAgent\work\f83b6632d72c7b5b\branches\release\EVE-TRANQUILITY\eve\common\modules\crest\authentication.py
# Compiled at: 2012-09-22 05:28:34
import base64, urllib, crest.client, logging
log = logging.getLogger(__name__)

def _MachoNetPasswordHash(userName, password):
    unicodeUserName = unicode(userName).strip()
    unicodePassword = unicode(password)
    salt = unicodeUserName.lower().encode('utf_16_le')
    from hashlib import sha1
    hashValue = sha1(unicodePassword.encode('utf_16_le') + salt)
    for i in xrange(1000):
        hashValue = sha1(hashValue.digest() + salt)

    return hashValue.digest()


def Authenticate(url, authData, payload=None):
    if 'scope' not in authData:
        authData['scope'] = 'dust'
    if 'client_id' not in authData:
        authData['client_id'] = 'dust'
    authData['grant_type'] = 'password'
    if not payload:
        username = authData['username']
        password = authData['password']
        authData['password'] = base64.b64encode(_MachoNetPasswordHash(username, password))
    log.info('Doing authentication against %s using data %s', url, authData)
    data = crest.client.Resource(url).Post(payload, authData)
    log.info('Authenticate response: %s' % data)
    return data.get('access_token', None)


def OAuthUsernamePassword(ssoServer, scope, username, password, clientID, clientSecret, characterID=None, languageID='en-us'):
    payload = {'grant_type': 'password', 
       'scope': scope, 
       'username': username, 
       'password': base64.b64encode(_MachoNetPasswordHash(username, password))}
    if characterID:
        payload['character'] = characterID
    return OAuthAuthenticate(ssoServer, payload, clientID, clientSecret, languageID)


def PsnOAuthLogin(ssoServer, scope, psnTicket, clientID, clientSecret, email=None, characterID=None, languageID='en-us'):
    payload = {'grant_type': 'password', 
       'scope': scope, 
       'psn_ticket': base64.b64encode(psnTicket)}
    if email is not None:
        payload['email'] = email
    if characterID is not None:
        payload['character'] = characterID
    return OAuthAuthenticate(ssoServer, payload, clientID, clientSecret, languageID)


def OAuthRefreshToken(ssoServer, refreshToken, clientID, clientSecret, scope=None, characterID=None, languageID='en-us'):
    payload = {'grant_type': 'refresh_token', 
       'refresh_token': refreshToken}
    if scope:
        payload['scope'] = scope
    if characterID:
        payload['character'] = characterID
    return OAuthAuthenticate(ssoServer, payload, clientID, clientSecret, languageID)


def OAuthAuthenticate(ssoServer, payload, clientID, clientSecret, languageID):
    log.info('Doing authentication against %s using payload; %s', ssoServer, payload)
    connection = crest.client.Session(ssoServer).GetConnection()
    payload = urllib.urlencode(payload)
    authorization = base64.b64encode('%s:%s' % (clientID, clientSecret))
    headers = {'Content-type': 'application/x-www-form-urlencoded', 
       'Accept': 'application/json', 
       'Content-Length': str(len(payload)), 
       'Authorization': 'Basic %s' % authorization, 
       'Accept-Language': languageID}
    log.info('POST server: %s\n\t payload: %s\n\t headers %s', ssoServer, payload, headers)
    connection.request('POST', ssoServer, payload, headers)
    response = connection.getresponse(buffering=True)
    try:
        crest.client.CheckResponse('POST', response)
        data = crest.client.ParseData(response.read())
    finally:
        response.close()

    log.info('Authenticate response: %s' % data)
    return data