from django.urls import path, include
from game.views.settings.getinfo import getinfo
from game.views.settings.login import signin
from game.views.settings.logout import signout
from game.views.settings.register import register
from game.views.settings.ranklist import get_ranklist

urlpatterns = [
        path('getinfo/', getinfo, name='settings_getinfo'),
        path('login/', signin, name='settings_login'),
        path('logout/', signout, name='settings_logout'),
        path('register/', register, name='settings_register'),
        path("acwing/", include("game.urls.settings.acwing.index")),
        path("github/", include("game.urls.settings.github.index")),
        path("gitee/", include("game.urls.settings.gitee.index")),
        path('ranklist/', get_ranklist, name='settings_ranklist'),
]
