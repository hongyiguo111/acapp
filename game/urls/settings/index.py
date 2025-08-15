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
from game.views.settings.admin_messages import (
    send_admin_message,
    get_admin_messages,
    reply_admin_message,
    get_unread_count,
    admin_reply_quick,
    mark_messages_read
)

from game.views.settings.admin_message_panel import admin_message_panel

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
    # 管理员私信相关路由
    path('send_admin_message/', send_admin_message, name='settings_send_admin_message'),
    path('get_admin_messages/', get_admin_messages, name='settings_get_admin_messages'),
    path('reply_admin_message/', reply_admin_message, name='settings_reply_admin_message'),
    path('get_unread_count/', get_unread_count, name='settings_get_unread_count'),
    path('admin_panel/', admin_message_panel, name='settings_admin_panel'),
    path('admin_reply_quick/', admin_reply_quick, name='settings_admin_reply_quick'),
    path('mark_messages_read/', mark_messages_read, name='settings_mark_messages_read'),
]

