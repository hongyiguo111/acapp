from django.shortcuts import redirect
from django.core.cache import cache
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.conf import settings
from game.models.player.player import Player
import requests
import logging

logger = logging.getLogger(__name__)


def receive_code(request):
    """处理 GitHub OAuth 回调"""

    # 1. 获取参数
    code = request.GET.get('code')
    state = request.GET.get('state')

    # 2. 验证参数
    if not code or not state:
        logger.warning("GitHub OAuth: 缺少 code 或 state 参数")
        return redirect("index")

    # 3. 验证 state（防 CSRF）
    cache_key = f"github_state_{state}"
    if not cache.get(cache_key):
        logger.warning("GitHub OAuth: state 验证失败")
        return redirect("index")

    # 删除已使用的 state
    cache.delete(cache_key)

    try:
        # 4. 用 code 换取 access_token
        token_url = "https://github.com/login/oauth/access_token"
        token_params = {
            'client_id': settings.GITHUB_CLIENT_ID,
            'client_secret': settings.GITHUB_CLIENT_SECRET,
            'code': code,
        }

        # GitHub 需要特殊的 Accept header
        headers = {
            'Accept': 'application/json'
        }

        token_response = requests.post(
            token_url,
            data=token_params,
            headers=headers,
            timeout=10
        )
        token_data = token_response.json()

        # 检查是否有错误
        if 'error' in token_data:
            logger.error(f"GitHub OAuth: {token_data.get('error_description', 'Unknown error')}")
            return redirect("index")

        access_token = token_data.get('access_token')
        if not access_token:
            logger.error("GitHub OAuth: 未获取到 access_token")
            return redirect("index")

        # 5. 使用 access_token 获取用户信息
        user_url = "https://api.github.com/user"
        user_headers = {
            'Authorization': f'token {access_token}',
            'Accept': 'application/json'
        }

        user_response = requests.get(
            user_url,
            headers=user_headers,
            timeout=10
        )
        user_data = user_response.json()

        # 6. 处理用户数据
        github_id = str(user_data.get('id'))  # GitHub 用户 ID
        github_username = user_data.get('login')  # GitHub 用户名
        github_avatar = user_data.get('avatar_url')  # 头像

        if not github_id:
            logger.error("GitHub OAuth: 未获取到用户 ID")
            return redirect("index")

        # 7. 查找或创建用户
        players = Player.objects.filter(github_id=github_id)

        if players.exists():
            # 老用户，直接登录
            player = players.first()
            login(request, player.user)
            logger.info(f"GitHub 用户 {github_username} 登录成功")
        else:
            # 新用户，创建账号
            # 生成唯一的用户名
            username = f"github_{github_username}"
            counter = 0
            while User.objects.filter(username=username).exists():
                counter += 1
                username = f"github_{github_username}_{counter}"

            # 创建 Django 用户
            user = User.objects.create_user(username=username)
            user.set_unusable_password()  # OAuth 用户不设密码
            user.save()

            # 创建 Player
            player = Player.objects.create(
                user=user,
                photo=github_avatar or "",
                github_id=github_id,
                github_username=github_username
            )

            login(request, user)
            logger.info(f"新 GitHub 用户 {github_username} 注册并登录")

        return redirect("index")

    except requests.RequestException as e:
        logger.error(f"GitHub OAuth 网络请求失败: {e}")
        return redirect("index")
    except Exception as e:
        logger.error(f"GitHub OAuth 未知错误: {e}")
        return redirect("index")

