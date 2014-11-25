from django.core.exceptions import ObjectDoesNotExist
from django.contrib.syndication.views import Feed
from django.contrib.auth.models import User
from bookmarks.models import Bookmark

class RecentBookmarks(Feed):
    title = 'Django Bookmarks | Recent Bookmarks'
    link = '/feeds/recent/'
    description = 'Recent bookmarks posted to Django Bookmarks'
    
    title_template = 'feeds/recent_title.html'
    description_template = 'feeds/recent_description.html'

    def items(self):
        return Bookmark.objects.order_by('-id')[:10]

class UserBookmarks(Feed):
    title_template = 'feeds/user_title.html'
    description_template = 'feeds/user_description.html'

    def get_object(self, request, username):
        return User.objects.get(username=username)

    def title(self, user):
        return ('Django Bookmarks | Bookmarks for %s' % user.username)

    def link(self, user):
        return '/feeds/user/%s/' % user.username

    def description(self, user):
        return 'Recent bookmarks posted by %s' % user.username

    def items(self, user):
        return user.bookmarks.order_by('-id')[:10]
