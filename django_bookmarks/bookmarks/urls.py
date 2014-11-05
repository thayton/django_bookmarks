from django.conf.urls import patterns, url

from bookmarks import views

urlpatterns = patterns('',
    url(r'^$', views.main_page, name='home'),                       
    url(r'^user/(\w+)/$', views.user_page, name='user_page'),
    url(r'^login/$', 'django.contrib.auth.views.login'),
    url(r'^logout/$', views.logout_page, name='logout'),
    url(r'^register/$', views.register_page, name='register'),
)
