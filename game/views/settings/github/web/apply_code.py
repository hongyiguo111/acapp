# views/settings/github/web/apply_code.py
from django.http import JsonResponse
from urllib.parse import quote
from django.core.cache import cache
from django.conf import settings
import secrets


def get_state():
    """生成安全的随机状态码"""
    return secrets.token_urlsafe(32)


def apply_code(request):
    # GitHub OAuth 参数
    client_id = settings.GITHUB_CLIENT_ID  # 从配置读取，不要硬编码！
    redirect_uri = quote(settings.GITHUB_REDIRECT_URI)
    scope = "user"  # GitHub 的权限范围
    state = get_state()

    # 保存 state 到缓存
    cache.set(f"github_state_{state}", True, 600)  # 10分钟有效

    # GitHub 的授权地址
    authorize_url = "https://github.com/login/oauth/authorize"

    return JsonResponse({
        'result': "success",
        'apply_code_url': f"{authorize_url}?client_id={client_id}&redirect_uri={redirect_uri}&scope={scope}&state={state}"
    })