from django.urls import path
from game.views.settings.github.web.apply_code import apply_code
from game.views.settings.github.web.receive_code import receive_code
from game.views.settings.github.web.test_worker import test_worker

urlpatterns = [
    path("web/apply_code/", apply_code, name="settings_github_web_apply_code"),
    path("web/receive_code/", receive_code, name="settings_github_web_receive_code"),
    path("web/test_worker/", test_worker),  # 新增测试路由
]