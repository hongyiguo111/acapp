from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from game.models.player.player import Player


@login_required
def get_user_settings(request):
    """获取用户的设置信息"""
    try:
        user = request.user
        player = Player.objects.get(user=user)

        # 判断用户的注册方式
        auth_type = "local"  # 默认本地注册
        if player.openid:
            auth_type = "acwing"
        elif player.github_id:
            auth_type = "github"
        elif player.gitee_id:
            auth_type = "gitee"

        return JsonResponse({
            'result': 'success',
            'username': user.username,
            'photo': player.photo,
            'auth_type': auth_type,
            'can_change_password': auth_type == "local",  # 只有本地用户可以改密码
            'score': player.score,
        })
    except Exception as e:
        return JsonResponse({
            'result': 'error',
            'message': str(e)
        })