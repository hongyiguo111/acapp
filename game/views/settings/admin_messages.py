from django.http import JsonResponse
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from game.models.player.player import Player
from game.models.admin_message.admin_message import AdminMessage
from django.utils import timezone
from django.utils.timezone import localtime
import json


@login_required
@require_POST
def send_admin_message(request):
    """发送私信给管理员"""
    try:
        data = json.loads(request.body)
        message = data.get('message', '').strip()

        if not message:
            return JsonResponse({
                'result': 'error',
                'message': '消息内容不能为空'
            })

        if len(message) > 1000:
            return JsonResponse({
                'result': 'error',
                'message': '消息长度不能超过1000个字符'
            })

        player = Player.objects.get(user=request.user)

        # 创建消息
        admin_msg = AdminMessage.objects.create(
            sender=player,
            message=message
        )

        # 使用localtime转换为本地时间（北京时间）
        local_timestamp = localtime(admin_msg.timestamp)

        return JsonResponse({
            'result': 'success',
            'message': '消息已发送',
            'msg_id': admin_msg.id,
            'timestamp': local_timestamp.strftime('%Y-%m-%d %H:%M:%S')
        })

    except Player.DoesNotExist:
        return JsonResponse({
            'result': 'error',
            'message': '用户信息不存在'
        })
    except Exception as e:
        return JsonResponse({
            'result': 'error',
            'message': str(e)
        })


@login_required
def get_admin_messages(request):
    """获取与管理员的历史私信"""
    try:
        player = Player.objects.get(user=request.user)

        # 获取所有相关消息
        messages = AdminMessage.objects.filter(sender=player).order_by('timestamp')

        # 标记所有回复为已读（如果你添加了reply_read字段）
        # messages.filter(reply__isnull=False, reply_read=False).update(reply_read=True)

        message_list = []
        for msg in messages:
            # 转换为本地时间
            local_timestamp = localtime(msg.timestamp)

            message_data = {
                'id': msg.id,
                'message': msg.message,
                'timestamp': local_timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'is_read': msg.is_read,
                'type': 'sent'
            }

            # 如果有回复，也转换回复时间
            if msg.reply:
                message_data['reply'] = msg.reply
                if msg.reply_timestamp:
                    local_reply_timestamp = localtime(msg.reply_timestamp)
                    message_data['reply_timestamp'] = local_reply_timestamp.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    message_data['reply_timestamp'] = None

            message_list.append(message_data)

        return JsonResponse({
            'result': 'success',
            'messages': message_list
        })

    except Player.DoesNotExist:
        return JsonResponse({
            'result': 'error',
            'message': '用户信息不存在'
        })
    except Exception as e:
        return JsonResponse({
            'result': 'error',
            'message': str(e)
        })

@login_required
@require_POST
def reply_admin_message(request):
    """管理员回复消息（仅admin可用）"""
    try:
        # 检查是否是管理员
        if request.user.username != 'admin':
            return JsonResponse({
                'result': 'error',
                'message': '权限不足'
            })

        data = json.loads(request.body)
        message_id = data.get('message_id')
        reply = data.get('reply', '').strip()

        if not reply:
            return JsonResponse({
                'result': 'error',
                'message': '回复内容不能为空'
            })

        # 更新消息
        admin_msg = AdminMessage.objects.get(id=message_id)
        admin_msg.reply = reply
        admin_msg.reply_timestamp = timezone.now()  # 这里Django会自动处理时区
        admin_msg.is_read = True
        admin_msg.save()

        return JsonResponse({
            'result': 'success',
            'message': '回复成功'
        })

    except AdminMessage.DoesNotExist:
        return JsonResponse({
            'result': 'error',
            'message': '消息不存在'
        })
    except Exception as e:
        return JsonResponse({
            'result': 'error',
            'message': str(e)
        })


@login_required
def get_unread_count(request):
    """获取未读私信数量"""
    try:
        if request.user.username == 'admin':
            # 管理员看到所有未读消息
            count = AdminMessage.objects.filter(is_read=False).count()
        else:
            # 普通用户获取自己未查看的回复数量
            player = Player.objects.get(user=request.user)
            count = AdminMessage.objects.filter(
                sender=player,
                reply__isnull=False,  # 有回复
                reply_read=False  # 用户未读回复
            ).count()

        return JsonResponse({
            'result': 'success',
            'count': count
        })

    except Exception as e:
        return JsonResponse({
            'result': 'error',
            'message': str(e)
        })


@login_required
@require_POST
def admin_reply_quick(request):
    """管理员快速回复（用于管理面板）"""
    try:
        if request.user.username != 'admin':
            return redirect('index')

        message_id = request.POST.get('message_id')
        reply = request.POST.get('reply', '').strip()

        if not reply:
            return redirect('/settings/admin_panel/')

        admin_msg = AdminMessage.objects.get(id=message_id)
        admin_msg.reply = reply
        admin_msg.reply_timestamp = timezone.now()
        admin_msg.is_read = True
        admin_msg.save()

        return redirect('/settings/admin_panel/')

    except Exception as e:
        return redirect('/settings/admin_panel/')


@login_required
@require_POST
def mark_messages_read(request):
    """批量标记消息为已读"""
    try:
        if request.user.username != 'admin':
            return JsonResponse({
                'result': 'error',
                'message': '权限不足'
            })

        data = json.loads(request.body)
        message_ids = data.get('message_ids', [])

        AdminMessage.objects.filter(id__in=message_ids).update(is_read=True)

        return JsonResponse({
            'result': 'success',
            'count': len(message_ids)
        })

    except Exception as e:
        return JsonResponse({
            'result': 'error',
            'message': str(e)
        })