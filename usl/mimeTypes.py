# uncompyle6 version 3.3.4
# Python bytecode 2.7 (62211)
# Decompiled from: Python 2.7.18 (v2.7.18:8d21aa21f2, Apr 20 2020, 13:25:05) [MSC v.1500 64 bit (AMD64)]
# Embedded file name: d:\BuildAgent\work\f83b6632d72c7b5b\branches\release\EVE-TRANQUILITY\eve\common\modules\usl\mimeTypes.py
# Compiled at: 2012-09-22 05:28:41
import urlparse, re
MimeTypes = {}

class MediaType(object):

    def __init__(self, name, attributes, description=None, relatedTypeNames=None):
        self.name = name
        self.attributes = attributes
        self.description = description
        self.relatedTypeNames = relatedTypeNames or []

    def __str__(self):
        return self.name

    @property
    def jsonType(self):
        return 'application/%s+json' % self.name


def RegisterType(name, attributes, description=None):
    type = MediaType(name, attributes, description)
    MimeTypes[name] = type
    return type


def RegisterPagedCollection(name, items, subTypeName=None):
    attributes = {'items': {'type': Array(items, subTypeName=subTypeName), 
                 'description': 'References to the data'}, 
       'pageCount': {'description': 'Total number of pages', 
                     'type': int, 
                     'optional': True}, 
       'totalCount': {'description': 'Number of total items in all pages', 
                      'type': int, 
                      'optional': True}, 
       'next': {'description': 'Reference to the next page', 
                'type': Ref(), 
                'optional': True}, 
       'previous': {'description': 'Reference to the previous page', 
                    'type': Ref(), 
                    'optional': True}}
    type = MediaType(name, attributes)
    MimeTypes[name] = type
    return type


def RegisterCollectionTypeNew(mediaType, denormalize=None, attributes=None, name=None, subTypeName=None, itemName=None):
    collectionName = name or '%sCollection' % mediaType.name
    attributes = attributes or {}
    denormalize = denormalize or []
    itemName = itemName or 'item'
    attributes.update({'href': {'description': 'URI of the %s' % itemName}})
    for each in denormalize:
        attributes[each] = mediaType.attributes[each]
        attributes[each]['optional'] = True

    page = {'items': {'type': Array(attributes, subTypeName=subTypeName), 'description': 'References to %s' % mediaType.name}, 'pageCount': {'description': 'Total number of pages', 'type': int, 'optional': True}, 'totalCount': {'description': 'Number of total items in all pages', 'type': int, 'optional': True}, 'next': {'description': 'Number of total items in all pages', 'type': Ref(), 'optional': True}, 'previous': {'description': 'Number of total items in all pages', 'type': Ref(), 'optional': True}}
    collectionType = MediaType(collectionName, page)
    MimeTypes[collectionName] = collectionType
    return collectionType


def RegisterCollectionType(mediaType, denormalize=None, name=None):
    collectionName = name or '%sCollection' % mediaType.name
    denormalize = denormalize or []
    items = {'href': {'description': 'Canonical URI to the item', 'type': Ref()}}
    for each in denormalize:
        items[each] = mediaType.attributes[each]

    attributes = {'items': {'type': Array(items), 'description': 'References to %s and optionally denormalized data' % mediaType.name}, 'pageCount': {'description': 'Total number of pages', 'type': int}, 'totalCount': {'description': 'Number of total items in all pages', 'type': int}, 'next': {'description': 'Number of total items in all pages', 'type': Ref(), 'optional': True}, 'previous': {'description': 'Number of total items in all pages', 'type': Ref(), 'optional': True}}
    collectionType = MediaType(collectionName, attributes)
    MimeTypes[collectionName] = collectionType
    return collectionType


def _CheckForExtraData(data, attributes, name):
    extraAttributes = set(data.keys())
    extraAttributes -= set(attributes.keys())
    if len(extraAttributes) > 0:
        raise ValueError('Unexpected %s in %s' % ((',').join([ str(i) for i in extraAttributes ]), name))


def _ConstructDict(data, attributes, name, strict=False, partial=False):
    result = {}
    for attributeName, attributeInfo in attributes.iteritems():
        if data is not None:
            if attributeName in data:
                value = data[attributeName]
            else:
                if name in attributeInfo.get('required', []):
                    raise ValueError('%s required in %s' % (attributeName, name))
                if partial:
                    continue
                elif 'default' in attributeInfo:
                    value = attributeInfo['default']
                elif attributeInfo.get('optional', False):
                    continue
                else:
                    raise ValueError('Expected %s in %s' % (attributeName, name))
        else:
            raise ValueError('%s can not be None in %s' % (attributeName, name))
        typeFunction = attributeInfo.get('type', None)
        if typeFunction and value is not None:
            try:
                if hasattr(typeFunction, '__name__') and typeFunction.__name__ in ('array',
                                                                                   'dict'):
                    value = typeFunction(value, strict=strict, partial=partial)
                else:
                    value = typeFunction(value)
            except Exception as e:
                raise TypeError('Expected %s to be of type %s in %s (%s)' % (attributeName, typeFunction.__name__, name, e))

        result[attributeName] = value

    return result


def ConstructResource(data, mimeTypeName, strict=False, partial=False):
    mimeTypeName = str(mimeTypeName)
    mimeType = MimeTypes[mimeTypeName]
    if strict:
        _CheckForExtraData(data, mimeType.attributes, mimeTypeName)
    return _ConstructDict(data, mimeType.attributes, mimeTypeName, strict=strict, partial=partial)


def MatchRef(uri, handlers):
    path = urlparse.urlparse(uri)[2]
    for handler in handlers:
        match = re.match(handler.Route(), path)
        if match is not None:
            return (handler, match.groups())

    raise ValueError
    return


def Ref(*args):

    class _Ref(dict):

        def __name__(self):
            if len(args) == 0:
                return 'reference'
            return 'reference to any of %s' % (' ').join(handler.get('resourceName', str(handler)) for handler in args)

        def __init__(self, value):
            super(_Ref, self).__init__(_ConstructDict(value, {'href': {}}, 'vnd.ccp.eve.Ref'))
            if len(args) > 0:
                try:
                    self.handler, self.groups = MatchRef(self['href'], args)
                except ValueError:
                    raise ValueError('%s does not contain a %s', value, self.__name__())

    return _Ref


def TypedRef(mimeType, attributes=None):
    attributes = attributes or {}

    class _Ref(object):

        def __name__(self):
            return 'reference to %s' % mimeType

        def __init__(self, value):
            self.value = Ref()(value)
            parts = self.value['href'].split('/')
            parts.reverse()
            self.id = None
            for each in parts:
                try:
                    self.id = long(each)
                    break
                except ValueError:
                    continue

            if self.id is None:
                raise ValueError('%s does not contain ID but claims to be a %s', value, self.__name__())
            return

        def __getitem__(self, item):
            return self.value[item]

    return _Ref


def TypedRefArray(types, attributes=None):
    attributes = attributes or {}

    class RefArray(object):

        def __name__(self):
            return 'Collection of references to any of %s' % ((' ').join(types),)

        def __init__(self, collection):
            self.collection = []
            for each in collection:
                self.collection.append(TypedRef('thing', attributes=attributes)(each))

        def __iter__(self):
            return self.collection.__iter__()

    return RefArray


def RefArray(array, attributes):
    for ref in array:
        if not isinstance(ref, dict):
            raise TypeError('Expected each part of a ref array to be a type containing hrefs')
        if 'href' not in ref:
            raise KeyError

    return array


def Array(subType, subTypeName=None):

    def CheckTypes(seq, strict=False, partial=False):
        for i in range(len(seq)):
            item = seq[i]
            if strict:
                _CheckForExtraData(item, subType, 'array')
            seq[i] = _ConstructDict(item, subType, subTypeName, strict=strict, partial=partial)

        return seq

    CheckTypes.__name__ = 'array'
    CheckTypes.__dict__['COW_sub_type'] = subType
    CheckTypes.__dict__['COW_sub_type_name'] = subTypeName
    return CheckTypes


def Dict(subType, subTypeName=None):

    def CheckTypes(item, strict=False, partial=False):
        if strict:
            _CheckForExtraData(item, subType, 'dict')
        return _ConstructDict(item, subType, subTypeName, strict=strict, partial=partial)

    CheckTypes.__name__ = 'dict'
    CheckTypes.__dict__['COW_sub_type'] = subType
    CheckTypes.__dict__['COW_sub_type_name'] = subTypeName
    return CheckTypes


def Number(value):
    float(value)
    return value