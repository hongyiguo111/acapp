from django.http import HttpResponse

def index(request):
    line1 = '<h1 style="text-align: center">术士之战</h1>'
    line3 = '<hr>'
    line4 = '<a href="/play/">进入游戏界面</a>'
    line2 = '<img src="https://bkimg.cdn.bcebos.com/pic/c2cec3fdfc039245efdd58288f94a4c27d1e25a8" width=1800>'
    return HttpResponse(line1 + line4 + line3 + line2)

def play(request):
    line1 = '<h1 style="text-align: center">游戏界面</h1>'
    line3 = '<hr>'
    line4 = '<a href="/">返回主页面</a>'
    line2 = '<img src="https://bkimg.cdn.bcebos.com/pic/4d086e061d950a7bd7da378c0ad162d9f3d3c98f" width=1800>'
    return HttpResponse(line1 + line4 + line3 + line2)
