# uncompyle6 version 3.3.4
# Python bytecode 2.7 (62211)
# Decompiled from: Python 2.7.18 (v2.7.18:8d21aa21f2, Apr 20 2020, 13:25:05) [MSC v.1500 64 bit (AMD64)]
# Embedded file name: d:\BuildAgent\work\f83b6632d72c7b5b\branches\release\EVE-TRANQUILITY\carbon\src\stackless\Lib\json\tool.py
# Compiled at: 2012-09-22 05:05:09
import sys, json

def main():
    if len(sys.argv) == 1:
        infile = sys.stdin
        outfile = sys.stdout
    else:
        if len(sys.argv) == 2:
            infile = open(sys.argv[1], 'rb')
            outfile = sys.stdout
        else:
            if len(sys.argv) == 3:
                infile = open(sys.argv[1], 'rb')
                outfile = open(sys.argv[2], 'wb')
            else:
                raise SystemExit(sys.argv[0] + ' [infile [outfile]]')
    try:
        obj = json.load(infile)
    except ValueError as e:
        raise SystemExit(e)

    json.dump(obj, outfile, sort_keys=True, indent=4)
    outfile.write('\n')


if __name__ == '__main__':
    main()