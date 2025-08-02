from django.http import JsonResponse
from urllib.parse import quote
from django.core.cache import cache
from django.conf import settings
import secrets


def apply_code(request):
    """申请 Gitee 授权码"""
    # Gitee OAuth 参数
    client_id = settings.GITEE_CLIENT_ID
    redirect_uri = quote("https://app7549.acapp.acwing.com.cn/settings/gitee/web/receive_code/")
    state = secrets.token_urlsafe(32)

    # 保存 state 到缓存
    cache.set(f"gitee_state_{state}", True, 600)  # 10分钟有效

    # Gitee 的授权地址
    authorize_url = "https://gitee.com/oauth/authorize"

    return JsonResponse({
        'result': "success",
        'apply_code_url': f"{authorize_url}?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&state={state}"
    })