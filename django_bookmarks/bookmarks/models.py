from django.core.mail import send_mail
from django.template.loader import get_template
from django.template import Context
from django.conf import settings
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

    def get_absolute_url(self):
        return self.link.url

class Tag(models.Model):
    name = models.CharField(max_length=64, unique=True)
    bookmarks = models.ManyToManyField(Bookmark, related_name='tags')

    def __str__(self):
        return self.name

class SharedBookmark(models.Model):
    bookmark = models.ForeignKey(Bookmark, unique=True)
    date = models.DateTimeField(auto_now_add=True)
    votes = models.IntegerField(default=1)
    users_voted = models.ManyToManyField(User)

    def __str__(self):
        return '%s, %d' % (self.bookmark, self.votes)    

class Follow(models.Model):
    '''
    User1 following the updates of User2 creates the following relationship:

    User1(follower) -> User2(followed)

    User1.following : list of users User1 follows
    User1.followers : list of users following User1
    '''
    follower = models.ForeignKey(User, related_name='following')
    followed = models.ForeignKey(User, related_name='followers')

    def __str__(self):
        return '%s, %s' % (self.follower.username, self.followed.username)

    class Meta:
        unique_together = (('follower', 'followed'),)

class Invitation(models.Model):
    name = models.CharField(max_length=50)
    email = models.EmailField()
    code = models.CharField(max_length=20)
    sender = models.ForeignKey(User)

    def __str__(self):
        return '%s, %s' % (self.sender.username, self.email)

    def send(self):
        subject = 'Invitation to join Django Bookmarks'
        link = 'http://127.0.0.1:8000/invite/accept/%s/' % self.code
        template = get_template('invitation_email.txt')
        context = Context({
                'name': self.name,
                'link': link,
                'sender': self.sender.username,
        })
        message = template.render(context)
        send_mail(
            subject, message,
            settings.DEFAULT_FROM_EMAIL, [self.email]
        )
