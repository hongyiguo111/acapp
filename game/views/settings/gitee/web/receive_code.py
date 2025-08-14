# views/settings/gitee/web/receive_code.py
from django.shortcuts import redirect
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.conf import settings
from django.core.cache import cache
from game.models.player.player import Player
import requests
import logging

logger = logging.getLogger(__name__)


def receive_code(request):
    """处理 Gitee OAuth 回调"""
    try:
        # 1. 获取参数
        code = request.GET.get('code')
        state = request.GET.get('state')

        if not code or not state:
            logger.warning("Gitee OAuth: 缺少 code 或 state")
            return redirect("index")

        # 2. 验证 state
        cache_key = f"gitee_state_{state}"
        if not cache.get(cache_key):
            logger.warning("Gitee OAuth: state 验证失败")
            return redirect("index")
        cache.delete(cache_key)

        # 3. 获取 access_token
        token_url = "https://gitee.com/oauth/token"
        token_params = {
            'grant_type': 'authorization_code',
            'code': code,
            'client_id': settings.GITEE_CLIENT_ID,
            'client_secret': settings.GITEE_CLIENT_SECRET,
            'redirect_uri': "https://app7562.acapp.acwing.com.cn/settings/gitee/web/receive_code/",
        }

        token_response = requests.post(token_url, data=token_params, timeout=10)
        token_data = token_response.json()

        if 'error' in token_data:
            logger.error(f"Gitee OAuth: {token_data.get('error_description', 'Unknown error')}")
            return redirect("index")

        access_token = token_data.get('access_token')
        if not access_token:
            logger.error("Gitee OAuth: 未获取到 access_token")
            return redirect("index")

        # 4. 获取用户信息
        user_url = f"https://gitee.com/api/v5/user?access_token={access_token}"
        user_response = requests.get(user_url, timeout=10)
        user_data = user_response.json()

        # 5. 处理用户数据
        gitee_id = str(user_data.get('id'))
        gitee_username = user_data.get('login')
        gitee_avatar = user_data.get('avatar_url')
        gitee_name = user_data.get('name', gitee_username)

        if not gitee_id:
            logger.error("Gitee OAuth: 未获取到用户 ID")
            return redirect("index")

        # 6. 查找或创建用户
        players = Player.objects.filter(gitee_id=gitee_id)

        if players.exists():
            # 老用户登录
            player = players.first()
            login(request, player.user)
            logger.info(f"Gitee 用户 {gitee_username} 登录成功")
        else:
            # 新用户注册
            username = f"gitee_{gitee_username}"
            counter = 0
            while User.objects.filter(username=username).exists():
                counter += 1
                username = f"gitee_{gitee_username}_{counter}"

            # 创建 Django 用户
            user = User.objects.create_user(username=username)
            user.set_unusable_password()
            user.save()

            # 创建 Player
            player = Player.objects.create(
                user=user,
                photo=gitee_avatar or "",
                gitee_id=gitee_id,
                gitee_username=gitee_username
            )

            login(request, user)
            logger.info(f"新 Gitee 用户 {gitee_username} 注册并登录")

        return redirect("index")

    except requests.exceptions.RequestException as e:
        logger.error(f"Gitee OAuth 网络请求失败: {e}")
        return redirect("index")
    except Exception as e:
        logger.error(f"Gitee OAuth 未知错误: {e}")
        return redirect("index")