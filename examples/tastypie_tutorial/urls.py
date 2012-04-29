from django.conf.urls.defaults import patterns, include

from django.contrib import admin
admin.autodiscover()

from tastypie.api import Api
from tutorial.api import EntryResource, UserResource

api = Api(api_name='1')
api.register(EntryResource())
api.register(UserResource())

urlpatterns = patterns('',
    (r'^api/', include(api.urls)),
    (r'^admin/', include(admin.site.urls)),
)
