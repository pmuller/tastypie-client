from tastypie.resources import ModelResource
from models import Entry
from django.contrib.auth.models import User
from tastypie.constants import ALL, ALL_WITH_RELATIONS
from tastypie import fields


class UserResource(ModelResource):
    posts = fields.ToManyField('tastypie_tutorial.tutorial.api.EntryResource', 'posts')
    class Meta:
        queryset = User.objects.all()
        resource_name = 'user'
        filtering = {'slug': ALL, 'title': ALL, 'body': ALL}


class EntryResource(ModelResource):
    user = fields.ForeignKey(UserResource, 'user')
    class Meta:
        queryset = Entry.objects.all()
        resource_name = 'entry'
        filtering = {'slug': ALL, 'title': ALL, 'body': ALL,
                     'user': ALL_WITH_RELATIONS,}
