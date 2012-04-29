Tastypie-client is a client API for `Django <https://www.djangoproject.com/>`_-`Tastypie <http://tastypieapi.org/>`_ `REST <http://en.wikipedia.org/wiki/REST>`_ services.

Quick start
-----------

These examples work on the `tastypie_tutorial <https://github.com/pmuller/tastypie-client/tree/master/examples/tastypie_tutorial>`_ Django project.

Create an ``Api`` object ::

    >>> from tastypie_client import Api
    >>> api = Api('http://127.0.0.1:8000/api/1/')
    >>> api
    <Api: http://127.0.0.1:8000/api/1/>

Finds an user by its ID ::

    >>> api.user
    <EndpointProxy http://127.0.0.1:8000/api/1/user/>
    >>> user = api.user(1)
    >>> user
    <Resource user/1: {u'username': u'test_user', ...}>
    >>> user.username
    u'test_user'

Look at its posts ::

    >>> user.posts
    [u'/api/1/entry/1/', u'/api/1/entry/2/']

Get the first one ::

    >>> user.posts[0]
    Resource entry/1: {u'body': u'foo body', u'title': u'foo!', u'id': u'1', u'user': <ResourceProxy user/1>, u'pub_date': u'2012-04-29T08:55:08', u'slug': u'foo'}>

Alternatively, you load both of them with an unique HTTP request ::

    >>> user.posts[:]
    [<Resource entry/1: {u'body': u'foo body', u'title': u'foo!', u'id': u'1', u'user': <ResourceProxy user/1>, u'pub_date': u'2012-04-29T08:55:08', u'slug': u'foo'}>,
     <Resource entry/2: {u'body': u'bar body', u'title': u'bar title', u'id': u'2', u'user': <ResourceProxy user/1>, u'pub_date': u'2012-04-29T08:55:21', u'slug': u'bar'}>]
