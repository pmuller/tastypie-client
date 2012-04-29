"""Serializers"""

import sys


try:
    import json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        sys.write('ERROR: Please install the `json` or `simplejson` module')
        sys.exit(-1)


class JsonSerializer(object):
    """Simple JSON serializer"""
    def encode(self, data):
        return json.dumps(data)
    def decode(self, data):
        return json.loads(data)
