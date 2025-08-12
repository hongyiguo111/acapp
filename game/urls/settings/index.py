from django.urls import path, include
from game.views.settings.getinfo import getinfo
from game.views.settings.login import signin
from game.views.settings.logout import signout
from game.views.settings.register import register
from game.views.settings.ranklist import get_ranklist
from game.views.settings.get_user_settings import get_user_settings
from game.views.settings.check_username import check_username
from game.views.settings.update_username import update_username
from game.views.settings.update_password import update_password
from game.views.settings.upload_avatar import upload_avatar

urlpatterns = [
    path('getinfo/', getinfo, name='settings_getinfo'),
    path('login/', signin, name='settings_login'),
    path('logout/', signout, name='settings_logout'),
    path('register/', register, name='settings_register'),
    path("acwing/", include("game.urls.settings.acwing.index")),
    path("github/", include("game.urls.settings.github.index")),
    path("gitee/", include("game.urls.settings.gitee.index")),
    path('ranklist/', get_ranklist, name='settings_ranklist'),
    path('get_user_settings/', get_user_settings, name='settings_get_user'),
    path('check_username/', check_username, name='settings_check_username'),
    path('update_username/', update_username, name='settings_update_username'),
    path('update_password/', update_password, name='settings_update_password'),
    path('upload_avatar/', upload_avatar, name='settings_upload_avatar'),
]
