from django.conf.urls import patterns, url
from django.views.generic import TemplateView

from bookmarks import views
from bookmarks.feeds import RecentBookmarks, UserBookmarks

urlpatterns = patterns('',
    # Session Management
    url(r'^login/$', 'django.contrib.auth.views.login'),
    url(r'^logout/$', views.logout_page, name='logout'),
    url(r'^register/$', views.register_page, name='register'),
    url(r'^register/success/$', 
        TemplateView.as_view(
            template_name="registration/register_success.html"
        ),
        name='register_success'),

    # Feeds
    url(r'^feeds/recent/$', RecentBookmarks()),
    url(r'^feeds/user/(?P<username>\w+)/$', UserBookmarks()),

    # Invitations
    url(r'^invite/$', views.friend_invite, name='invite_friend'),
    url(r'^invite/accept/(\w+)/$', views.accept_invite, name='accept_invite'),

    # Browsing
    url(r'^$', views.main_page, name='home'),  
    url(r'^popular/$', views.popular_page, name='popular_bookmarks'),
    url(r'^user/(\w+)/$', views.user_page, name='user_page'),
    url(r'^tag/$', views.tag_cloud_page, name='tag_cloud_page'),
    url(r'^tag/([^\s]+)/$', views.tag_page, name='tag_page'),
    url(r'^search/$', views.search_page, name='search_page'),
  
    # Account management
    url(r'^save/$', views.bookmark_save_page, name='save_bookmark'),                       
    url(r'^vote/$', views.bookmark_vote_page, name='vote_bookmark'),                       

    # Followers/Followed
    url(r'^follow/(\w+)/$', views.follow_user, name='follow_user'),
    url(r'^unfollow/(\w+)/$', views.unfollow_user, name='unfollow_user'),
    url(r'^(\w+)/following/$', views.following_page, name='following'),
    url(r'^(\w+)/followers/$', views.followers_page, name='followers'),

    # Ajax
    url(r'^ajax/tag/autocomplete/$', views.ajax_tag_autocomplete, name='tag_autocomplete'),
)
