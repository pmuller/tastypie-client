"""Core"""

import pprint
import urlparse
import urllib

import requests

from tastypie_client.serializers import JsonSerializer
from tastypie_client.exceptions import \
    BadHttpStatus, ResourceTypeMissing, ResourceIdMissing, TooManyResources


class EndpointProxy(object):
    """Proxy object to a service endpoint"""

    def __init__(self, api, endpoint_url, schema_url):
        self._api = api
        self._endpoint_url = endpoint_url
        self._schema_url = schema_url
        self._resource = filter(bool, endpoint_url.split('/'))[-1]

    def __repr__(self):
        return '<EndpointProxy %s>' % self._api._get_url(self._resource)

    def _get_url(self):
        return '%s%s' % (self._api.base_url, self._endpoint_url)

    def __call__(self, id=None, **kw):
        return self._api(self._resource, id, **kw)

    def many(self, *ids, **kw):
        return self._api.many(self._resource, *ids, **kw)

    def find(self, **kw):
        return self._api.find(self._resource, **kw)


class ResourceProxy(object):
    """Proxy object to a resource

    It lazily fetches data.
    """

    def __init__(self, url, service, api):
        self._url = url
        self._service = service
        self._api = api
        self._type, id = self._service.parse_resource_url(self._url)
        self._id = int(id)
        self._resource = None

    def __repr__(self):
        if self._resource:
            return repr(self._resource)
        else:
            return '<ResourceProxy %s/%s>' % (self._type, self._id)

    def __getattr__(self, attr):
        return getattr(self._get(), attr)

    def __getitem__(self, item):
        return self._get()[item]

    def __contains__(self, attr):
        return attr in self._get()

    def _get(self):
        """Load the resource
        
        Do nothing if already loaded.
        """
        if not self._resource:
            self._resource = self._api(self._type, self._id)
        return self._resource


class Resource(object):
    """A fetched resource"""

    def __init__(self, resource, type, id, url):
        self._resource = resource
        self._type = type
        self._id = id
        self._url = url

    def __repr__(self):
        return '<Resource %s: %s>' % (self._url, self._resource)

    def __getattr__(self, attr):
        if attr in self._resource:
            return self._resource[attr]
        else:
            raise AttributeError(attr)
    
    def __getitem__(self, item):
        if item in self._resource:
            return self._resource[item]
        else:
            raise KeyError(item)

    def __contains__(self, attr):
        return attr in self._resource


class ResourceListMixin(object):

    def values(self):
        return [ r._resource for r in self[:] ]

    def values_list(self, *fields, **kw):
        if 'flat' in kw and kw['flat'] is True:
            if len(fields) != 1:
                raise Exception('Can\'t flatten if more than 1 field')
            field = fields[0]
            return [ getattr(r, field) for r in self[:] ]
        else:
            return [ tuple(getattr(r, f) for f in fields) for r in self[:] ]


class SearchResponse(ResourceListMixin):
    """A service response containing multiple resources"""

    def __init__(self, api, type, meta, resources, kw={}):
        self._api = api
        self._type = type
        self._total_count = meta['total_count']
        self._resources = dict(enumerate(resources))
        self._kw = kw

    def __repr__(self):
        return '<SearchResponse %s (%s/%s)>' % (self._type,
                                                len(self._resources),
                                                self._total_count)

    def __len__(self):
        return self._total_count

    def __getitem__(self, index):
        if isinstance(index, slice):
            offset = index.start or 0
            limit = (index.stop - offset) if index.stop else 0
            limit = len(self) - offset
            missing = [ index for index in range(offset, offset + limit)
                          if index not in self._resources ]

            if missing:
                req_offset = min(missing)
                req_limit = max(missing) - req_offset + 1
                kw = self._kw.copy()
                kw['offset'] = req_offset
                kw['limit'] = req_limit
                response = self._api._get(self._type, **kw)
                resources = self._api._parse_resources(response['objects'])
                for index, resource in enumerate(resources):
                    self._resources[req_offset + index] = resource

            return [ self._resources[i] for i in range(offset, offset + limit) ]

        else:
            if index >= len(self):
                raise IndexError(index)
            elif index not in self._resources:
                kw = self._kw.copy()
                kw['offset'] = index
                kw['limit'] = 1
                response = self._api._get(self._type, **kw)
                resource = self._api._parse_resource(response['objects'][0])
                self._resources[index] = resource
            return self._resources[index]


class Service(object):
    """Describe a service"""

    def __init__(self, url):
        self.url = url
        self.base_url, self.base_path = self._parse_url(url)

    def _parse_url(self, url):
        """Extracts the base URL and the base path from the service URL
        
        >>> service.parse_url('http://foo.bar/1/')
        ('http://foo.bar', '/1/')
        """
        proto, host, path = urlparse.urlsplit(url)[0:3]
        return '%s://%s' % (proto, host), path

    def is_resource_url(self, obj):
        """Returns True if `obj` is a valid resource URL"""
        return isinstance(obj, basestring) and \
               obj.startswith(self.base_path)

    def parse_resource_url(self, url):
        """Parses a resource URL and returns a tuple of (resource, id)

        `resource` is the resource type, and `id` is the resource id.
        """
        return url.split('/')[-3:-1]


class ListProxy(ResourceListMixin):
    """Acts like a `list` but resolves ResourceProxy objects on access"""

    def __init__(self, list, service, api):
        self._list = list
        self._service = service
        self._api = api

    def __repr__(self):
        return pprint.pformat(self._list)

    def __getitem__(self, index):
        item = self._list[index]
        if isinstance(item, list):
            if item:
                # index is a slice object
                slice = index
                items = map(self._parse_item, item)
                missing = {}
                for index, item in enumerate(items):
                    if isinstance(item, ResourceProxy):
                        if item._resource:
                            items[index] = item._resource
                        else:
                            type = item._type
                            if type not in missing:
                                missing[type] = {}
                            # We assume a list only contains unique IDs
                            # otherwise, we lose the list index of dupplicate
                            # IDs.
                            missing[type][item._id] = index
                for type in missing:
                    ids = missing[type].keys()
                    resources = self._api.many(type, *ids)
                    for id, resource in resources.items():
                        index = missing[type][int(id)]
                        items[index] = resource
                self._list[slice] = items
                return items
            else:
                return []
        else:
            item = self._parse_item(item)
            if isinstance(item, ResourceProxy):
                resource = self._api(proxy=item)
                self._list[index] = resource
                return resource
            else:
                return item

    def _parse_item(self, item):
        if self._service.is_resource_url(item):
            return ResourceProxy(item, self._service, self._api)
        else:
            return item


class Api(object):
    """The TastyPie client"""

    def __init__(self, service_url, serializer=None):
        self._service = Service(service_url)
        self._serializer = JsonSerializer() if serializer is None \
                                    else serializer
        self._endpoints = self._get() # The API endpoint should return 
                                      # resource endpoints list.

    def __repr__(self):
        return '<Api: %s>' % self._service.url

    def __getattr__(self, attr):
        """
        Some magic to enable us to dynamically resolves the endpoints names on
        on the Api object.
        
        For example :
            Api('http://localhost:1337/').poney.find(name__startswith='D')
        Generates an HTTP GET request on this URL :
            http://localhost:1337/poney/?name__startswith=D
        """
        if attr in self._endpoints:
            return EndpointProxy(self, self._endpoints[attr]['list_endpoint'],
                                       self._endpoints[attr]['schema'])
        else:
            raise AttributeError(attr)

    def _get_url(self, resource=None, id=None, **kw):
        """Generate an URL
        
        1. The service URL is used as the base string (eg. "/api/1/")
        2. If a `resource` is given, it is appended (eg. "/api/1/country/")
            2.1. If an `id` is given, it is appended (eg. "/api/1/country/2/")
        3. If keyword arguments are given, construct a query string and append
           it :
           kw = dict(foo=42, bar='test')
           => '/api/1/resource/?foo=42&bar=test
        """
        url = self._service.url
        if resource is not None:
            url += '%s/' % resource
            if id is not None:
                url += '%s/' % id
        if kw:
            for key, value in kw.items():
                if isinstance(value, basestring):
                    kw[key] = value.encode('utf-8')
            url += '?' + urllib.urlencode(kw)
        return url

    def _parse_resource(self, resource):
        """Parses a raw resource as returned by the service, replace related
           resource URLs with ResourceProxy objects.
        """

        url = resource['resource_uri']
        del resource['resource_uri']

        for attr, value in resource.items():
            if self._service.is_resource_url(value):
                resource[attr] = ResourceProxy(value, self._service, self)
            elif isinstance(value, list):
                resource[attr] = ListProxy(value, self._service, self)

        type_, id_ = self._service.parse_resource_url(url)
        return Resource(resource, type_, id_, url)

    def _parse_resources(self, resources):
        return map(self._parse_resource, resources)

    def _get(self, type=None, id=None, **kw):
        """Do a HTTP GET request"""

        url = self._get_url(type, id, **kw)
        response = requests.get(url)
        if response.status_code != 200:
            raise BadHttpStatus(response)
        raw_data = response.content
        data = self._serializer.decode(raw_data)
        return data

    def __call__(self, type=None, id=None, proxy=None, **kw):
        """Get a resource by its ID or a search filter

        Get an entry by its ID ::

            api.entry(42)

        Finds an entry by it's title ::

            api.entry(title='foo!')

        Find an entry by it's name, case insensitive ::

            api.entry(name__iexact='FOO!')
        """

        if proxy:
            if proxy._resource:
                return proxy._resource
            type = proxy._type
            id = proxy._id
        elif type is None:
            raise ResourceTypeMissing

        if id is None:
            if not kw:
                raise ResourceIdMissing
            response = self.find(type, **kw)
            if len(response) != 1:
                raise TooManyResources
            return response[0]
        else:
            response = self._get(type, id, **kw)
            resource = self._parse_resource(response)
            if proxy:
                proxy._resource = resource
            return resource

    def many(self, type, *ids, **kw):
        """Get multiple resources (of the same type) with an unique request

        Returns a list of `Resource` objects.

        Example:
            api.entry.many(17, 41)
        """
        id = 'set/' + ';'.join(map(str, ids))
        response = self._get(type, id, **kw)
        resources = self._parse_resources(response['objects'])
        # Transform a list of Resource in a dict using resource ID as key
        resources = dict([ (r.id, r) for r in resources ])
        # Add not found IDs to the dict
        if 'not_found' in response:
            for id in response['not_found']:
                resources[int(id)] = None
        return resources

    def find(self, type, **kw):
        """Find resources based on a search filter"""
        response = self._get(type, **kw)
        meta = response['meta']
        resources = self._parse_resources(response['objects'])
        return SearchResponse(self, type, meta, resources, kw)
