from django.contrib.auth.models import User
from django.db import models
from django.template.defaultfilters import slugify


class Entry(models.Model):
    user = models.ForeignKey(User, related_name='posts')
    pub_date = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=200)
    slug = models.SlugField()
    body = models.TextField()

    def __unicode__(self):
        return self.title

    def save(self, *args, **kwargs):
        # For automatic slug generation.
        if not self.slug:
            self.slug = slugify(self.title)[:50]

        return super(Entry, self).save(*args, **kwargs)
