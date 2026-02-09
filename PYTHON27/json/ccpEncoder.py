# uncompyle6 version 3.3.4
# Python bytecode 2.7 (62211)
# Decompiled from: Python 2.7.18 (v2.7.18:8d21aa21f2, Apr 20 2020, 13:25:05) [MSC v.1500 64 bit (AMD64)]
# Embedded file name: d:\BuildAgent\work\f83b6632d72c7b5b\branches\release\EVE-TRANQUILITY\carbon\src\stackless\Lib\json\ccpEncoder.py
# Compiled at: 2012-09-22 05:05:09


class IterNodeMaker(object):
    __slots__ = [
     'markers', '_default', '_encoder', '_indent', '_floatstr',
     '_key_separator', '_item_separator', '_sort_keys', '_skipkeys', '_one_shot']

    def __init__(self, markers, _default, _encoder, _indent, _floatstr, _key_separator, _item_separator, _sort_keys, _skipkeys, _one_shot):
        self.markers = markers
        self._default = _default
        self._encoder = _encoder
        self._indent = _indent
        self._floatstr = _floatstr
        self._key_separator = _key_separator
        self._item_separator = _item_separator
        self._sort_keys = _sort_keys
        self._skipkeys = _skipkeys
        self._one_shot = _one_shot

    def _make_iterencode_ccp(self):
        return self._iterencode_ccp

    def _iterencode_ccp(self, o, _current_indent_level):
        if isinstance(o, basestring):
            yield self._encoder(o)
        else:
            if o is None:
                yield 'null'
            else:
                if o is True:
                    yield 'true'
                else:
                    if o is False:
                        yield 'false'
                    else:
                        if isinstance(o, (int, long)):
                            yield str(o)
                        else:
                            if isinstance(o, float):
                                yield self._floatstr(o)
                            else:
                                if isinstance(o, (list, tuple)):
                                    for chunk in self._iterencode_list_ccp(o, _current_indent_level):
                                        yield chunk

                                else:
                                    if isinstance(o, dict):
                                        for chunk in self._iterencode_dict_ccp(o, _current_indent_level):
                                            yield chunk

                                    else:
                                        if self.markers is not None:
                                            markerid = id(o)
                                            if markerid in self.markers:
                                                raise ValueError('Circular reference detected')
                                            self.markers[markerid] = o
                                        o = self._default(o)
                                        for chunk in self._iterencode_ccp(o, _current_indent_level):
                                            yield chunk

                                    if self.markers is not None:
                                        del self.markers[markerid]
        return

    def _iterencode_list_ccp(self, lst, _current_indent_level):
        if not lst:
            yield '[]'
            return
        if self.markers is not None:
            markerid = id(lst)
            if markerid in self.markers:
                raise ValueError('Circular reference detected')
            self.markers[markerid] = lst
        buf = '['
        if self._indent is not None:
            _current_indent_level += 1
            newline_indent = '\n' + ' ' * (self._indent * _current_indent_level)
            separator = self._item_separator + newline_indent
            buf += newline_indent
        else:
            newline_indent = None
            separator = self._item_separator
        first = True
        for value in lst:
            if first:
                first = False
            else:
                buf = separator
            if isinstance(value, basestring):
                yield buf + self._encoder(value)
            elif value is None:
                yield buf + 'null'
            elif value is True:
                yield buf + 'true'
            elif value is False:
                yield buf + 'false'
            elif isinstance(value, (int, long)):
                yield buf + str(value)
            elif isinstance(value, float):
                yield buf + self._floatstr(value)
            else:
                yield buf
                if isinstance(value, (list, tuple)):
                    chunks = self._iterencode_list_ccp(value, _current_indent_level)
                else:
                    if isinstance(value, dict):
                        chunks = self._iterencode_dict_ccp(value, _current_indent_level)
                    else:
                        chunks = self._iterencode_ccp(value, _current_indent_level)
                for chunk in chunks:
                    yield chunk

        if newline_indent is not None:
            _current_indent_level -= 1
            yield '\n' + ' ' * (self._indent * _current_indent_level)
        yield ']'
        if self.markers is not None:
            del self.markers[markerid]
        return

    def _iterencode_dict_ccp(self, dct, _current_indent_level):
        if not dct:
            yield '{}'
            return
        if self.markers is not None:
            markerid = id(dct)
            if markerid in self.markers:
                raise ValueError('Circular reference detected')
            self.markers[markerid] = dct
        yield '{'
        if self._indent is not None:
            _current_indent_level += 1
            newline_indent = '\n' + ' ' * (self._indent * _current_indent_level)
            item_separator = self._item_separator + newline_indent
            yield newline_indent
        else:
            newline_indent = None
            item_separator = self._item_separator
        first = True
        if self._sort_keys:
            items = sorted(dct.items(), key=lambda kv: kv[0])
        else:
            items = dct.iteritems()
        for key, value in items:
            if isinstance(key, basestring):
                pass
            else:
                if isinstance(key, float):
                    key = self._floatstr(key)
                else:
                    if key is True:
                        key = 'true'
                    else:
                        if key is False:
                            key = 'false'
                        else:
                            if key is None:
                                key = 'null'
                            else:
                                if isinstance(key, (int, long)):
                                    key = str(key)
                                else:
                                    if self._skipkeys:
                                        continue
                                    else:
                                        raise TypeError('key ' + repr(key) + ' is not a string')
            if first:
                first = False
            else:
                yield item_separator
            yield self._encoder(key)
            yield self._key_separator
            if isinstance(value, basestring):
                yield self._encoder(value)
            elif value is None:
                yield 'null'
            elif value is True:
                yield 'true'
            elif value is False:
                yield 'false'
            elif isinstance(value, (int, long)):
                yield str(value)
            elif isinstance(value, float):
                yield self._floatstr(value)
            else:
                if isinstance(value, (list, tuple)):
                    chunks = self._iterencode_list_ccp(value, _current_indent_level)
                else:
                    if isinstance(value, dict):
                        chunks = self._iterencode_dict_ccp(value, _current_indent_level)
                    else:
                        chunks = self._iterencode_ccp(value, _current_indent_level)
                for chunk in chunks:
                    yield chunk

        if newline_indent is not None:
            _current_indent_level -= 1
            yield '\n' + ' ' * (self._indent * _current_indent_level)
        yield '}'
        if self.markers is not None:
            del self.markers[markerid]
        return