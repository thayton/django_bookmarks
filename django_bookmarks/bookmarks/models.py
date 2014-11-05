from django.db import models
from django.contrib.auth.models import User

class Link(models.Model):
    url = models.URLField(unique=True)

    def __str__(self):
        return self.url

class Bookmark(models.Model):
    title = models.CharField(max_length=200)
    user = models.ForeignKey(User, related_name='bookmarks')
    link = models.ForeignKey(Link, related_name='bookmarks')

    def __str__(self):
        return '%s %s %s' % (self.user.username, self.title, self.link)
