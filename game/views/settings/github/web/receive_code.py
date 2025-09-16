# views/settings/github/web/receive_code.py
from django.shortcuts import redirect
from django.http import HttpResponse
from django.core.cache import cache
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.conf import settings
from game.models.player.player import Player
import requests
import logging
import json

logger = logging.getLogger(__name__)

# 你的 Cloudflare Worker URL
WORKER_URL = "https://github-oauth-proxy.eg372933.workers.dev"


def receive_code(request):
    """直接调用GitHub API，不使用Worker"""
    try:
        # 1. 获取参数
        code = request.GET.get('code')
        state = request.GET.get('state')

        if not code:
            return HttpResponse("缺少授权码")

        # 2. 验证state
        cache_key = f"github_state_{state}"
        if cache.get(cache_key):
            cache.delete(cache_key)

        # 3. 直接获取access_token（不用Worker）
        logger.info("正在获取access_token...")

        token_data = {
            'client_id': settings.GITHUB_CLIENT_ID,
            'client_secret': settings.GITHUB_CLIENT_SECRET,
            'code': code,
        }

        token_response = requests.post(
            'https://github.com/login/oauth/access_token',
            data=token_data,
            headers={'Accept': 'application/json'},
            timeout=30
        )

        if token_response.status_code != 200:
            return HttpResponse(f"GitHub错误: {token_response.status_code}")

        token_result = token_response.json()
        logger.info(f"Token响应: {token_result}")

        if 'error' in token_result:
            return HttpResponse(f"GitHub错误: {token_result.get('error_description', token_result.get('error'))}")

        access_token = token_result.get('access_token')
        if not access_token:
            return HttpResponse(f"未获取到access_token: {token_result}")

        # 4. 直接获取用户信息
        logger.info("正在获取用户信息...")

        user_response = requests.get(
            'https://api.github.com/user',
            headers={
                'Authorization': f'token {access_token}',
                'User-Agent': 'Django-OAuth-App'
            },
            timeout=30
        )

        if user_response.status_code != 200:
            return HttpResponse(f"获取用户信息失败: {user_response.status_code}")

        user_data = user_response.json()
        logger.info(f"用户数据: {user_data.get('login')}")

        # 5. 后续处理用户登录/注册的代码保持不变
        github_id = str(user_data.get('id'))
        github_username = user_data.get('login')
        github_avatar = user_data.get('avatar_url')

        if not github_id:
            return HttpResponse("无法获取GitHub用户ID")

        # 查找或创建用户
        players = Player.objects.filter(github_id=github_id)

        if players.exists():
            player = players.first()
            login(request, player.user)
            logger.info(f"用户 {github_username} 登录成功")
        else:
            username = f"github_{github_username}"
            counter = 0
            while User.objects.filter(username=username).exists():
                counter += 1
                username = f"github_{github_username}_{counter}"

            user = User.objects.create_user(username=username)
            user.set_unusable_password()
            user.save()

            player = Player.objects.create(
                user=user,
                photo=github_avatar or "",
                github_id=github_id,
                github_username=github_username
            )

            login(request, user)
            logger.info(f"新用户 {github_username} 注册并登录")

        return redirect("index")

    except requests.exceptions.Timeout:
        return HttpResponse("请求超时，请重试")
    except Exception as e:
        logger.error(f"错误: {e}")
        return HttpResponse(f"错误: {str(e)}")