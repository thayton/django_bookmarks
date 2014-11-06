from django.conf.urls import patterns, url
from django.views.generic import TemplateView

from bookmarks import views

urlpatterns = patterns('',
    # Browsing
    url(r'^$', views.main_page, name='home'),                       
    url(r'^user/(\w+)/$', views.user_page, name='user_page'),
    url(r'^tag/$', views.tag_cloud_page, name='tag_cloud_page'),
    url(r'^tag/([^\s]+)/$', views.tag_page, name='tag_page'),
  
    # Session Management
    url(r'^login/$', 'django.contrib.auth.views.login'),
    url(r'^logout/$', views.logout_page, name='logout'),
    url(r'^register/$', views.register_page, name='register'),
    url(r'^register/success/$', 
        TemplateView.as_view(
            template_name="registration/register_success.html"
        ),
        name='register_success'),

    # Account management
    url(r'^save/$', views.bookmark_save_page, name='save_bookmark'),                       
)
