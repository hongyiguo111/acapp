from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.views.decorators.http import require_POST
from game.models.player.player import Player
import json


@require_POST
@login_required
def update_password(request):
    """更新密码（仅限本地注册用户）"""
    try:
        # 检查是否是本地注册用户
        player = Player.objects.get(user=request.user)
        if player.openid or player.github_id or player.gitee_id:
            return JsonResponse({
                'result': 'error',
                'message': '第三方登录用户不能修改密码'
            })

        data = json.loads(request.body)
        old_password = data.get('old_password', '')
        new_password = data.get('new_password', '')
        confirm_password = data.get('confirm_password', '')

        # 验证参数
        if not all([old_password, new_password, confirm_password]):
            return JsonResponse({
                'result': 'error',
                'message': '请填写所有密码字段'
            })

        # 验证旧密码
        if not request.user.check_password(old_password):
            return JsonResponse({
                'result': 'error',
                'message': '当前密码不正确'
            })

        # 验证新密码
        if new_password != confirm_password:
            return JsonResponse({
                'result': 'error',
                'message': '两次输入的新密码不一致'
            })

        if len(new_password) < 6:
            return JsonResponse({
                'result': 'error',
                'message': '密码长度至少为6个字符'
            })

        # 更新密码
        user = request.user
        user.set_password(new_password)
        user.save()

        # 更新session，避免用户被登出
        update_session_auth_hash(request, user)

        return JsonResponse({
            'result': 'success',
            'message': '密码更新成功'
        })

    except Player.DoesNotExist:
        return JsonResponse({
            'result': 'error',
            'message': '用户信息不存在'
        })
    except json.JSONDecodeError:
        return JsonResponse({
            'result': 'error',
            'message': '无效的请求数据'
        })
    except Exception as e:
        return JsonResponse({
            'result': 'error',
            'message': str(e)
        })