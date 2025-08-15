from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from game.models.admin_message.admin_message import AdminMessage
from django.core.paginator import Paginator


@login_required
def admin_message_panel(request):
    """管理员消息管理面板"""
    # 检查是否是管理员
    if request.user.username != 'admin':
        return redirect('index')

    # 获取所有消息
    messages = AdminMessage.objects.all().order_by('-timestamp')

    # 分页
    paginator = Paginator(messages, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'messages': page_obj,
        'unread_count': AdminMessage.objects.filter(is_read=False).count()
    }

    return render(request, 'admin_message_panel.html', context)