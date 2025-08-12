from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
import json


@require_POST
@login_required
def update_username(request):
    """更新用户名"""
    try:
        data = json.loads(request.body)
        new_username = data.get('username', '').strip()

        if not new_username:
            return JsonResponse({
                'result': 'error',
                'message': '用户名不能为空'
            })

        if len(new_username) < 3 or len(new_username) > 20:
            return JsonResponse({
                'result': 'error',
                'message': '用户名长度应在3-20个字符之间'
            })

        # 检查用户名是否已被占用
        if new_username != request.user.username:
            if User.objects.filter(username=new_username).exists():
                return JsonResponse({
                    'result': 'error',
                    'message': '用户名已被使用'
                })

        # 更新用户名
        user = request.user
        user.username = new_username
        user.save()

        return JsonResponse({
            'result': 'success',
            'message': '用户名更新成功',
            'username': new_username
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