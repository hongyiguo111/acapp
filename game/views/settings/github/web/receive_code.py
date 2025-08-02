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
    """通过 Cloudflare Worker 处理 GitHub OAuth"""
    try:
        # 1. 获取参数
        code = request.GET.get('code')
        state = request.GET.get('state')

        if not code:
            return HttpResponse("缺少授权码")

        # 2. 验证 state（可选）
        cache_key = f"github_state_{state}"
        if cache.get(cache_key):
            cache.delete(cache_key)

        # 3. 通过 Worker 获取 access_token
        logger.info(f"正在通过 Worker 获取 access_token...")

        token_response = requests.post(
            f"{WORKER_URL}/github/access_token",
            json={
                'client_id': settings.GITHUB_CLIENT_ID,
                'client_secret': settings.GITHUB_CLIENT_SECRET,
                'code': code,
            },
            timeout=30
        )

        if token_response.status_code != 200:
            return HttpResponse(f"Worker 错误: {token_response.status_code}")

        token_data = token_response.json()
        logger.info(f"Token 响应: {token_data}")

        # 检查错误
        if 'error' in token_data:
            return HttpResponse(f"GitHub 错误: {token_data.get('error_description', token_data.get('error'))}")

        access_token = token_data.get('access_token')
        if not access_token:
            return HttpResponse(f"未获取到 access_token: {token_data}")

        # 4. 通过 Worker 获取用户信息
        logger.info("正在通过 Worker 获取用户信息...")

        user_response = requests.post(
            f"{WORKER_URL}/github/user",
            json={'access_token': access_token},
            timeout=30
        )

        if user_response.status_code != 200:
            return HttpResponse(f"获取用户信息失败: {user_response.status_code}")

        user_data = user_response.json()
        logger.info(f"用户数据: {user_data.get('login')}")

        # 5. 处理用户登录/注册
        github_id = str(user_data.get('id'))
        github_username = user_data.get('login')
        github_avatar = user_data.get('avatar_url')

        if not github_id:
            return HttpResponse("无法获取 GitHub 用户 ID")

        # 查找或创建用户
        players = Player.objects.filter(github_id=github_id)

        if players.exists():
            # 老用户登录
            player = players.first()
            login(request, player.user)
            logger.info(f"用户 {github_username} 登录成功")
        else:
            # 新用户注册
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