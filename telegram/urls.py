from django.conf.urls import url

from . import views
from . import send_views
from . import user_views

urlpatterns = [
    url(r'^$', views.hello_world, name='Hello World'),
    url(r'^send/text$', send_views.send_text, name='Sending text message'),
    url(r'^send/media$', send_views.send_media, name='Sending media message'),
    url(r'^status/read$', send_views.status_read, name='Status Read message'),
    url(r'^user/request_code$', user_views.request_code, name='User Request Code'),
    url(r'^user/sign_in$', user_views.sign_in, name='User Sign In'),
    url(r'^user/sign_up$', user_views.sign_up, name='User Sign Up'),
    url(r'^user/logout$', user_views.log_out, name='User Log Out'),
    url(r'^user/status$', user_views.set_presence, name='User Set Presence'),
]