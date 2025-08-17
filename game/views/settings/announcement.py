from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from game.models.announcement.announcement import Announcement
import json


def get_announcements(request):
    """获取所有活动公告（所有用户可访问）"""
    try:
        announcements = Announcement.objects.filter(is_active=True)[:5]  # 最多显示5条

        data = []
        for ann in announcements:
            data.append({
                'id': ann.id,
                'title': ann.title,
                'content': ann.content,
                'updated_at': ann.updated_at.strftime('%m-%d %H:%M')
            })

        # 如果是管理员，返回额外的编辑权限标记
        is_admin = request.user.is_authenticated and request.user.username == 'admin'

        return JsonResponse({
            'result': 'success',
            'announcements': data,
            'is_admin': is_admin
        })
    except Exception as e:
        return JsonResponse({
            'result': 'error',
            'message': str(e)
        })


@login_required
@require_POST
def update_announcement(request):
    """更新公告（仅管理员）"""
    try:
        # 权限检查
        if request.user.username != 'admin':
            return JsonResponse({
                'result': 'error',
                'message': '权限不足'
            })

        data = json.loads(request.body)

        # 获取或创建第一条公告
        announcement, created = Announcement.objects.get_or_create(
            id=1,  # 固定使用ID=1的公告
            defaults={
                'title': '系统公告',
                'content': '暂无公告'
            }
        )

        # 更新内容
        announcement.title = data.get('title', '系统公告')[:100]  # 限制长度
        announcement.content = data.get('content', '')[:500]  # 限制长度
        announcement.is_active = data.get('is_active', True)
        announcement.save()

        return JsonResponse({
            'result': 'success',
            'message': '公告已更新'
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'result': 'error',
            'message': '无效的数据格式'
        })
    except Exception as e:
        return JsonResponse({
            'result': 'error',
            'message': str(e)
        })