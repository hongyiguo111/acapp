`项目地址: `

* [acgit](https://git.acwing.com/HongyiGuo/acapp)
* [github](https://github.com/hongyiguo111/acapp)

[游戏网址](https://app7562.acapp.acwing.com.cn/)

[Acapp下载地址](https://www.acwing.com/file_system/file/content/whole/index/content/13650477/)

# Linux基础课最后一课

## 租云服务器及配环境 **（文中未提到的配置，均不需要更改！！！）**

> 建议使用阿里云，因为yxc喜欢用这个做演示

### 一、[阿里云](https://www.aliyun.com/)(好像学生优惠是有范围的，只能买[学生认证](https://university.aliyun.com/mobile?clubTaskBiz=subTask..11542025..10215..&userCode=455ljtgy)页面下的产品)

1. 进入[阿里云](https://www.aliyun.com/)，完成账号注册。推荐使用`支付宝`联合登陆
2. 进入[云服务器ECS购买界面](https://ecs-buy.aliyun.com/ecs?spm=a2c4g.11186623.0.0.58e63ea1P4A52j#/custom/prepay/cn-hangzhou)
3. 第一栏：
   --付费类型：包年包月
   --地域：离你近的就好
   --网络及可用区：随意选择
   ![屏幕截图 2025-07-07 110102.png](https://cdn.acwing.com/media/article/image/2025/07/07/182463_c4087a695a-屏幕截图-2025-07-07-110102.png) 

4. 第二栏 实例与镜像：
   --选择一个配置比较低的，但内存最好在`2.0GB`以上
   --若找不到配置合适的服务器，可以尝试在第一栏中`改变可用区`
   --镜像一定要选择`Ubuntu 20.04`
   ![屏幕截图 2025-07-07 110231.png](https://cdn.acwing.com/media/article/image/2025/07/07/182463_ea7c457f5a-屏幕截图-2025-07-07-110231.png) 
   ![屏幕截图 2025-07-07 110238.png](https://cdn.acwing.com/media/article/image/2025/07/07/182463_edccb93d5a-屏幕截图-2025-07-07-110238.png) 
5. 第三栏存储无需更改
6. 第四栏带宽与安全组
   --一定要选中`分配公网IP`（默认应该是选中的）
   --带宽计费模式选择`按使用流量`：这样比较便宜
   --带宽峰值拉到最满
   --开通IPv4端口/协议：一开始只选择`22端口`即可
7. 第五栏管理设置：
   --选择`自定义密码`并设置登陆密码

### 二、腾讯云（[学生认证](https://cloud.tencent.com/act/campus#step1)）

1. 进入[官网](https://cloud.tencent.com/)注册账号
2. 进入[选购界面](https://buy.cloud.tencent.com/cvm?tab=lite&supportConfidentiality=false&wanIp=0&templateCreateMode=createLt&isBackup=false&backupDiskType=ALL&backupDiskCustomizeValue=&backupQuotaSegment=1&backupQuota=1)
3. 配置过程和阿里云类似，就不讲了


----------



## 登陆并配置服务器(登陆之前先在控制台重置一下密码)

1. 执行：```ssh root@xxx.xxx.xxx.xxx  #xxx.xxx.xxx.xxx替换成新服务器的公网IP```

2. 可以看一下服务器配置`cat /proc/cpuinfo `

3. 创建acs用户

   ```
   adduser acs  # 创建用户acs
   usermod -aG sudo acs  # 给用户acs分配sudo权限
   ```

4. 退回AC Terminal，然后配置acs用户的别名和免密登录，可以参考[4. ssh——ssh登录](https://www.acwing.com/file_system/file/content/whole/index/content/2898263/)。

5. 配置新服务器的工作环境
   将AC Terminal的配置传到新服务器上：

    ```
   scp .bashrc .vimrc .tmux.conf server_name:  #server_name需要换成自己配置的别名
    ```

6. 安装tmux和docker
   登录自己的服务器，然后安装tmux：

   ```
   sudo apt-get update
   sudo apt-get install tmux
   ```

   打开`tmux`。（养成好习惯，所有工作都在`tmux`里进行，防止意外关闭终端后，工作进度丢失）

   然后在`tmux`中安装`docker`即可。

```
# 更新包列表
sudo apt-get update

# 直接从Ubuntu仓库安装Docker
sudo apt-get install docker.io

# 启动并设置开机自启
sudo systemctl start docker
sudo systemctl enable docker

# 添加用户到docker组
sudo usermod -aG docker $USER

# 重新加载组权限
newgrp docker
```

## docker教程

参考Linux基础课笔记[docker教程](https://www.acwing.com/blog/content/10878/)

### 将当前用户添加到`docker`用户组

为了避免每次使用`docker`命令都需要加上`sudo`权限，可以将当前用户加入安装中自动创建的`docker`用户组(可以参考[官方文档](https://docs.docker.com/engine/install/linux-postinstall/))：

```
sudo usermod -aG docker $USER
```

执行完此操作后，需要退出服务器，再重新登录回来，才可以省去`sudo`权限。

### `docker`-`images`-`container`之间的关系

![屏幕截图 2025-07-08 091245.png](https://cdn.acwing.com/media/article/image/2025/07/08/182463_ccfc08275b-屏幕截图-2025-07-08-091245.png) 

### 镜像（images）

配置 daemon.json，这样以后所有 Docker 拉取都会自动使用国内镜像源：

1. `docker pull ubuntu:20.04`：拉取一个镜像
   `docker pull ubuntu:20.04`：拉取一个镜像

**如果不行可以尝试**：
① 创建 Docker 配置文件

```bash
sudo mkdir -p /etc/docker
sudo tee /etc/docker/daemon.json <<-'EOF'
{
  "registry-mirrors": [
    "https://docker.m.daocloud.io",
    "https://dockerproxy.com",
    "https://docker.nju.edu.cn",
    "https://docker.mirrors.sjtug.sjtu.edu.cn"
  ]
}
EOF
```

② 重新加载并重启 Docker

```bash
sudo systemctl daemon-reload
sudo systemctl restart docker
```

③ 验证配置是否生效

```bash
docker info | grep -A 10 "Registry Mirrors"
```

④ 测试镜像拉取

```bash
docker pull ubuntu:20.04
```

现在应该能看到下载速度明显提升了！配置完成后，以后所有的 `docker pull` 命令都会自动使用这些镜像源，不需要每次都指定地址。

试试看，如果第一个镜像源有问题，Docker 会自动尝试下一个。

2. `docker images`：列出本地所有镜像
3. `docker image rm ubuntu:20.04` 或 `docker rmi ubuntu:20.04`：删除镜像`ubuntu:20.04`
4. `docker [container] commit CONTAINER IMAGE_NAME:TAG`：创建某个`container`的镜像
   [ ]代表可选
5. `docker save -o ubuntu_20_04.tar ubuntu:20.04`：将镜像`ubuntu:20.04`导出到本地文件`ubuntu_20_04.tar`中
6. `docker load -i ubuntu_20_04.tar`：将镜像`ubuntu:20.04`从本地文件`ubuntu_20_04.tar`中加载出来

### 容器（container）

1. `docker [container] create -it ubuntu:20.04`：利用镜像`ubuntu:20.04`创建一个容器。
2. `docker ps -a`：查看本地的所有容器
3. `docker [container] start CONTAINER`：启动容器
4. `docker [container] stop CONTAINER`：停止容器
5. `docker [container] restart CONTAINER`：重启容器
6. `docker [contaienr] run -itd ubuntu:20.04`：创建并启动一个容器
   `-it` 是交互式运行并分配终端（前台运行），`-itd` 是在 `-it` 基础上加了 `-d` 参数让容器在后台运行（detached mode）。
7. `docker [container] attach CONTAINER`：进入容器
   先按`Ctrl-p`，再按`Ctrl-q`可以挂起容器
8. `docker [container] exec CONTAINER COMMAND`：在容器中执行命令
9. `docker [container] rm CONTAINER`：删除容器
10. `docker container prune`：删除所有已停止的容器
11. `docker export -o xxx.tar CONTAINER`：将容器`CONTAINER`导出到本地文件`xxx.tar`中
12. `docker import xxx.tar image_name:tag`：将本地文件`xxx.tar`导入成镜像，并将镜像命名为`image_name:tag`
13. `docker export/import`与`docker save/load`的区别：
    `export/import`会丢弃历史记录和元数据信息，仅保存容器当时的快照状态
    `save/load`会保存完整记录，体积更大
14. `docker top CONTAINER`：查看某个容器内的所有进程
15. `docker stats`：查看所有容器的统计信息，包括CPU、内存、存储、网络等信息
16. `docker cp xxx CONTAINER:xxx` 或 `docker cp CONTAINER:xxx xxx`：在本地和容器间复制文件
17. `docker rename CONTAINER1 CONTAINER2`：重命名容器
18. `docker update CONTAINER --memory 500MB`：修改容器限制

# Django课从这里开始（下面每一个二级标题 和 每节课的标题对应）

## 1.1 课程概论和Python3语法（上）

## 1.2 Python3语法（下）

## 1.3 习题课



## 2. 配置docker、git环境与项目创建

### 准备工作-配置环境

1. `scp /var/lib/acwing/docker/images/ django_lesson_1_0.tar server_name:` 将镜像上传到自己租的云端服务器

2. `ssh server_name` 登录自己的云端服务器

3. `docker load -i django_lesson_1_0.tar`将镜像加载到本地

4. `docker run -p 20000:22 -p 8000:8000 --name django_server -itd django_lesson:1.0`创建并运行django_lesson:1.0镜像 (端口要自己去云平台放行)

   端口放行步骤：
   ①点击您要配置的轻量应用服务器实例
   ②在服务器详情页面，点击左侧菜单的 "安全" → "防火墙"，点击 "添加规则" 按钮
   ![屏幕截图 2025-07-09 103110.png](https://cdn.acwing.com/media/article/image/2025/07/09/182463_c8f3d5e95c-屏幕截图-2025-07-09-103110.png) 

   ③添加端口规则
   ![屏幕截图 2025-07-09 103318.png](https://cdn.acwing.com/media/article/image/2025/07/09/182463_1585377f5c-屏幕截图-2025-07-09-103318.png) 
   为您的两个端口分别添加规则：

   #### 添加端口 20000 (SSH)

   - **应用类型**：自定义
   - **协议**：TCP
   - **端口**：20000
   - **源地址**：0.0.0.0/0（建议改为您的IP地址）
   - **备注**：SSH端口

   #### 添加端口 8000 (Django)

   - **应用类型**：自定义
   - **协议**：TCP
   - **端口**：8000
   - **源地址**：0.0.0.0/0
   - **备注**：Django应用
     ![屏幕截图 2025-07-09 104259.png](https://cdn.acwing.com/media/article/image/2025/07/09/182463_723e9d335c-屏幕截图-2025-07-09-104259.png) 


5. `docker attach django_server`进入创建的docker容器
6. `adduser acs`创建普通用户acs
7. `usermod -aG sudo acs`给用户acs分配sudo权限
8. `ctrl p + ctrl q`挂起容器
9. 返回`AC terminal`，为acs用户配置别名和免密登录
   `cd .ssh/`进到ssh目录
   `vim config`配置别名
   `ssh-copy-id 别名` 为acs用户一键添加公钥，免密登录
   `scp .bashrc .vimrc .tmux.conf 别名:`配置一下环境
   ###开始施工
10. `django-admin startproject acapp` 创建django项目acapp
    目录结构会变成这样
    ![屏幕截图 2025-07-09 111309.png](https://cdn.acwing.com/media/article/image/2025/07/09/182463_a6b1440e5c-屏幕截图-2025-07-09-111309.png) 
11. 配置git
    `ssh-keygen` 生成密钥用于连接到ac git上面
    在git偏好设置中，打开ssh密钥，添加一下刚才生成的公钥
    `git init` 进到acapp中将其配置成git仓库
    打开git，在git上创建一个仓库（项目）按照下面的提示在acs里面配置一下git
    `git config --global user.name xxx`
    `git config --global user.email xxx@xxx.com`
    `git add .`
    `git commit -m "xxx"`
    `git remote add origin git@git.acwing.com:xxx/XXX.git` #建立连接
    `git push --set-upstream origin master`
12. 在`tmux`里跑一下项目：
    `python3 manage.py runserver 0.0.0.0:8000`
13. `ag ALLOWED-HOSTS` 全文搜索
    找到这个字段所在位置，并将自己的IP地址添加到里面
    便可用 IP地址:8000 打开django页面
    附一张成功后的截图![屏幕截图 2025-07-09 120339.png](https://cdn.acwing.com/media/article/image/2025/07/09/182463_b79799af5c-屏幕截图-2025-07-09-120339.png) 
14. git 一下代码
    注意：在git仓库的根目录下（acapp）,执行`vim .gitignore`
    在文件里面写上 `**/__pycache__`(两个杠)
    再去添加文件的时候就不会再添加这类不必要的文件
15. 再打开一个tmux，(一个tmux用于维护控制台，另一个tmux用于开发)
    `python3 manage.py startapp game` 创建gameapp
    commit一下
16. 登录django管理员界面
    `ctrl c` 先关掉控制台
    `python3 manage.py migrate` 同步一下数据库的修改
    `python3 manage.py createsuperuser` 创建管理员账号
    `pyhton3 manage.py runserver 0.0.0.0:8000` 启动控制台
    `IP地址:8000/admin` 进到管理员登录界面，输入一下刚才创建的账号即可进到管理员界面
    8\. 
    创建网页的步骤：
    `cd game`
    `touch urls.py`
    `mkdir templates`
    `vim views` 定义一个index函数 视频位置 1:00:00
    `vim urls.py` 写一下路由
    `cd acapp vim urls.py` 将刚才的路由写到总路由里面
     **最关键的来了（y总说的, 整个项目只需要操作这四个东西）：models，views，urls，templates** 
    这部分建议边照着做边学，在示例的基础上可以再加点料，加深理解
    每个app里面有这四个东西
    * models，数据类库，**定义各种数据类型**
      * class User
      * ……
    * views，**实现各种函数**，做成文件夹，防止多个函数放进同一个文件里面，比较麻烦
      * ……
    * urls，路由库，**用于解析访问网站时要干嘛**
    * templates，**存html**

**game/views.py 示例**

```
from django.http import HttpResponse

def index(resquest):
    return HttpResponse("我的第一个网页！！！！")
```

也就是，`index()`函数在接收到一个**用户的请求**的时候，就会被调用，并返回响应

**game/urls.py 示例**

```
from django.urls import path
from game.views import index # 从game/views.py 里面调用index函数

urlpatterns = [
    path('', index, name = 'game_index')
]
```

这其中，`path('PATH', function, name)` 的含义是，在用户访问网站的时候，如果是网站`/game/PATH`，就会调用`function`，名字为`name`，这是在`/game/`目录下的调用，所以这个`'PATH'`是在`/game/`的基础上的相对路径，所以他的绝对路径是网站`/game/PATH`。

**acapp/urls.py 示例**

```
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('', include('game.urls')),
    path('admin/', admin.site.urls)
]
```

这其中，`path('PATH', include('game.urls'))`的含义是，在用户访问网站的时候，如果是`网站/PATH`，就会走到`/game/urls`，并根据`/game/urls.py`来跑路由，就是说，用户在访问`网站/`的时候，由于此时调用的函数是`include('game.urls')`，所以访问`网站/`相当于根据`game/urls`访问。所以，从这里也可以明白为什么`网站/admin`会跳转到管理员页面。

综上，访问`网站/`的时候，首先是相当于访问`网站/game/`，然后根据`/game/urls.py`，此时对于`game/urls.py`来说访问的相对路径是`''`，所以会调用`views.index`，然后就会看到网页：
![屏幕截图 2025-07-10 140347.png](https://cdn.acwing.com/media/article/image/2025/07/10/182463_a7693dd75d-屏幕截图-2025-07-10-140347.png) 

9\. 如果**game/views.py**是这样写的：

```
from django.http import HttpResponse

def index(request):
    line1 = '<h1 style="text-align: center">我的第一个网页！！！！</h1>'
    return HttpResponse(line1)
```

就会看到这样的网页（源代码）：

```
<h1 style="text-align: center">我的第一个网页！！！！</h1>
```

正常访问是一个居中一级标题的`我的第一个网页！！！！`，如果是源代码就会是上述情况，所以`HttpResponse()`“本质上”是将参数里的字符串写进`.html`中。

10\. 如果要在网页上放图片，字符换成`<img src='URL' width='2000'>`，其中`URL`是图片的链接，在网上找个图片，把图片的`URL`复制过来即可，`width`是图片大小。

11\.如果要写跳转链接（超链接）：

```
<a href="https://www.acwing.com">acwing</a>
```

网页会出现一个可点击的字符串`acwing`，点击即跳转acwing官网。`<a href='LINK'>string</a>`的含义是，定义一个跳转链接，并显示成string，在网页点击的时候会跳转到LINK

### 最后附上我的代码、网址、项目地址、以及最终的效果

#### 我的代码

![屏幕截图 2025-07-10 153939.png](https://cdn.acwing.com/media/article/image/2025/07/10/182463_17ce38925d-屏幕截图-2025-07-10-153939.png) 

#### 我配置好环境的网址：

http://39.96.169.44:8000/

#### 我的项目地址：

https://git.acwing.com/HongyiGuo/acapp

#### 效果

主界面
![屏幕截图 2025-07-10 154247.png](https://cdn.acwing.com/media/article/image/2025/07/10/182463_899dd3ff5d-屏幕截图-2025-07-10-154247.png) 
play界面
![屏幕截图 2025-07-10 154302.png](https://cdn.acwing.com/media/article/image/2025/07/10/182463_8e7e0ebf5d-屏幕截图-2025-07-10-154302.png)

## 3. 创建菜单界面

### 项目总览

![屏幕截图 2025-07-11 101734.png](https://cdn.acwing.com/media/article/image/2025/07/11/182463_3679d9d85d-屏幕截图-2025-07-11-101734.png) 

### 创建项目框架

#### 首先整理项目结构

我们在`python`中调用`import urls.xxx`时，`urls.py` 还是 `urls` 作为一个 `moudle` （文件夹）都可以。

这里为了防止 `urls.py` 和 `views.py` 太冗长，因此删掉单个文件，改用 `moudle` 。如果是 `moudle` 的话，需要有 `__init__.py` 帮助 `python 解释器`认定这个文件夹是一个 `moudle` 。

```
acs:~/acapp$ cd game/
acs:~/acapp/game$ rm views.py
acs:~/acapp/game$ rm urls.py
acs:~/acapp/game$ mkdir views urls
```

`models`同理

```
acs:~/acapp/game$ rm models.py
acs:~/acapp/game$ mkdir models
```

建立`__init__.py`

```
acs:~/acapp/game$ touch urls/__init__.py
acs:~/acapp/game$ touch models/__init__.py
acs:~/acapp/game$ touch views/__init__.py
```

此外建立 `static` 管理静态资源。

#### 修改全局配置

1\. 设置时区
在`acapp/acapp/settings.py` ：

```
-TIME_ZONE = 'UTC'
+TIME_ZONE = 'Asia/Shanghai'
```

2\. 把自己的app加到settings
![屏幕截图 2025-07-11 105904.png](https://cdn.acwing.com/media/article/image/2025/07/11/182463_15ac5d505e-屏幕截图-2025-07-11-105904.png) 
如上，我们在`settings`里面加入。
![屏幕截图 2025-07-11 105912.png](https://cdn.acwing.com/media/article/image/2025/07/11/182463_28c61a4a5e-屏幕截图-2025-07-11-105912.png) 

3\. 设置静态文件
![屏幕截图 2025-07-11 111130.png](https://cdn.acwing.com/media/article/image/2025/07/11/182463_be20997b5e-屏幕截图-2025-07-11-111130.png) 

```
acs:~/acapp/game$ cd static/
acs:~/acapp/game/static$ ls
acs:~/acapp/game/static$ mkdir css js image
acs:~/acapp/game/static$ cd image/
acs:~/acapp/game/static/image$ mkdir menu playground settings
acs:~/acapp/game/static/image$ ls
menu  playground  settings
```

4\. 加一个背景图片

```
acs:~/acapp/game/static/image/menu$ wget --output-document=background.gif https://cdn.acwing.com/media/article/image/2023/03/17/1_067a3e9cc4-background.gif
```

现在可以通过`<你的域名/ip>:<端口号>/static/image/menu/background.gif`访问你刚刚上传的图片
[我图片的地址](http://39.96.169.44:8000/static/image/menu/background.gif)

### 创建js文件的文件夹

一个项目有一个`css`文件就可以
`js`文件夹下一般分两个，`dist`和`src`

+ `dist`存储最终生成的，使用的`js`文件
+ `src`存储源文件
  通过`bash`实现`js`的合并
  所有`bash`文件可以放在一个文件夹里

脚本：

```shell
#! /bin/bash

JS_PATH=/home/acs/acapp/game/static/js/
JS_PATH_DIST=${JS_PATH}dist/
JS_PATH_SRC=${JS_PATH}src/

find $JS_PATH_SRC -type f -name '*.js' | sort | xargs cat > ${JS_PATH_DIST}game.js
```

### 添加html文件

进入到`/acapp/game/templates`
同样创建三个文件夹`menu playground settings`
为了支持多终端，创建文件夹`mutiends`，并添加web.html文件，写入如下内容：

```html
//path: acapp/templates/multiends/web.html

{% load static %} //使用静态库需要写这个

<head>
    <link rel="stylesheet" href="https://cdn.acwing.com/static/jquery-ui-dist/jquery-ui.min.css">
    <script src="https://cdn.acwing.com/static/jquery/js/jquery-3.3.1.min.js"></script>
    <link rel="stylesheet" href="{% static 'css/game.css' %}">
    <script src="{% static 'js/dist/game.js' %}"></script>

</head>

<body styles="margin: 0">
    <div id="acgame_12345678"></div>  //随便起个名字
    <script>
        $(document).ready(function(){
            let ac_game = new AcGame("acgame_12345678");      //js文件的函数名
        });
    </script>
</body>
```

`下面是代码讲解: `

#### HTML部分

```html
<body styles="margin: 0">
    <div id="acgame_12345678"></div>
```

- `<body>` 标签定义了网页的主体内容
- `styles="margin: 0"` 这里应该是 `style="margin: 0"`（少了个e），用于设置body的外边距为0
- `<div id="acgame_12345678"></div>` 创建了一个空的div容器，id是"acgame_12345678"

#### JavaScript/jQuery部分

```javascript
<script>
    $(document).ready(function(){
        let ac_game = new AcGame("acgame_12345678");
    });
</script>
```

这部分使用了**jQuery库**（一个JavaScript库）：

1. **`$(document).ready(function(){...})`** 
   - 这是jQuery的语法
   - 意思是"等待整个HTML文档加载完成后，再执行里面的代码"
   - 相当于原生JavaScript的 `window.onload`

2. **`let ac_game = new AcGame("acgame_12345678");`**
   - 创建了一个名为 `ac_game` 的变量
   - 使用 `new` 关键字实例化了一个 `AcGame` 类的对象
   - 传入参数 `"acgame_12345678"`（就是上面div的id）

#### 整体作用

这段代码的作用是：

1. 创建一个空的div容器作为游戏画布
2. 等待页面加载完成
3. 初始化一个游戏对象，并将其绑定到这个div容器上

**注意**：要使用这段代码，你需要：

- 引入jQuery库（通常在`<head>`中添加）
- 确保有一个定义了 `AcGame` 类的JavaScript文件

这是典型的网页游戏初始化代码的写法。



------



### 添加js文件

`view` 在云端运行
`js` 在用户本地运行

1. 在`src`下创建文件`menu playgroud settings`
2. 并在`src`下创建 总js文件 `zbase.js` 用这个名字是因为字典序靠后，在生成`dist`中`js`文件时，需要它最后出现，不然会错。

```
//path: acapp/game/static/js/src/zbase.js

class AcGame {
    constructor(id) {

    }
}
```

### views

进入`views`创建三个文件夹`menu playgroud settings`，和 `index.py` 并在每一个文件夹下添加`__init__.py`

```
# acapp/game/views/index.py
from django.shortcuts import render  # 渲染库

def index(request):
    return render(request, "multiends/web.html")
```

### 添加路由

在`game/urls`中创建`menu playgroud settings`文件夹，和`index.py`
在三个文件夹中，创建`index.py`，加入内容：

```python
from django.urls import path
urlpatterns = [

]
```

在`game/urls`下的`index.py`中加入这三个路由, 并且添加`views`

```python
# game/urls/index.py
from django.urls import path, include
from game.views.index import index

urlpatterns = [
    path("", index, name="index"),
    path("menu/", include("game.urls.menu.index")),
    path("playground/", include("game.urls.playground.index")),
    path("settings/", include("game.urls.settings.index")),
]
```

进入到`acapp/acapp` 打开`urls.py`

```python
# acapp/acapp/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('', include('game.urls.index')),
    path('admin/', admin.site.urls),
]
```

至此，框架搭建完成

### 梳理一下路由的过程，以及构建框架的顺序

#### 在网页中输入`服务器公网ip:8000`后，路由过程

![2159_68ac40d2c5-调用结构.jpg](https://cdn.acwing.com/media/article/image/2025/07/12/182463_5f11f2a85e-2159_68ac40d2c5-调用结构.jpg) 

#### 搭建框架的顺序

```
|-- README.md                                                                                                                                                                                                    |-- acapp                                                                                                                                                                                                        |   |-- __init__.py                                                                                                                                                                                                                                                                                                                                                                                           
|   |-- settings.py     ----------------------------------------------2
|   |-- urls.py            ----------------------------------------------12
|-- db.sqlite3
|-- game                 ----------------------------------------------1
|   |-- __init__.py
|   |-- admin.py
|   |-- apps.py
|   |-- migrations
|   |   |-- __init__.py
|   |-- models           ----------------------------------------------3
|   |   |-- __init__.py
|   |-- static              ----------------------------------------------4
|   |   |-- audio
|   |   |-- css
|   |   |   `-- game.css
|   |   |-- image
|   |   |   |-- menu
|   |   |   |   `-- backgroud.gif
|   |   |   |-- playgroud
|   |   |   `-- settings
|   |   `-- js               -----------------------------------------------5
|   |       |-- dist
|   |       |   `-- game.js   
|   |       `-- src
|   |           |-- menu
|   |           |-- playground
|   |           |-- settings
|   |           `-- zbase.js  ------------------------------------------8
|   |-- templates    ----------------------------- -----------------6
|   |   |-- menu       
|   |   |-- mutiends
|   |   |   `-- web.html  -------------------------------------------7
|   |   |-- playground
|   |   `-- settings
|   |-- tests.py
|   |-- urls         --------------------------------------------------3
|   |   |-- __init__.py
|   |   |-- index.py  -----------------------------------------------11
|   |   |-- menu
|   |   |   |-- __init__.py
|   |   |   `-- index.py ---------------------------------------------11
|   |   |-- playground
|   |   |   |-- __init__.py
|   |   |   `-- index.py ---------------------------------------------11
|   |   `-- settings
|   |       |-- __init__.py
|   |       `-- index.py ---------------------------------------------11
|   `-- views      --------------------------------------------------3
|       |-- __init__.py
|       |-- index.py    ---------------------------------------------9
|       |-- menu
|       |   `-- __init__.py
|       |-- playground
|       |   `-- __init__.py
|       `-- settings
|           `-- __init__.py
|-- manage.py
`-- scripts     ----------------------------------------------------6
    `-- compress_game_js.sh
```

### 开始菜单

#### 1. 创建菜单界面对象

`/game/static/js/src/menu/zbase.js`

```
class AcGameMenu {
    constructor(root) {
        this.root = root;
        this.$menu = $(`
<div class="ac-game-menu">
</div>
`);
        this.root.$ac_game.append(this.$menu);
    }
}
```

#### 2. 并且同步添加css

`/game/static/css/game.css`

```
.ac-game-menu {
    width: 100%;
    height: 100%;
    background-image: url("/static/image/menu/background.gif");
    background-size: 100% 100%;
    user-select: none;
}
```

#### 3. 将对象添加到

`/game/static/js/src/zbase.js`

```
class AcGame {
    constructor(id) {
        this.id = id;
        this.$ac_game = $('#' + id);
        this.menu = new AcGameMenu(this);
    }
} 
```

##### 前三步的一些解释

###### 语法

- `$` = jQuery 函数
- `$('#id')` = 选择元素
- `$('<div>')` = 创建元素  
- `this.$variable` = 存储 jQuery 对象的变量（命名习惯）

这就是为什么之前的 HTML 中需要 `$(document).ready()` —— 它们都是 jQuery 的语法！

###### 完整的执行流程

初始状态

```html
<!-- 原始 HTML -->
<body style="margin: 0">
    <div id="acgame_12345678"></div>
    <script>
        $(document).ready(function(){
            let ac_game = new AcGame("acgame_12345678");
        });
    </script>
</body>
```

执行过程详解

**步骤 1：页面加载完成**

```javascript
$(document).ready(function(){
    // 等待 DOM 加载完成后执行
    let ac_game = new AcGame("acgame_12345678");
});
```

**步骤 2：创建 AcGame 实例**

```javascript
new AcGame("acgame_12345678")
// 调用 AcGame 构造函数，传入 id = "acgame_12345678"
```

**步骤 3：AcGame 构造函数执行**

```javascript
class AcGame {
    constructor(id) {
        // 1. 保存 id
        this.id = id;  // this.id = "acgame_12345678"
        
        // 2. 查找 DOM 元素
        this.$ac_game = $('#' + id);  
        // 等同于 $('#acgame_12345678')
        // 找到 <div id="acgame_12345678"></div>
        // 将其包装成 jQuery 对象存储
        
        // 3. 创建菜单
        this.menu = new AcGameMenu(this);
        // 调用 AcGameMenu 构造函数
        // 传入 this（当前 AcGame 实例）作为 root
    }
}
```

**步骤 4：AcGameMenu 构造函数执行**

```javascript
class AcGameMenu {
    constructor(root) {
        // 1. 保存父对象引用
        this.root = root;  // root 是 AcGame 实例
        
        // 2. 创建菜单 DOM
        this.$menu = $(`
            <div class="ac-game-menu">
            </div>
        `);
        // 创建一个新的 div 元素
        // 设置 class="ac-game-menu"
        // 此时这个 div 还在内存中，不在页面上
        
        // 3. 将菜单添加到游戏容器
        this.root.$ac_game.append(this.$menu);
        // this.root 是 AcGame 实例
        // this.root.$ac_game 是 $('#acgame_12345678')
        // append() 把新创建的菜单 div 插入到游戏容器中
    }
}
```

最终结果

**DOM 结构变化**

```html
<!-- 执行前 -->
<div id="acgame_12345678"></div>

<!-- 执行后 -->
<div id="acgame_12345678">
    <div class="ac-game-menu"></div>
</div>
```

**对象关系图**

```
ac_game (AcGame 实例)
├── id: "acgame_12345678"
├── $ac_game: jQuery对象(指向 #acgame_12345678)
└── menu: (AcGameMenu 实例)
    ├── root: 指向 ac_game
    └── $menu: jQuery对象(指向 .ac-game-menu)
```

**样式应用**

```css
.ac-game-menu {
    width: 100%;
    height: 100%;
    background-image: url("/static/image/menu/background.gif");
    background-size: 100% 100%;
    user-select: none;
}
```

菜单 div 会：

- 占满父容器（100% 宽高）

- 显示背景图片

- 禁止文字选择

  

内存中的引用关系

```javascript
// 可以这样访问各个部分
ac_game.$ac_game           // 游戏容器
ac_game.menu              // 菜单对象
ac_game.menu.$menu        // 菜单 DOM
ac_game.menu.root         // 返回 ac_game（循环引用）
```



###### 总结

当你运行 `new AcGame("acgame_12345678")` 时：

1. 找到 `id="acgame_12345678"` 的 div
2. 创建一个新的菜单 div
3. 把菜单 div 插入到游戏容器中
4. 最终 HTML 结构变成：

```html
<div id="acgame_12345678">
    <div class="ac-game-menu">
    </div>
</div>
```





#### 4. 添加页面的选项：

`/game/static/js/src/menu/zbase.js`

```javascript
class AcGameMenu {
    constructor(root) {
        this.root = root;
        this.$menu = $(`
<div class="ac-game-menu">
// 新加内容
    <div class="ac-game-menu-field">
        <div class="ac-game-menu-field-item ac-game-menu-field-item-single-mode">
            单人模式
        </div>
        <br>
        <div class="ac-game-menu-field-item ac-game-menu-field-item-multi-mode">
            多人模式
        </div>
        <br>
        <div class="ac-game-menu-field-item ac-game-menu-field-item-settings">
            设置
        </div>
    </div>
// 新加内容
</div>
`);
        this.root.$ac_game.append(this.$menu);
    }
}
```

#### 5. 更新开始菜单的选项：

`/game/static/css/game.css`

```css
.ac-game-menu {
    width: 100%;
    height: 100%;
    background-image: url("/static/image/menu/background.gif");
    background-size: 100% 100%;
    user-select: none;
}

/*注释起来的是yxc的代码，我觉得效果不太好，就让ai重新写了一个，放在后面了*/
/*.ac-game-menu-field{*/
/*    width: 20vw;*/
/*    position: relative;*/
/*    top: 40vh;*/
/*    left: 19vw;*/
/*}*/

/*.ac-game-menu-field-item {*/
/*    color: white;*/
/*    height: 7vh;*/
/*    width: 18vw;*/
/*    font-size: 5vh;*/
/*    font-style: italic;*/
/*    padding: 1.3vh;*/
/*    text-align: center;*/
/*    background-color: rgba(39,21,28, 0.6);*/
/*    border-radius: 10px;*/
/*    letter-spacing: 0.4vw;*/
/*    cursor: pointer;*/
/*}*/

/*.ac-game-menu-field-item:hover {*/
/*    transform: scale(1.2);*/
/*    transition: 150ms;*/
/*}*/

.ac-game-menu-field {
    width: 20vw;
    position: relative;
    top: 38vh;
    left: 19vw;
}

.ac-game-menu-field-item {
    color: #e4e4e7;
    height: 9vh;
    width: 18vw;
    font-size: 4vh;
    font-weight: 400;
    font-family: 'Inter', 'Roboto', sans-serif;
    padding: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, rgba(25, 25, 35, 0.6), rgba(35, 35, 45, 0.5));
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    letter-spacing: 0.15vw;
    cursor: pointer;
    text-transform: uppercase;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.4),
                inset 0 1px 0 rgba(255, 255, 255, 0.06);
    backdrop-filter: blur(12px);
    position: relative;
    overflow: hidden;
    transition: all 0.2s ease;
    margin-bottom: 0.5vh;
}

.ac-game-menu-field-item::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg,
                transparent,
                rgba(255, 255, 255, 0.03),
                rgba(255, 255, 255, 0.06),
                rgba(255, 255, 255, 0.03),
                transparent);
    transition: left 0.5s ease;
}

.ac-game-menu-field-item::after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 0;
    width: 0;
    height: 2px;
    background: linear-gradient(90deg, #f39c12, #e74c3c);
    transition: width 0.3s ease;
}

.ac-game-menu-field-item:hover {
    transform: translateY(-2px);
    color: #ffffff;
    background: linear-gradient(135deg, rgba(30, 30, 40, 0.7), rgba(40, 40, 50, 0.6));
    border-color: rgba(255, 255, 255, 0.2);
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.5),
                0 0 24px rgba(243, 156, 18, 0.1),
                inset 0 1px 0 rgba(255, 255, 255, 0.1);
    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
}

.ac-game-menu-field-item:hover::before {
    left: 100%;
}

.ac-game-menu-field-item:hover::after {
    width: 100%;
}

.ac-game-menu-field-item:active {
    transform: translateY(0);
    background: linear-gradient(135deg, rgba(25, 25, 35, 0.7), rgba(35, 35, 45, 0.6));
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.5),
                inset 0 2px 4px rgba(0, 0, 0, 0.3);
}

/* 可选：为不同按钮添加不同的强调色 */
.ac-game-menu-field-item:nth-child(1):hover::after {
    background: linear-gradient(90deg, #3498db, #2980b9);
}

.ac-game-menu-field-item:nth-child(2):hover::after {
    background: linear-gradient(90deg, #e74c3c, #c0392b);
}

.ac-game-menu-field-item:nth-child(3):hover::after {
    background: linear-gradient(90deg, #95a5a6, #7f8c8d);
}
```

#### 6. 更新点击按钮的动作

`/game/static/js/src/menu/zbase.js`

```javascript
class AcGameMenu {
    constructor(root) {
        this.root = root;
        this.$menu = $(`
<div class="ac-game-menu">
    <div class="ac-game-menu-field">
        <div class="ac-game-menu-field-item ac-game-menu-field-item-single-mode">
            单人模式
        </div>
        <br>
        <div class="ac-game-menu-field-item ac-game-menu-field-item-multi-mode">
            多人模式
        </div>
        <br>
        <div class="ac-game-menu-field-item ac-game-menu-field-item-settings">
            设置
        </div>
    </div>
</div>
`);
        this.root.$ac_game.append(this.$menu);
        this.$single_mode = this.$menu.find('.ac-game-menu-field-item-single-mode');
        this.$multi_mode = this.$menu.find('.ac-game-menu-field-item-multi-mode');
        this.$settings = this.$menu.find('.ac-game-menu-field-item-settings');

        this.start();
    }

    start() {
        this.add_listening_events();
    }
    add_listening_events() {
        let outer = this;
        this.$single_mode.click(function(){
            outer.hide();
            outer.root.playground.show();
        });
        this.$multi_mode.click(function(){
            console.log("click multi mode");
        });
        this.$settings.click(function(){
            console.log("click settings");
        });
    }
}


```

#### 7. 创建playground界面

`/game/static/js/src/playground/zbase.js`
在未点击按钮时，应该只显示`menu`页面，`playground`页面应当在点击单人或多人游戏后显示。
用`hide()` 隐藏页面，用`show()` 显示页面

```
class AcGamePlayground {
    constructor(root) {
        this.root = root;
        this.$playground = $(`<div>游戏界面</div>`);
        this.hide();
        this.root.$ac_game.append(this.$playground);
        this.start();
    }
    start() {
    }
    show() {
        this.$playground.show();
    }
    hide() {
        this.$playground.hide();
    }
}
```

#### 8. 在`menu`中加入点击单人模式跳转到`playground`的动作

```
class AcGameMenu {
    constructor(root) {
        this.root = root;
        this.$menu = $(`
<div class="ac-game-menu">
    <div class="ac-game-menu-field">
        <div class="ac-game-menu-field-item ac-game-menu-field-item-single-mode">
            单人模式
        </div>
        <br>
        <div class="ac-game-menu-field-item ac-game-menu-field-item-multi-mode">
            多人模式
        </div>
        <br>
        <div class="ac-game-menu-field-item ac-game-menu-field-item-settings">
            设置
        </div>
    </div>
</div>
`);
        this.root.$ac_game.append(this.$menu);
        this.$single_mode = this.$menu.find('.ac-game-menu-field-item-single-mode');
        this.$multi_mode = this.$menu.find('.ac-game-menu-field-item-multi-mode');
        this.$settings = this.$menu.find('.ac-game-menu-field-item-settings');

        this.start();
    }

    start() {
        this.add_listening_events();
    }
    add_listening_events() {
        let outer = this;
        this.$single_mode.click(function(){
            outer.hide();
            outer.root.playground.show();
        });
        this.$multi_mode.click(function(){
            console.log("click multi mode");
        });
        this.$settings.click(function(){
            console.log("click settings");
        });
    }
    show() {
        this.$menu.show();
    }
    hide() {
        this.$menu.hide();
    }
}
```

- **ac_game**：游戏主实例
- **ac_game.menu**：菜单实例
- **root**：菜单实例中存储的 `ac_game` 引用
- **outer**：在事件函数中保存的 `ac_game.menu` 引用

#### 9. 在根`js`加入`playground`的页面

`/game/static/js/src/zbase.js`

```
class AcGame {
    constructor(id) {
        this.id = id;
        this.$ac_game = $('#' + id);
        this.menu = new AcGameMenu(this);
        this.playground = new AcGamePlayground(this);
        this.start();
    }
    start(){
    }
}
```

### 本次课总结：程序执行的流程

```
时间轴 →
│
├─ T1: 浏览器加载 /game/templates/multiends/web.html
│      └─ 创建 <div id="ac_game_12345678">
│
├─ T2: 加载 /game/static/css/game.css
│      └─ 应用样式规则
│
├─ T3: 加载 /game/static/js/dist/game.js (包含所有src下的JS)
│
├─ T4: $(document).ready() 触发
│      └─ 执行: new AcGame("ac_game_12345678")
│
├─ T5: AcGame 构造函数执行 (/game/static/js/src/zbase.js)
│      ├─ this.$ac_game = $('#ac_game_12345678')
│      ├─ new AcGameMenu(this)
│      └─ new AcGamePlayground(this)
│
├─ T6: AcGameMenu 构造函数执行 (/game/static/js/src/menu/zbase.js)
│      ├─ 创建菜单HTML结构
│      ├─ append到游戏容器
│      └─ 绑定点击事件
│
├─ T7: AcGamePlayground 构造函数执行 (/game/static/js/src/playground/zbase.js)
│      ├─ 创建游戏界面HTML
│      ├─ append到游戏容器
│      └─ 执行 hide() 隐藏界面
│
├─ T8: 页面显示完成（只显示菜单）
│
└─ T9: 用户点击"单人模式"
       ├─ 执行 outer.hide() → 菜单消失
       └─ 执行 outer.root.playground.show() → 游戏界面显示
```

## 附加内容：pycharm连接服务器同步写代码(图文详细过程)

之前写在分享里[传送门](https://www.acwing.com/blog/content/11813/)  
有很多新同学没看过，这里迁移到课内

废话不多说直接上图

### 中文界面

#### 打开`工具`——>`部署`——>`配置`

![20211103003725.png](https://cdn.acwing.com/media/article/image/2022/05/02/82975_a87fd61dca-20211103003725.png)

#### 点击左上角`+`，选择`SFTP`

![20211103003956.png](https://cdn.acwing.com/media/article/image/2022/05/02/82975_c5273798ca-20211103003956.png)

#### 新建服务器名称随便取

![20211103004549.png](https://cdn.acwing.com/media/article/image/2022/05/02/82975_ded66a00ca-20211103004549.png)

#### 点击配置ssh连接

![20211103004858.png](https://cdn.acwing.com/media/article/image/2022/05/02/82975_f5849d24ca-20211103004858.png)

#### 填上自己的公网ip和用户名和密码(我这里直接连接docker，所以端口号填的20000)

**！！！！注意：大坑**

`你的用户名不能有符号，只能包含数字和字母(不清楚原因)，否则会连接失败`

这个步骤其实就相当于在配置`.ssh/config`

![82975_05102f57ca-20211103005113.png](https://cdn.acwing.com/media/article/image/2022/05/02/82975_904a43b6ca-82975_05102f57ca-20211103005113.png)

#### 点击测试链接，如果显示下图，说明成功连接

#### 点击确定后，点击`根路径`旁边的`自动检测`,会自动填写服务器的家目录

![20211103010814.png](https://cdn.acwing.com/media/article/image/2022/05/02/82975_be44f9d1ca-20211103010814.png)

#### 然后点击上方的`映射`

![20211103010921.png](https://cdn.acwing.com/media/article/image/2022/05/02/82975_f470c5a6ca-20211103010921.png)

把`部署路径`设置成项目的路径

![20211103011502.png](https://cdn.acwing.com/media/article/image/2022/05/02/82975_0e400a67ca-20211103011502.png)

#### 至此，大功告成！！！

#### 点击`工具`——>`部署`——>`浏览远程主机`

![20211103011745.png](https://cdn.acwing.com/media/article/image/2022/05/02/82975_23883e53ca-20211103011745.png)

就可以在右边看到熟悉的自己的服务器了

测试一下同步修改

修改完记得点击右上角`上传当前远程文件`

![测试pycharm连接gif.gif](https://cdn.acwing.com/media/article/image/2022/05/02/82975_49aa1b8fca-测试pycharm连接gif.gif)

完美！！！！！

### tips

把pycharm设置为中文：

在`Flies`——>`settings`——>`plug-in`，中搜索`chinese`

![20211103013515.png](https://cdn.acwing.com/media/article/image/2022/05/02/82975_618b8eb4ca-20211103013515.png)

下载这个插件



## 4. 创建游戏界面

### 前端的模块化引入

这属于上节课的疑难杂症，由于在 `html` 代码部分，是将整个 `game.js` 文件引入

这样会导致在 `game.js` 中定义的变量，会变成整个网页的 **全局变量**（之后可能会引起变量重名的诸多问题）

因此，我们考虑使用 **模块化引入** 的功能，让网页只引入在 **html** 中需要的部分



#### 修改 `web.html`

```html
<!-- 首先，先删掉上面整个引入 game.js 的部分 -->
<!-- 然后，下方创建对象的部分，先使用模块化引入 -->
......
    <script type="module">
        import {AcGame} from "{% static 'js/dist/game.js' %}"
        $(document).ready(function(){
            let ac_game = new AcGame("ac_game_12345678")
        })
    </script>
......
```



此外，还有修改引入的类，在前面加上 `export`，如下修改 `js/src/zbase.js`

```javascript
export class AcGame {
    ......
}
```



这样，在全局中，只会出现引入的模块，其他的 `.js` 代码不会出现在全局中



### 构建游戏界面框架

文件框架在上一节已经完全搭建好了

这里要完成的是对 **游戏界面画布** 的构建，十分简单

给画布的 **div block** 一个 **class** 叫 **ac-game-playground**，然后在 **game.css** 中进行设置



`static/js/src/playground/=zbase.js`

```javascript
......
    this.$playground = $(`<div class="ac-game-playground"></div>`);
......
```



`game.css`

```css
......
.ac-game-playground{
    width: 100%;
    height: 100%;
    user-select: none;
}
```

---

### 实现游戏引擎框架

首先，需要对这部分有一个基本的认识

游戏中，物体在移动，其实现原理是：每一个动作都会渲染多张图片出来，然后图片快速的切换，从而实现动的过程

因此，需要先实现一个游戏引擎的基类 `AcGameObject` ，使得每帧能渲染一张图片出来

该基类需要具备的功能有：

1. `start()` 在游戏开始的第一帧时需要执行的任务（一般是创建对象）
2. `update()` 在游戏开始后的每一帧均会执行的任务（一般是渲染当前对象的各种状态）
3. `on_destroy()` 删掉该物体前需要执行的任务（一般是删掉动画，或者给对手加分）
4. `destroy()` 删掉该物体



根据上述逻辑，我们就可以基本搭建出来一个游戏引擎的基类了，具体如下：

`/static/js/playground/ac_game_object/zbase.js`

```javascript
let AC_GAME_OBJECTS = []; //用于记录当前画布中，需要渲染的对象有哪些

class AcGameObject{
    constructor() {
        AC_GAME_OBJECTS.push(this); //将当前新建的对象，加入到全局的画布中去，参与渲染

        this.has_called_start = false; //是否执行过start
        this.timedelta = 0 ; // 当前帧距离上一帧的时间间隔
        // 该数据记录是为了后续计算速度等参数的
    }

    start(){ // 只会在第一帧执行一次

    }

    update(){ // 每一帧均会执行一次

    }

    on_destroy(){ // 在销毁前执行一次

    }


    destroy(){ // 删掉该物体
        this.on_destroy(); // 删掉该物体前，执行删前的操作

        // 在全局渲染物体中，找到该物体，并将其删掉
        for(let i = 0 ; i < AC_GAME_OBJECTS.length ; i ++){
            if(AC_GAME_OBJECTS[i] === this){  // 三等号，在js里额外加了一层类型相等约束
                AC_GAME_OBJECTS.splice(i, 1);
                break;
            }
        }
    }
}

let last_timestamp;

let AC_GAME_ANIMATION = function (timestamp){ // 回调函数，实现：每一帧重绘时，都会执行一遍
    for(let i = 0 ; i < AC_GAME_OBJECTS.length ; i ++){
        let obj = AC_GAME_OBJECTS[i];
        if(!obj.has_called_start) { // 如果还未执行初始帧动作，就先执行
            obj.start();
            obj.has_called_start = true;
        }else { // 执行过初始帧，就执行每一帧的任务
            obj.timedelta = timestamp - last_timestamp;
            obj.update();
        }
    }

    last_timestamp = timestamp;
    requestAnimationFrame(AC_GAME_ANIMATION);
}


requestAnimationFrame(AC_GAME_ANIMATION); // js提供的api，其功能请见笔记
```

> `window.requestAnimationFrame(callback)` 告诉浏览器——你希望执行一个动画，并且要求浏览器在下次重绘之前调用指定的回调函数更新动画。该方法需要传入一个回调函数作为参数，该回调函数会在浏览器下一次重绘之前执行。
>
> 参数 `callback` : 下一次重绘之前更新动画帧所调用的函数(即上面所说的回调函数)。该回调函数会被传入 `DOMHighResTimeStamp` 参数，该参数与 `performance.now()` 的返回值相同，它表示 `requestAnimationFrame()` 开始去执行回调函数的时刻。
>
> 接下来所有的一切游戏，都是基于这个引擎的基类完成的

---

### 实现游戏地图功能

目标：实现一个每一秒都在渲染的纯黑背景

虽然现阶段要实现的地图较为简单，但为了后期的拓展性，故还是考虑新建一个文件夹来完成

然后在 `js` 中，已经封装好了一个 `canvas` 的 `api` 来帮助实现背景画布，直接调用即可

先铺开画布，然后设置为黑色



`static/js/playground/zbase.js`

```javascript
class AcGamePlayground {
    constructor(root) {
        ......
        // $('.playground')对象已经在 css 文件里渲染出高宽了
        // 现在把他的高宽存下来，往下传递
        this.width = this.$playground.width();
        this.weight = this.$playground.height();
        this.game_map = new GameMap(this);
        ......
    }
    .....
}
```



`static/js/playground/game-map/zbase.js`

```javascript
class GameMap extends AcGameObject { // 继承自游戏引擎基类
    constructor(playground) {
        super(); // 自函数功能：调用基类的构造函数
        this.playground = playground;
        this.$canvas = $(`<canvas></canvas>`)//创建一个canvas的jQuery对象，就是我们要实现的画布
        this.ctx = this.$canvas[0].getContext('2d'); //jQuery对象是一个数组，第一个索引是html对象
        //设置画布的宽高
        this.ctx.canvas.width = this.playground.width;
        this.ctx.canvas.height = this.playground.height;
        this.playground.$playground.append(this.$canvas);
    }

     start(){

     }

     update(){  // 游戏地图每帧都要渲染
        this.render()
     }

     render(){
        this.ctx.fillStyle = "rgba(0, 0, 0, 0.2)";
        this.ctx.fillRect(0, 0, this.ctx.canvas.width, this.ctx.canvas.height);
     }
}
```

----

### 实现玩家显示功能

毛坯版玩家显示，每个玩家定义成一个圆，然后渲染在前端

需要对于玩家类定义多个参数，以方便日后拓展：

1. `x` 当前位置的横坐标
2. `y` 当前位置的纵坐标
3. `radius` 当前的半径
4. `speed` 当前的速度
5. `is_me`该对象是否是当前玩家操控的对象（一是区别于 bot，二是区别于 日后联机的其他玩家）



`static/js/playground/zbase.js`

```javascript
class AcGamePlayground {
    constructor(root) {
        ......
        this.players = [];  // 存放当前游戏中的所有玩家
        //将玩家加入游戏中
        this.players.push(new Player(this, this.width / 2, this.height / 2, this.height * 0.05, "white", this.height * 0.15, true));
        ......
    }
    .....
}
```



`static/js/playground/player/zbase.js`

```javascript
class Player extends AcGameObject {
    constructor(playground, x, y, radius, color, speed, is_me) {
        super();
        //把信息都存下来
        this.playground = playground;
        this.ctx = this.playground.game_map.ctx;
        this.x = x;
        this.y = y;
        this.color = color;
        this.speed = speed;
        this.radius = radius;
        this.is_me = is_me;
        //用于浮点数运算
        this.eps = 0.1;
    }
    start() {
    }
    update() {
        this.render();
    }
    render() {  //渲染一个圆
        this.ctx.beginPath();
        this.ctx.arc(this.x, this.y, this.radius, 0, 2 * Math.PI, false);
        this.ctx.fillStyle = this.color;
        this.ctx.fill();
    }
    on_destroy() {
    }
}
```

---

### 实现玩家移动功能

移动的实现逻辑很简单，就是让每帧渲染的圆的位置发生移动即可

上述简单逻辑的实现如下：



`static/js/playground/player/zbase.js`

```javascript
class Player extends AcGameObject {
    constructor(....)
    {
        ...
        this.vx = 1;
        this.vy = 1;
        ...
    }
    ...
    update() {
        this.x += x;
        this.y += y;
        this.render();
    }
}
```

然后我们来实现一个向鼠标点击位置移动的功能

这就需要设置一个 `click` 事件的监听函数，分别传递：

1. 鼠标点击事件
2. 鼠标点击位置的横坐标
3. 鼠标点击位置的纵坐标

然后开始让圆的位置逐步向鼠标点击位置进行移动

```
start() {
    if (this.is_me) {   //对于用户玩家，加上监听函数
        this.add_listening_events();
    }
}
add_listening_events() {
    let outer = this;
    //把鼠标右键调出菜单栏的功能关掉
    this.playground.game_map.$canvas.on("contextmenu", function() {
        return false;
    });
    //把右键控制移动功能加上
    this.playground.game_map.$canvas.mousedown(function(e) {
        // 左键:1 中键:2 右键:3
        if (e.which === 3) {
            outer.move_to(e.clientX, e.clientY);
        }
    });
}
```

然后，我们来实现移动功能的函数 `move_to(tx, ty)`

```
constructor(...){
    ...
    this.vx = 0;    //x方向上的移动速度
    this.vy = 0;    //y方向上的移动速度
    this.move_length = 0;   //剩余移动距离
    ...
}
...
get_dist (x1, y1, x2, y2) { //求两点的欧几里得距离
    let dx = x2 - x1;
    let dy = y2 - y1;
    return Math.sqrt(dx * dx + dy * dy);
}
move_to(tx, ty) {
    // 计算移动距离
    this.move_length = this.get_dist(this.x, this.y, tx, ty);
    // 计算移动角度，api接口：atan2(dy, dx)
    let angle = Math.atan2(ty - this.y, tx - this.x);
    // 位移 1 个单位长度（向着矢量方向移动到单位圆上）
    this.vx = Math.cos(angle);  //极直互化
    this.vy = Math.sin(angle);
}
update() {
    //浮点数精度运算
    if (this.move_length < this.eps) {
        this.move_length = 0;
        this.vx = this.vy = 0;
    } else {
        // 计算单位帧里的移动距离
        let moved = Math.min(this.move_length, this.speed * this.timedelta / 1000);
        this.x += this.vx * moved;
        this.y += this.vy * moved;
        // 还要减掉移动的距离
        this.move_length -= moved;
    }
    this.render();
}
...
```

---

### 实现火球技能的功能

火球对象的建立与玩家基本一致，直接照搬，在从细节上改改即可



`js/src/playground/skill/fireball/zbase.js`

```javascript
class FireBall extends AcGameObject {
    constructor(playground, player, x, y, radius, vx, vy, color, speed, move_length, damage) {
        super();
        this.playground = playground;
        this.ctx = this.playground.game_map.ctx;
        this.player = player;
        this.x = x;
        this.y = y;
        this.vx = vx;
        this.vy = vy;
        this.radius = radius;
        this.color = color;
        this.speed = speed;
        this.move_length = move.length;
        this.damage = damage;
        this.eps = 0.1;
    }
    start() {

    }
    update() {
        if (this.move_length < this.eps) {
            this.destroy();
            return false;
        } else {
            let moved = Math.min(this.move_length, this.speed * this.timedelta / 1000);
            this.x += this.vx * moved;
            this.y += this.vy * moved;
            this.move_length -= moved;
        }
        this.render();
    }
    render() {
        this.ctx.beginPath();
        this.ctx.arc(this.x, this.y, this.radius, 0, 2 * Math * Pi, false);
        this.ctx.fillStyle = this.color;
        this.ctx.fill();
    }

} 
```


然后在玩家身上实现发火球的功能

基本实现逻辑：当前选中了火球技能，鼠标左键点击一处，向该处发射一个火球

因此，为了知道用户是否选择了技能，需要加一个键盘触发事件监听函数，然后加一个鼠标左键触发事件监听函数

然后发射一个火球即可



`js/src/playground/player/zbase.js`

```javascript
constructor(...) {
    ...
    this.cur_skill = null;  //记录当前选择的技能
    ...
}
add_listening_events() {
    ...
    this.playground.game_map.$canvas.mousedown(function(e) {
        // 左键:1 中键:2 右键:3
        if (e.which === 3) {
            outer.move_to(e.clientX, e.clientY);
        } else if (e.which === 1) {     //鼠标左键事件
            if (outer.cur_skill === "fireball") {   //当前已经选中火球技能
                outer.shoot_fireball(e.clientX, e.clientY);
            }
        }
        outer.cur_skill = null; //清空当前技能
    });
    $(window).keydown(function(e) {
        if (e.which === 81) {       //键盘按下事件
            outer.cur_skill = "fireball";
            return false;
        }
    });
}
shoot_fireball(tx, ty) {
    //确定火球的参数
    let x = this.x, y = this.y; //火球发射点就是当前玩家的位置
    let radius = this.playground.height * 0.01;
    let angle = Math.atan2(ty - this.y, tx - this.x);
    let vx = Math.cos(angle), vy = Math.sin(angle);
    let color = "orange";
    let speed = this.playground.height * 0.5;
    let move_length = this.playground.height * 1.0;
    let damage = this.playground.height * 0.01;
    new FireBall(this.playground, this, x, y, radius, vx, vy, color, speed, move_length, damage);
}
```



这样就成功实现了玩家发射火球的功能了

---

### 实现单人模式下的人机功能

先创建好 5 个人机

`playground/zbase.js`

```javascript
//创建好 5 个人机
for (len i = 0; i < 5; i ++ ) {
    this.players.push(new Player(this, this.width / 2, this.height / 2, this.height * 0.05, "blue", this.height * 0.15, false));
}
```


这样创建出来的 5 个人机是不会行动的

我们写一个简易的 Ai 程序，让他们也会移动

这里实现的逻辑是：每次随机一个目的地，向目的地移动，然后再随机一个目的地，循环下去

根据该逻辑，修改两个函数即可



`playground/player/zbase.js`

```javascript
...
start() {
    if (this.is_me) {   //对于用户玩家，加上监听函数
        this.add_listening_events();
    } else {
        let tx = Math.random() * this.playground.width;
        let ty = Math.random() * this.playground.height;
        this.move_to(tx, ty);
    }
}
...
 update() {
    if (this.move_length < this.eps) {
        this.move_length = 0;
        this.vx = this.vy = 0;
        if (!this.is_me) {   //如果是人机，停下来时再随机一个方向前进
            let tx = Math.random() * this.playground.width;
            let ty = Math.random() * this.playground.height;
            this.move_to(tx, ty);
        }
    }
    ...
}
on_destroy() {
    for (let i = 0; i < this.playground.players.length; i ++ ) {
        if (this.playground.players[i] === this) {
            this.playground.players.splice(i, 1);
        }
    }
}
```

---

### 实现技能命中效果（碰撞检测功能）

实现逻辑：检测两个圆的中心距离是否小于两个圆的半径之和

小于等于时，代表发生碰撞，开始执行命中效果：

1. 被击中用户掉血
2. 被击中用户收到向后击退效果

碰撞检测写在火球类里，击退效果写在玩家类里



`fireball/zbase.js`

```javascript
update() {
    if (...) {
        ...
    } else {
        ...

        // 碰撞检测
        for (let i = 0; i < this.playground.players.length; i ++ ) {
            let player = this.playground.players[i];
            if (this.player !== player && this.is_collision(player)) {  // 碰撞发生一定是在非施法者身上
                this.attack(player);    //火球命中，目标玩家执行击退效果
            }
        }
    }
    this.render();

}
get_dist(x1, y1, x2, y2) {  //获得两点的欧几里得距离
        let dx = x2 - x1;
        let dy = y2 - y1;
        return Math.sqrt(dx * dx + dy * dy);
    }
is_collision(player) {  //检测两个圆的中心距离是否小于两个圆的半径之和
    let distance = this.get_dist(this.x, this.y, player.x, player.y);
    if (distance < (this.radius + player.radius))
        return true;
    return false;
}
attack(player) {    //火球命中，目标玩家执行击退效果
    let angle = Math.atan2(player.y - this.y, player.x - this.x);   //计算角度
    player.is_attacked(angle, this.damage); //火球命中，目标玩家执行击退效果
    this.destroy(); //火球命中后，自然消失
}
```


写击退效果时，有几个细节要注意

被击退的时候，原来的移动速度应该置为 0，当前的移动应该转为向被击中方向上的移动



`player/zbase.js`

```javascript
is_attacked(angle, damage) {
    this.radius -= damage;  //受伤，半径减少
    if (this.radius < 10) { //当半径小于10像素时，代表死亡
        this.destroy();
        return false;
    }
    //开始执行击退效果
    this.damage_vx = Math.cos(angle);
    this.damage_vy = Math.sin(angle);
    this.damage_speed = damage * 100;

    this.speed *= 0.5;  //被击中以后移动速度减半

}
update() {
    if (this.damage_speed > this.eps) {   //当前仍处于击退效果中
        this.vx = this.vy = 0;
        this.move_length = 0;
        this.x += this.damage_vx * this.damage_speed * this.timedelta / 1000;
        this.y += this.damage_vy * this.damage_speed * this.timedelta / 1000;
        this.damage_speed *= this.friction; // 击退速度乘以摩擦系数，已达到削减的目的
    } else {
        ...
    }
    ...
}
```

---

### 被击中以后的粒子效果特效

实现逻辑：被击中以后，在玩家附近随机生成一些粒子小球

因此我们要先实现 `粒子小球` 对象

`static/js/src/playground/particle/zbase.js`

```javascript
class Particle extends AcGameObject {
    constructor(playground, x, y, radius, vx, vy, color, speed) {
        super();
        this.playground = playground;
        this.ctx = this.playground.game_map.ctx;
        this.x = x;
        this.y = y;
        this.radius = radius;
        this.vx = vx;
        this.vy = vy;
        this.color = color;
        this.speed = speed;
        this.friction = 0.9;
    }
    start() {
    }
    update() {
        if (this.speed < this.eps) {
            this.destroy;
            return false;
        }
        this.x += this.vx * this.speed * this.timedelta / 1000;
        this.y += this.vy * this.speed * this.timedelta / 1000;
        this.speed *= this.friction;
        this.render();
    }
    render() {
        this.ctx.beginPath();
        this.ctx.arc(this.x, this.y, this.radius, 0, 2 * Math.PI, false);
        this.ctx.fillStyle = this.color;
        this.ctx.fill();
    }
} 
```




然后我们在被击退功能模块，实现生成粒子小球的效果

* 粒子小球释放弧度为 [0,2π)的随机数
* 粒子小球的 x, y 分量比率根据弧度来设定
* 粒子小球的起始坐标应与玩家的坐标相同
* 粒子小球的颜色与玩家颜色相同
* 粒子小球的速度为玩家移动速度的 10倍

`js/src/playground/player/zbase.js`

```javascript
is_attacked(angle, damage) {
    // 粒子小球效果
    for (let i = 0; i < 10 + Math.random() * 5; i ++ ) {
        let x = this.x, y = this.y;
        let radius = this.radius * Math.random() * 0.1;
        let angle = 2 * Math.PI * Math.random();
        let vx = Math.cos(angle), vy = Math.sin(angle);
        let color = this.color;
        let speed = this.speed * 10;
        new Particle(this.playground, x, y, radius, vx, vy, color, speed);
    }
    ...
}
```

---

### 一些小优化

#### 人机随机颜色

`js/src/playground/zbase.js`

```javascript
constructor(root) {
    ......
    //创建好 5 个人机
    for (let i = 0; i < 5; i ++ ) {
        this.players.push(new Player(this, this.width / 2, this.height / 2, this.height * 0.05, this.get_random_color(), this.height * 0.15, false));
    }
    ......
}
get_random_color() {
    let colors = ["blue", "red", "pink", "grey", "green"];
    return colors[Math.floor(Math.random() * 5)];
}
```



#### 人机AI随机攻击操作

`js/src/playground/player/zbase.js`

```javascript
constructor (...) {
    ...
    this.spent_time = 0;    // 初始人机冷却攻击时间
}
...
update() {
    this.spent_time += this.timedelta / 1000;
    if (!this.is_me && this.spent_time > 4 && Math.random() * 180 < 1) {
        let player = this.playground.players[Math.floor(Math.random() * this.playground.players.length)];
        this.shoot_fireball(player.x, player.y);
}
```



## 5. 部署nginx与对接acapp

### 1. 增加容器的映射端口：80与443

第一步，登录容器，关闭所有运行中的任务。



第二步，登录运行容器的服务器，然后执行：

```bash
docker commit CONTAINER_NAME django_lesson:1.1  # 将容器保存成镜像，将CONTAINER_NAME替换成容器名称
docker stop CONTAINER_NAME  # 关闭容器
docker rm CONTAINER_NAME # 删除容器

# 使用保存的镜像重新创建容器
docker run -p 20000:22 -p 8000:8000 -p 80:80 -p 443:443 --name CONTAINER_NAME -itd django_lesson:1.1
```

如果不小心命名错了，可以用 `docker rename CONTAINER_NAME 你想要的新名字` 来重命名



第三步，去云服务器控制台，在安全组配置中开放80和443端口。

* 先删掉这两个端口
  * ![屏幕截图 2025-07-28 094219.png](https://cdn.acwing.com/media/article/image/2025/07/28/504252_25bc00ef6b-%E5%B1%8F%E5%B9%95%E6%88%AA%E5%9B%BE-2025-07-28-094219.png)

* 之后添加这两个端口，具体操作可以参考本文前几段配置服务器的部分
  * ![屏幕截图 2025-07-28 094645.png](https://cdn.acwing.com/media/article/image/2025/07/28/504252_c796ae786b-%E5%B1%8F%E5%B9%95%E6%88%AA%E5%9B%BE-2025-07-28-094645.png)



在完成上述步骤后，我们无需再配置免密登陆。原因是：**我们已经把之前的容器变成镜像，变成的镜像里是有之前容器的配置文件的**



登上服务器，在tmux里执行`python3 manage.py runserver 0.0.0.0:8000`, 看看是否正常运行。

---

### 2. 创建AcApp，获取域名、nginx配置文件及https证书

* 打开[AcWing应用中心](https://www.acwing.com/file_system/file/content/whole/index/content/whole/application/1/)，点击“创建应用”的按钮，进入下图所示界面。

![屏幕截图 2025-07-28 100314.png](https://cdn.acwing.com/media/article/image/2025/07/28/504252_0ec913b36b-%E5%B1%8F%E5%B9%95%E6%88%AA%E5%9B%BE-2025-07-28-100314.png)

* 在`服务器IP`一栏填入自己服务器的ip地址。

* 为了保证vim和tmux的配置不变，应先执行`sudo cp .vimrc .tmux.conf /root/`。该命令的目的是：将当前用户的Vim和tmux配置文件复制到root用户的主目录中，这样root用户也能使用相同的配置。

* 将`django-nginx.conf`中的内容写入服务器`/etc/nginx/nginx.conf`文件中。如果django项目路径与配置文件中不同，注意修改路径。

* 将`acapp.key`中的内容写入服务器`/etc/nginx/cert/acapp.key`文件中。

* 将`acapp.pem`中的内容写入服务器`/etc/nginx/cert/acapp.pem`文件中。

* 然后启动nginx服务：

  ```bash
  sudo /etc/init.d/nginx start
  ```

  * 完成后可以看到OK标志![屏幕截图 2025-07-28 104124.png](https://cdn.acwing.com/media/article/image/2025/07/28/504252_8a50fce06b-%E5%B1%8F%E5%B9%95%E6%88%AA%E5%9B%BE-2025-07-28-104124.png)

---

### 3. 修改django项目的配置

* `cd /acapp/acapp`, 进入到当前目录下的`settings`
  * 打开`settings.py`文件：将分配的域名添加到`ALLOWED_HOSTS`列表中。注意只需要添加`https://`后面的部分。![屏幕截图 2025-07-28 110335.png](https://cdn.acwing.com/media/article/image/2025/07/28/504252_869215846b-%E5%B1%8F%E5%B9%95%E6%88%AA%E5%9B%BE-2025-07-28-110335.png)
  * 令`DEBUG = False`。![屏幕截图 2025-07-28 105649.png](https://cdn.acwing.com/media/article/image/2025/07/28/504252_9e9a2cb76b-%E5%B1%8F%E5%B9%95%E6%88%AA%E5%9B%BE-2025-07-28-105649.png)

* 在 `/acapp` 下, 执行`python3 manage.py collectstatic`

---

### 4. 配置uwsgi

在`django`项目中添加`uwsgi`的配置文件：`scripts/uwsgi.ini`，内容如下：

```
[uwsgi]
socket          = 127.0.0.1:8000
chdir           = /home/acs/acapp
wsgi-file       = acapp/wsgi.py
master          = true
processes       = 2
threads         = 5
vacuum          = true
```

启动uwsgi服务(先关闭刚刚的runserver服务)：

```
uwsgi --ini scripts/uwsgi.ini
```

---

### 5. 填写应用的剩余信息

* 标题：应用的名称
* 关键字：应用的标签（选填）
* css地址：css文件的地址，例如：https://app76.acapp.acwing.com.cn/static/css/game.css
* js地址：js文件的地址：例如：https://app76.acapp.acwing.com.cn/static/js/dist/game.js
* 主类名：应用的main class，例如AcGame。
* 图标：4:3的图片
* 应用介绍：介绍应用，支持markdown + latex语法。

---

### 6. 使分配的域名生效

填写完服务器IP之后，点“保存”或者“提交”按钮，均可使分配的域名生效。

---

### 7. 提交后点”打开应用”按钮，即可预览自己所写的应用

---

### 8. 发布应用

---

### 9. 修复bug

**在完成上述步骤以后，我们在acapp里打开游戏，发现坐标出现了bug。只有当我们把acapp的窗口拖到屏幕左上角时才可正常移动小球。接下来我们修复一下这个bug。**



#### 修改`player`类

`/home/acs/acapp/game/static/js/src/playground/player/zbase.js`

注意：文件路径开头是在`game`下，不是`acapp`下。我一开始改错了，还没找到问题在哪，甚至还把这个docker删了，整个重新来了一遍。。。

```javascript
add_listening_events() {
        let outer = this;
        this.playground.game_map.$canvas.on("contextmenu", function() {
            return false;
        });
        this.playground.game_map.$canvas.mousedown(function (e) {
            const rect = outer.ctx.canvas.getBoundingClientRect(); // <-----修复bug

            if (e.which === 3){//移动功能
                outer.move_to(e.clientX - rect.left, e.clientY - rect.top);// <-----修复bug
            }else if(e.which === 1){
                if(outer.cur_skill == "fireball"){
                    outer.shoot_fireball(e.clientX - rect.left, e.clientY - rect.top);
                }
                outer.cur_skill = null;
            }
        });
```

---

### 10. 变美观

#### 修改压缩`js`代码的`shell`文件

`/home/acs/acapp/scripts/compress_game_js.sh`

```shell
#! /bin/bash

JS_PATH=/home/acs/acapp/game/static/js/
JS_PATH_DIST=${JS_PATH}dist/
JS_PATH_SRC=${JS_PATH}src/

find $JS_PATH_SRC -type f -name '*.js' | sort | xargs cat > ${JS_PATH_DIST}game.js

echo yes | python3 /home/acs/acapp/manage.py collectstatic // <-----加上这一行
```

---

#### 修改`AcGamePlayground`类

把计算画布宽高挪到了`show()`之后。

```javascript
class AcGamePlayground{
    constructor(root){
        this.root = root;
        this.$playground =$(`<div class="ac-game-playground"></div>`);
        
        this.hide();

        this.start();
    }

    get_random_color(){
        let colors = ["blue", "red", "pink", "grey", "green"];
        return colors[Math.floor(Math.random() * 5)];
    }

    start(){
    
    }


    show(){ // 打开playground界面
        this.$playground.show();
        this.root.$ac_game.append(this.$playground);
        //存下来宽高
        this.width = this.$playground.width();
        this.height = this.$playground.height();
        this.game_map = new GameMap(this);
        this.players = [];
        this.players.push(new Player(this, this.width / 2, this.height / 2, this.height * 0.05, "white", this.height * 0.15, true));

        for(let i = 0 ; i < 5 ; i ++){
            this.players.push(new Player(this, this.width / 2, this.height / 2, this.height * 0.05, this.get_random_color(), this.height * 0.15, false));
        }
    }
    
    hide(){ // 关闭playground界面
        this.$playground.hide();
    }

}
```

---

#### 修改`css`

```css
.ac-game-menu-field {
    width: 20vw;
    position: relative;
    top: 30%;
    left: 17%;
}

.ac-game-menu-field-item {
    color: #e4e4e7;
    height: 7vh;
    width: 14vw;
    font-size: 3.3vh;
    font-weight: 400;
    font-family: 'Inter', 'Roboto', sans-serif;
    padding: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, rgba(25, 25, 35, 0.6), rgba(35, 35, 45, 0.5));
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    letter-spacing: 0.15vw;
    cursor: pointer;
    text-transform: uppercase;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.4),
                inset 0 1px 0 rgba(255, 255, 255, 0.06);
    backdrop-filter: blur(12px);
    position: relative;
    overflow: hidden;
    transition: all 0.2s ease;
    margin-bottom: 0.5vh;
}
```



## 6.1 用户名密码登录

### 前期准备工作

做开发，先开启调试模式，如果不开启，服务器一旦运行错误，就只返回`Error` 报错



`/home/acs/acapp/acapp/settings.py`

```python
...
DEBUG = True
...
```



如果忘记自己之前创建的管理员账号，可以重新创建一个超级用户，方便进入到后台管理 admin 页面

```bash
$ python3 manage.py createsuperuser
...

```

然后登陆到管理员页面：`http://xxxxx/admin/`



不过 `django` 自带的 `User` 表并不能满足我们的需求，因此我们需要自己额外建表

---

### 创建用户表

所有的数据表都存在 `models` 里

我们在 `models` 里创建一个 `player` 文件夹，用于存储所有的 `player` 相关的表

然后对文件夹初始化 `__init__.py`，接着扩充成一个我们需要的数据表



`\acapp\game\models\player\player.py`

```python
# 从Django的数据库模块导入models，这是创建数据库模型的基础
from django.db import models
# 从Django的认证系统导入User模型，这是Django内置的用户模型
from django.contrib.auth.models import User

# 定义一个Player类，继承自models.Model
# 这会在数据库中创建一个名为"player"的表（Django会自动转换为小写）
class Player(models.Model):
    # 创建一个一对一关系字段，将Player模型与Django内置的User模型关联
    # OneToOneField表示：一个User只能对应一个Player，一个Player也只能对应一个User
    # on_delete=models.CASCADE表示：当关联的User被删除时，对应的Player也会被自动删除
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    # 创建一个URL字段，用于存储玩家头像的网址
    # max_length=256：URL的最大长度为256个字符
    # blank=True：在Django表单中，这个字段可以为空（不是必填项）
    # 注意：blank=True只影响表单验证，数据库层面仍然允许NULL值
    photo = models.URLField(max_length=256, blank=True)

    # 定义模型的字符串表示方法
    # 当你打印Player对象或在Django admin中显示时，会显示关联的用户名
    # 例如：如果user.username是"张三"，那么这个Player对象就会显示为"张三"
    def __str__(self):
        return str(self.user)
```



将定义的表，注册到后台 `admin` 页面中

`\acapp\game\admin.py`

```python
# 从Django的管理后台模块导入admin
# admin模块提供了Django自带的管理界面功能
from django.contrib import admin

# 从你的项目中导入Player模型
# 这个路径表示：game应用 -> models文件夹 -> player文件夹 -> player.py文件中的Player类
from game.models.player.player import Player

# Register your models here. (在这里注册你的模型)
# 将Player模型注册到Django管理后台
# 注册后，你就可以在Django admin界面中对Player数据进行增删改查操作
admin.site.register(Player)
```



然后将创建的数据表更新到 `django` 的数据库中去

```bash
$ python3 manage.py makemigrations
> Migrations for 'game':
>   game/migrations/0001_initial.py
>     - Create model Player
$ 
$ python3 manage.py migrate
> Operations to perform:
>   Apply all migrations: admin, auth, contenttypes, game, sessions
> Running migrations:
>   Applying game.0001_initial... OK
```



重新启动服务，即可在管理员界面看到: 

![屏幕截图 2025-07-29 135501.png](https://cdn.acwing.com/media/article/image/2025/07/29/504252_99b9bc806c-%E5%B1%8F%E5%B9%95%E6%88%AA%E5%9B%BE-2025-07-29-135501.png)

---

### 实现客户端的类型判别（ACAPP or WEB）

由于我们实现的项目是前后端分离类型，因此对于不同的客户端，前端要控制生成不同的页面

为了增强扩展性，故这里要实现客户端类型的判别

y总 已经提前写好了 **ACAPP** 的接口，如果用户用的是 **ACAPP** 访问，则在新建对象 **ac_game** 时，会额外传递一个参数

我们只需按照这个接口去完成扩充即可

>  之后写小程序之类的同理，额外传一个接口



`js/zbase.js`

```javascript
export class AcGame {
    constructor(id, AcWingOS) {
        this.id = id;
        this.$ac_game = $('#' + id);

        this.AcWingOS = AcWingOS;   //如果是acapp端，该变量就会带着一系列y总提供的接口

        this.menu = new AcGameMenu(this);
        this.playground = new AcGamePlayground(this);

        this.start();
    }
    start() {

    }
}
```

---

### 构建登录功能框架

基本逻辑 : 用户访问页面 -> 进入登录页面 -> 提交登录信息 -> 核对登录信息 -> 返回登陆结果和其他信息

每实现一个函数，就需要实现三个部分：

1. `views` : 实现具体的调用数据库的逻辑

2. `urls` : 实现一个路由

3. `js` : 前端实现GET上述接口的过程

   

欲实现流程 :

1.  用户访问网站，通过先前完成的路由，访问到 `web.html`
2.  `web.html` 中的 `js` 部分创建了一个 `AcGame` 对象
3.  `AcGame` 对象创建的过程中，生成了 `Settings` 对象
4.  `Settings` 对象创建完成后，调用 `Settings.start()` 函数
5.  `Settings.start()` 函数调用了 `Settings.getinfo()` 函数
6.  `Settings.getinfo()` 函数中执行了 `ajax` 向 `getinfo` 接口发起一个含参数 `platform` 的 `GET` 请求
7.  通过 `urls` 路由的实现，最终定位到 `views/settings/getinfo.py` 文件的 `getinfo(request)` 函数
8.  根据传递过来的 `platform` 函数，实现不同的 `JsonResponse` 返回
9.  `Settings.getinfo()` 接受到了 `response` 完成上述基本逻辑



#### views

`views/settings/getinfo.py`

```python
from django.http import JsonResponse
from game.models.player.player import Player

def getinfo_acapp(request):
    player = Player.objects.all()[0]    # 取出数据库中第一个用户(调试该功能)
    return JsonResponse({
        'result': "success",
        'username': player.user.username,
        'photo': player.photo,
    })

def getinfo_web(request):
    player = Player.objects.all()[0]    # 取出数据库中第一个用户(调试该功能)
    return JsonResponse({
        'result': "success",
        'username': player.user.username,
        'photo': player.photo,
    })

def getinfo(request):   # 处理请求
    platform = request.GET.get('platform')  # 根据请求的平台不同，进行不同返回处理
    if platform == "ACAPP":
        return getinfo_acapp(request)
    elif platform == "WEB":
        return getinfo_web(request)
```

---

#### urls

`urls/settings/index.py`

```python
from django.urls import path
from game.views.settings.getinfo import getinfo

urlpatterns = [
    path("getinfo/", getinfo, name="settings_getinfo"),
]
```



路由建立好以后，访问 `xxxx/settings/getinfo`，可以看到 `getinfo.py` 返回的`JSON` 类型的 `JSONResponse`

```json
{"result": "success", "username": "admin", "photo": "https://cdn.acwing.com/media/user/profile/photo/504252_lg_f82193bb5a.png"}
```

---

#### js

网页刚访问时，应先将 `menu` 关闭，然后打开登录界面，随意先修改一个让 `menu` 初始关闭

`static/js/src/menu/zbase.js`

```javascript
class AcGameMenu {
    constructor(root) {
        ...
        this.$menu.hide();
        ...
    }
    ...
```



`static/js/src/settings/zbase.js`

```javascript
class Settings {
    constructor(root) {
        this.root = root;
        this.platform = "WEB";
        if (this.root.AcWingOS) this.platform = "ACAPP";
        this.start();
    }
    start() {
        this.getinfo();
    }
    register() {    //打开注册界面
    }
    login() {       //打开登录界面
    }
    getinfo() {
        let outer = this;
        $.ajax({
            url: "https://app1117.acapp.acwing.com.cn/settings/getinfo/",
            type: "GET",
            data: {
                platform: outer.platform,
            },
            success: function(resp) {
                console.log(resp);
                if (resp.result === "success") {    //登录成功，关闭登录界面，打开主菜单
                    outer.hide();
                    outer.root.menu.show();
                } else {
                    outer.login();
                }
            }
        });
    }
    hide() {
    }
    show() {
    }
}
```



然后不要忘记在 `根js` 下创建对象



`static/js/zbase.js`

```javascript
export class AcGame {
    constructor(id, AcWingOS) {
        ...
        this.settings = new Settings(this);
        ...
    }
    ...
}
```

这样基本框架就完成了

---

#### 完善 `HTTP` 请求的函数

如果用户未登录，返回信息 “not login”；如果用户登录，返回信息 “success” 以及用户名和头像



`views/setting/getinfo.py`

```javascript
def getinfo_web(request):
    user = request.user
    if not user.is_authenticated:   # 未登录
        return JsonResponse({
            'result': "not login"
        })
    else:                           # 已登录
        player = Player.objects.all()[0]
        return JsonResponse({
            'result': "success",
            'username': player.user.username,
            'photo': player.photo,
        })
```

> 注意前后台是一个登录系统，因此要先退掉后台，才测试

---

### 将用户头像渲染到玩家上

将返回的 `JsonResponse` 存到 `Settings` 类的变量中



`settings/zbase.js`

```javascript
class Settings {
    constructor(root) {
        ...
        this.username = "";
        this.photo = "";
        ...
    }
    ...
    getinfo() {
        let outer = this;
        $.ajax({
            ...
            success: function(resp) {
                ...
                if (resp.result === "success") {
                    outer.username = resp.username;
                    outer.photo = resp.photo;
                    ...
                }
                ..
            }
        });
    }
}
```



然后在 `Player` 里把用户的头像渲染到对应的玩家上

`playground/player/zbase.js`

```javascript
class Player {
    constructor(...) {
        ...
        this.img = new Image();
        this.img.src = this.playground.root.settings.photo;
    }
    ...
    render() {
        if (this.is_me) {
            this.ctx.save();
            this.ctx.beginPath();
            this.ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2, false);
            this.ctx.stroke();
            this.ctx.clip();
            this.ctx.drawImage(this.img, this.x - this.radius, this.y - this.radius, 
                               this.radius * 2, this.radius * 2);
            this.ctx.restore();
        } else {
            this.ctx.beginPath();
            this.ctx.arc(this.x, this.y, this.radius, 0, 2 * Math.PI, false);
            this.ctx.fillStyle = this.color;
            this.ctx.fill();
        }
    }
    ...
}
```

---

### 实现登录界面的前端

先完成登录界面显示的逻辑



`settings/zbase.js`

```javascript
class Settings {
    ...
    register() {  // 打开注册界面
        this.$login.hide();
        this.$register.show();
    }

    login() {  // 打开登录界面
        this.$register.hide();
        this.$login.show();
    }
    ...
    hide() {
        this.$settings.hide();
    }

    show() {
        this.$settings.show();
    }
}
```



#### 实现前端的基础框架

`settings/zbase.js`

```javascript
class Settings {
    constructor(root) {
        ...
        this.$settings = $(`
<div class="ac-game-settings">
    <div class="ac-game-settings-login">
        <div class="ac-game-settings-title">
            登录
        </div>
        <div class="ac-game-settings-username">
            <div class="ac-game-settings-item">
                <input type="text" placeholder="用户名">
            </div>
        </div>
        <div class="ac-game-settings-password">
            <div class="ac-game-settings-item">
                <input type="password" placeholder="密码">
            </div>
        </div>
        <div class="ac-game-settings-submit">
            <div class="ac-game-settings-item">
                <button>登录</button>
            </div>
        </div>
        <div class="ac-game-settings-error-message">
        </div>
        <div class="ac-game-settings-option">
            注册
        </div>
        <br>
        <div class="ac-game-settings-acwing">
            <img width="30" src="https://app165.acapp.acwing.com.cn/static/image/settings/acwing_logo.png">
            <br>
            <div>
                AcWing一键登录
            </div>
        </div>
    </div>
    <div class="ac-game-settings-register">
        <div class="ac-game-settings-title">
            注册
        </div>
        <div class="ac-game-settings-username">
            <div class="ac-game-settings-item">
                <input type="text" placeholder="用户名">
            </div>
        </div>
        <div class="ac-game-settings-password ac-game-settings-password-first">
            <div class="ac-game-settings-item">
                <input type="password" placeholder="密码">
            </div>
        </div>
        <div class="ac-game-settings-password ac-game-settings-password-second">
            <div class="ac-game-settings-item">
                <input type="password" placeholder="确认密码">
            </div>
        </div>
        <div class="ac-game-settings-submit">
            <div class="ac-game-settings-item">
                <button>注册</button>
            </div>
        </div>
        <div class="ac-game-settings-error-message">
        </div>
        <div class="ac-game-settings-option">
            登录
        </div>
        <br>
        <div class="ac-game-settings-acwing">
            <img width="30" src="https://app165.acapp.acwing.com.cn/static/image/settings/acwing_logo.png">
            <br>
            <div>
                AcWing一键登录
            </div>
        </div>
    </div>
</div>
`);
        this.$login = this.$settings.find(".ac-game-settings-login");
        this.$login_username = this.$login.find(".ac-game-settings-username input");
        this.$login_password = this.$login.find(".ac-game-settings-password input");
        this.$login_submit = this.$login.find(".ac-game-settings-submit button");
        this.$login_error_message = this.$login.find(".ac-game-settings-error-message");
        this.$login_register = this.$login.find(".ac-game-settings-option");

        this.$login.hide();

        this.$register = this.$settings.find(".ac-game-settings-register");
        this.$register_username = this.$register.find(".ac-game-settings-username input");
        this.$register_password = this.$register.find(".ac-game-settings-password-first input");
        this.$register_password_confirm = this.$register.find(".ac-game-settings-password-second input");
        this.$register_submit = this.$register.find(".ac-game-settings-submit button");
        this.$register_error_message = this.$register.find(".ac-game-settings-error-message");
        this.$register_login = this.$register.find(".ac-game-settings-option");

        this.$register.hide();

        this.root.$ac_game.append(this.$settings);
        ...
    }
    ...
}
```



对应的 `css` 文件部分：



`css/game.css`

y总代码

```css
.ac-game-settings {
    width: 100%;
    height: 100%;
    background-image: url("/static/image/menu/background.gif");
    background-size: 100% 100%;
    user-select: none;
}

.ac-game-settings-login {
    height: 41vh;
    width: 20vw;
    position: relative;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    background-color: rgba(0, 0, 0, 0.7);
    border-radius: 5px;
}

.ac-game-settings-title {
    color: white;
    font-size: 3vh;
    text-align: center;
    padding-top: 2vh;
    margin-bottom: 2vh;
}

.ac-game-settings-username {
    display: block;
    height: 7vh;
}

.ac-game-settings-password {
    display: block;
    height: 7vh;
}

.ac-game-settings-submit {
    display: block;
    height: 7vh;
}

.ac-game-settings-acwing {
    display: block;
    height: 7vh;
}

.ac-game-settings-item {
    width: 100%;
    height: 100%;
}

.ac-game-settings-item > input {
    width: 90%;
    line-height: 3vh;
    position: relative;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
}

.ac-game-settings-item > button {
    color: white;
    width: 90%;
    line-height: 3vh;
    position: relative;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    background-color: #4CAF50;
    border-radius: 5px;
}

.ac-game-settings-error-message {
    color: red;
    font-size: 0.8vh;
    display: inline;
    float: left;
    padding-left: 1vw;
}

.ac-game-settings-option {
    color: white;
    font-size: 2vh;
    display: inline;
    float: right;
    padding-right: 1vw;
    cursor: pointer;
}

.ac-game-settings-acwing > img {
    position: relative;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    cursor: pointer;
    display: block;
}

.ac-game-settings-acwing > div {
    color: white;
    font-size: 1.5vh;
    text-align: center;
    display: block;
}

.ac-game-settings-register {
    height: 49vh;
    width: 20vw;
    position: relative;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    background-color: rgba(0, 0, 0, 0.7);
    border-radius: 5px;
}
```



我觉得y总的css效果不是很好，所以自己借助ai写了一个，大家可以参考一下。（登陆页面和游戏菜单界面的风格是类似的）

```css
.ac-game-settings {
    width: 100%;
    height: 100%;
    background-image: url("/static/image/menu/background.gif");
    background-size: 100% 100%;
    user-select: none;
}

.ac-game-settings-login {
    height: 41vh;
    width: 17vw;
    position: relative;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    background: linear-gradient(135deg, rgba(25, 25, 35, 0.8), rgba(35, 35, 45, 0.7));
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4),
                inset 0 1px 0 rgba(255, 255, 255, 0.06);
    backdrop-filter: blur(12px);
    overflow: hidden;
}

.ac-game-settings-title {
    color: #e4e4e7;
    font-size: 3vh;
    font-weight: 400;
    font-family: 'Inter', 'Roboto', sans-serif;
    text-align: center;
    padding-top: 2vh;
    margin-bottom: 2vh;
    text-transform: uppercase;
    letter-spacing: 0.15vw;
    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
}

.ac-game-settings-username {
    display: block;
    height: 7vh;
    margin: 0 1vw;
}

.ac-game-settings-password {
    display: block;
    height: 7vh;
    margin: 0 1vw;
}

.ac-game-settings-submit {
    display: block;
    height: 7vh;
    margin: 0 1vw;
}

.ac-game-settings-acwing {
    display: block;
    height: 7vh;
    margin: 0 1vw;
}

.ac-game-settings-item {
    width: 100%;
    height: 100%;
    position: relative;
}

.ac-game-settings-item > input {
    width: 90%;
    height: 3.7vh;
    line-height: 1.4;  /* 使用较小的行高 */
    padding: 0.5vh 1vw; /* 添加适当的上下内边距 */
    box-sizing: border-box; /* 确保padding计算在总高度内 */
    position: relative;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    color: #e4e4e7;
    font-family: 'Inter', 'Roboto', sans-serif;
    font-size: 0.9em; /* 可以适当调整字体大小 */
    transition: all 0.2s ease;
    backdrop-filter: blur(8px);
}

.ac-game-settings-item > input:focus {
    outline: none;
    border-color: rgba(255, 255, 255, 0.3);
    background: rgba(255, 255, 255, 0.08);
    box-shadow: 0 0 16px rgba(243, 156, 18, 0.1),
                inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

.ac-game-settings-item > input::placeholder {
    color: rgba(228, 228, 231, 0.5);
}

.ac-game-settings-item > button {
    color: #e4e4e7;
    width: 90%;
    line-height: 3vh;
    position: relative;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    background: linear-gradient(135deg, rgba(52, 152, 219, 0.8), rgba(41, 128, 185, 0.7));
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 8px;
    font-family: 'Inter', 'Roboto', sans-serif;
    font-weight: 400;
    text-transform: uppercase;
    letter-spacing: 0.1vw;
    cursor: pointer;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.4),
                inset 0 1px 0 rgba(255, 255, 255, 0.1);
    transition: all 0.2s ease;
    overflow: hidden;
}

.ac-game-settings-item > button::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg,
                transparent,
                rgba(255, 255, 255, 0.1),
                rgba(255, 255, 255, 0.2),
                rgba(255, 255, 255, 0.1),
                transparent);
    transition: left 0.5s ease;
}

.ac-game-settings-item > button:hover {
    transform: translate(-50%, -50%) translateY(-2px);
    background: linear-gradient(135deg, rgba(52, 152, 219, 0.9), rgba(41, 128, 185, 0.8));
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.5),
                0 0 24px rgba(52, 152, 219, 0.2),
                inset 0 1px 0 rgba(255, 255, 255, 0.2);
}

.ac-game-settings-item > button:hover::before {
    left: 100%;
}

.ac-game-settings-item > button:active {
    transform: translate(-50%, -50%);
    background: linear-gradient(135deg, rgba(41, 128, 185, 0.8), rgba(52, 152, 219, 0.7));
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.5),
                inset 0 2px 4px rgba(0, 0, 0, 0.3);
}

.ac-game-settings-error-message {
    color: #ef4444;
    font-size: 1vh;
    font-family: 'Inter', 'Roboto', sans-serif;
    display: inline;
    float: left;
    padding-left: 2vw;
    padding-top: 0.72vh;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
}

.ac-game-settings-option {
    color: #e4e4e7;
    font-size: 1.7vh;
    font-family: 'Inter', 'Roboto', sans-serif;
    display: inline;
    float: right;
    padding-right: 2.0vw;
    cursor: pointer;
    transition: all 0.2s ease;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
}

.ac-game-settings-option:hover {
    color: #ffffff;
    text-decoration: underline;
    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.8);
}

.ac-game-settings-acwing {
    display: block;
    height: 7vh;
    margin: 0 1vw;
    position: absolute;  /* 改为绝对定位 */
    bottom: 0;          /* 贴底 */
    left: 0;            /* 左对齐 */
    right: 0;           /* 右对齐 */
}

.ac-game-settings-acwing > img {
    position: absolute;
    top: 30%;           /* 调整位置，让图标在div内合适的位置 */
    left: 50%;
    transform: translate(-50%, -50%);
    cursor: pointer;
    display: block;
    transition: all 0.2s ease;
    filter: brightness(0.9);
    width: auto;
    height: auto;
    max-height: 3.5vh;
    max-width: 90%;
}

.ac-game-settings-acwing > img:hover {
    transform: translate(-50%, -50%) scale(1.05);
    filter: brightness(1.1) drop-shadow(0 4px 8px rgba(0, 0, 0, 0.5));
}

.ac-game-settings-acwing > div {
    color: #e4e4e7;
    font-size: 1.3vh;
    font-family: 'Inter', 'Roboto', sans-serif;
    text-align: center;
    display: block;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
    position: absolute;
    bottom: 15%;
    left: 50%;
    transform: translateX(-50%);
    white-space: nowrap;
}

.ac-game-settings-register {
    height: 49vh;
    width: 17vw;
    position: relative;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    background: linear-gradient(135deg, rgba(25, 25, 35, 0.8), rgba(35, 35, 45, 0.7));
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.06);
    backdrop-filter: blur(12px);
    overflow: hidden;
}

.ac-game-menu {
    width: 100%;
    height: 100%;
    background-image: url("/static/image/menu/background.gif");
    background-size: 100% 100%;
    user-select: none;
}

/*注释起来的是yxc的代码，我觉得效果不太好，就让ai重新写了一个，放在后面了*/
/*.ac-game-menu-field{*/
/*    width: 20vw;*/
/*    position: relative;*/
/*    top: 40vh;*/
/*    left: 19vw;*/
/*}*/

/*.ac-game-menu-field-item {*/
/*    color: white;*/
/*    height: 7vh;*/
/*    width: 18vw;*/
/*    font-size: 5vh;*/
/*    font-style: italic;*/
/*    padding: 1.3vh;*/
/*    text-align: center;*/
/*    background-color: rgba(39,21,28, 0.6);*/
/*    border-radius: 10px;*/
/*    letter-spacing: 0.4vw;*/
/*    cursor: pointer;*/
/*}*/

/*.ac-game-menu-field-item:hover {*/
/*    transform: scale(1.2);*/
/*    transition: 150ms;*/
/*}*/


.ac-game-menu-field {
    width: 20vw;
    position: relative;
    top: 20%;
    left: 17%;
}

.ac-game-menu-field-item {
    color: #e4e4e7;
    height: 7vh;
    width: 12vw;
    font-size: 3.3vh;
    font-weight: 400;
    font-family: 'Inter', 'Roboto', sans-serif;
    padding: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, rgba(25, 25, 35, 0.6), rgba(35, 35, 45, 0.5));
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    letter-spacing: 0.15vw;
    cursor: pointer;
    text-transform: uppercase;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.4),
                inset 0 1px 0 rgba(255, 255, 255, 0.06);
    backdrop-filter: blur(12px);
    position: relative;
    overflow: hidden;
    transition: all 0.2s ease;
    margin-bottom: 1.7vh;
}

.ac-game-menu-field-item::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg,
                transparent,
                rgba(255, 255, 255, 0.03),
                rgba(255, 255, 255, 0.06),
                rgba(255, 255, 255, 0.03),
                transparent);
    transition: left 0.5s ease;
}

.ac-game-menu-field-item::after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 0;
    width: 0;
    height: 2px;
    background: linear-gradient(90deg, #f39c12, #e74c3c);
    transition: width 0.3s ease;
}

.ac-game-menu-field-item:hover {
    transform: translateY(-2px);
    color: #ffffff;
    background: linear-gradient(135deg, rgba(30, 30, 40, 0.7), rgba(40, 40, 50, 0.6));
    border-color: rgba(255, 255, 255, 0.2);
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.5),
                0 0 24px rgba(243, 156, 18, 0.1),
                inset 0 1px 0 rgba(255, 255, 255, 0.1);
    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
}

.ac-game-menu-field-item:hover::before {
    left: 100%;
}

.ac-game-menu-field-item:hover::after {
    width: 100%;
}

.ac-game-menu-field-item:active {
    transform: translateY(0);
    background: linear-gradient(135deg, rgba(25, 25, 35, 0.7), rgba(35, 35, 45, 0.6));
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.5),
                inset 0 2px 4px rgba(0, 0, 0, 0.3);
}

.ac-game-menu-field-item:last-child {
    margin-bottom: 0;  /* 最后一个按钮不需要底部间距 */
}

/* 可选：为不同按钮添加不同的强调色 */
.ac-game-menu-field-item:nth-of-type(1):hover::after {
    background: linear-gradient(90deg, #3498db, #2980b9);
}

.ac-game-menu-field-item:nth-of-type(2):hover::after {
    background: linear-gradient(90deg, #51cb18, #2f4e2f);
}

.ac-game-menu-field-item:nth-of-type(3):hover::after {
    background: linear-gradient(90deg, #95a5a6, #7f8c8d);
}

.ac-game-menu-field-item:nth-of-type(4):hover::after {
    background: linear-gradient(90deg, #b85151, #b11f09);
}

/**/
.ac-game-playground{
    width: 100%;
    height: 100%;
    user-select: none;
}
```



#### 实现登录/注册的相互切换

```css
class Settings {
    constructor(root) {
        ...
    }
    start() {
        this.getinfo();
        this.add_listening_events();
    }
    add_listening_events() {
        this.add_listening_events_login();
        this.add_listening_events_register();
    }
    add_listening_events_login() {
        let outer = this;
        this.$login_register.click(function() {
            outer.register();   //跳到注册界面
        });
    }
    add_listening_events_register() {
        let outer = this;
        this.$register_login.click(function() {
            outer.login();      //跳到登录界面
        })
    }
    ...
}
```

---

### 实现登录功能



`views/settings/login.py`

```python
from django.http import JsonResponse
from django.contrib.auth import authenticate, login

def signin(request):
    data = request.GET
    username = data.get('username')
    password = data.get('password')
    user = authenticate(username=username, password=password)
    if not user:
        return JsonResponse({
            'result': "用户名或密码不正确"
        })
    login(request, user)
    return JsonResponse({
        'result': "success"
    })
```



`urls/settings/index.py`

```python
from django.urls import path
from game.views.settings.getinfo import getinfo
from game.views.settings.login import signin

urlpatterns = [
    path("getinfo/", getinfo, name="settings_getinfo"),
    path("login/", signin, name="settings_login"),
]
```



`settings/zbase.js`

```javascript
class Settings{
    ...
    add_listening_events_login() {
        ...
        this.$login_submit.click(function() {
            outer.login_on_remote();
        });
    }
    ...
    login_on_remote() {     //在远程服务器上登录
        let outer = this;
        let username = this.$login_username.val();
        let password = this.$login_password.val();
        this.$login_error_message.empty();
        $.ajax({
            url: "https://app1117.acapp.acwing.com.cn/settings/login/",
            type: "GET",
            data: {
                username: username,
                password: password,
            },
            success: function(resp) {
                console.log(resp);
                if (resp.result === "success") {
                    location.reload();
                } else {
                    outer.$login_error_message.html(resp.result);
                }
            }
        });
    }
}
```

---

### 实现登出功能



`views/settings/register.py`

```python
from django.http import JsonResponse
from django.contrib.auth import logout

def signout(request):
    user = request.user
    if not user.is_authenticated:
        return JsonResponse({
            'result': "success",
        })
    logout(request)
    return JsonResponse({
        'result': "success",
    })
```



`urls/settings/index.py`

```python
...
from game.views.settings.logout import signout
urlpatterns = [
    ...
    path("logout/", signout, name="settings_logout"),
]
```



`settings/zbase.js`

```javascript
...
login_on_remote() {     //在远程服务器上登录
    let outer = this;
    let username = this.$login_username.val();
    let password = this.$login_password.val();
    this.$login_error_message.empty();

    $.ajax({
        url: "https://app1117.acapp.acwing.com.cn/settings/login/",
        type: "GET",
        data: {
            username: username,
            password: password,
        },
        success: function(resp) {
            console.log(resp);
            if (resp.result === "success") {
                location.reload();
            } else {
                outer.$login_error_message.html(resp.result);
            }
        }
    });
}
...
```



再顺便将 `menu` 菜单页面里的 `设置` 按钮也绑定上登出功能



`menu/zbase.js`

```javascript
add_listening_events() {
    let outer = this;
    ...
    this.$settings_mode.click(function() {
        ...
        outer.root.settings.logout_on_remote();
    });
}
```

---

### 实现注册功能

`views/settings/register.py`

```python
from django.http import JsonResponse
from django.contrib.auth import login
from django.contrib.auth.models import User
from game.models.player.player import Player

def register(request):
    data = request.GET
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    password_confirm = data.get("password_confirm", "").strip()

    if not username or not password:
        return JsonResponse({
            'result': "用户名或密码不能为空",
        })
    if password != password_confirm:
        return JsonResponse({
            'result': "两个密码不一致",
        })
    if User.objects.filter(username=username).exists():
        return JsonResponse({
            'result': "用户名已存在",
        })
    user = User(username=username)
    user.set_password(password)
    user.save()
    Player.objects.create(user=user, photo="https://cdn.acwing.com/media/user/profile/photo/42832_lg_f999efc3c8.png")
    login(request, user)
    return JsonResponse({
        'result': "success",
    })
```



`urls/settings/index.py`

```python
...
from game.views.settings.register import register
...
urlpatterns = [
    ...
    path("register/", register, name="settings_register"),
]
```



`settings/zbase.js`

```javascript
...
add_listening_events_register() {
    ...
    this.$register_submit.click(function() {
        outer.register_on_remote();
    });
}
...
register_on_remote() {  //在远程服务器上注册
    let outer = this;
    let username = this.$register_username.val();
    let password = this.$register_password.val();
    let password_confirm = this.$register_password_confirm.val();
    this.$register_error_message.empty();

    $.ajax({
        url: "https://app1117.acapp.acwing.com.cn/settings/register/",
        type: "GET",
        data: {
            username: username,
            password: password,
            password_confirm: password_confirm,
        },
        success: function(resp) {
            console.log(resp);
            if (resp.result === "success") {
                location.reload();
            } else {
                outer.$register_error_message.html(resp.result);
            }
        }
    })
}
...
```

---

## 6.2 web端AcWing一键登录

业务流程如下所示：

![img](https://cdn.acwing.com/media/article/image/2021/11/25/1_1ddf070e4d-weboauth2.png)

### 在Django中集成Redis

#### 1. 安装 `django_redis`

`pip install django_redis`

#### 2. 配置 `settings.py`

```python
CACHES = { 
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },  
    },  
}
USER_AGENTS_CACHE = 'default'
```

#### 3. 启动`redis-server`

`sudo redis-server /etc/redis/redis.conf`



在 `django` 后台里操纵 `reids`

```shell
$ python3 manage.py shell

In [1]: from django.core.cache import cache # 引入redis

In [2]: cache.keys('*')                     # 查询redis里所有的关键字
Out[2]: []

In [3]: cache.set('yxc', 1, 5)              # 插入一个key-val，存在 5 s
Out[3]: True

In [4]: cache.keys('*')                     # 查询redis里所有的关键字
Out[4]: ['yxc']

In [5]: cache.set('yxc', 2, None)           # 插入一个key-val，不会过期
Out[5]: True

In [6]: cache.set('abc', 3, None)
Out[6]: True

In [7]: cache.keys('y*')
Out[7]: ['yxc']

In [8]: cache.has_key('abc')
Out[8]: True

In [9]: cache.has_key('abcd')
Out[9]: False

In [10]: cache.get('yxc')
Out[10]: 2

In [11]: cache.delete('yxc')
Out[11]: True

In [12]: cache.keys('*')
Out[12]: ['abc']

In [13]:
```

---

### 扩充Player表

为了实现一键登录，需要额外存储一个 `openid` 来标识每一个 `Player` 绑定的 `AcWing` 账号



`models/player.py`

```python
...
class Player(models.Model):
    ...
    openid = models.CharField(default="", max_length=256, blank=True, null=True)
    ...
```



然后更新数据库：

```python
$ python3 manage.py makemigrations
$ python3 manage.py migrate
```

---

### 申请授权码code

请求地址：`https://www.acwing.com/third_party/api/oauth2/web/authorize/`



**参考示例**：

```
请求方法：GET
https://www.acwing.com/third_party/api/oauth2/web/authorize/?appid=APPID&redirect_uri=REDIRECT_URI&scope=SCOPE&state=STATE
```



**参数说明**


| 参数         | 是否必须 | 说明                                                         |
| ------------ | -------- | ------------------------------------------------------------ |
| appid        | 是       | 应用的唯一id，可以在AcWing编辑AcApp的界面里看到              |
| redirect_uri | 是       | 接收授权码的地址。需要用 `urllib.parse.quote` 对链接进行处理 |
| scope        | 是       | 申请授权的范围。目前只需填 `userinfo`                        |
| state        | 否       | 用于判断请求和回调的一致性，授权成功后后原样返回。该参数可用于防止csrf攻击（跨站请求伪造攻击），建议第三方带上该参数，可设置为简单的随机数 |



**返回说明**

用户同意授权后会重定向到 `redirect_uri` ，返回参数为 `code` 和 `state` 。 链接格式如下：

```
redirect_uri?code=CODE&state=STATE
```

如果用户拒绝授权，则不会发生重定向。



##### views

> 创建新的 `views` 和 `urls` 时不要忘记初始化一个 `__init__.py` 文件



`views/settings/acwing/web/apply_code.py`

```python
from django.http import JsonResponse
from urllib.parse import quote
from random import randint
from django.core.cache import cache

def get_state():    # 随机8位数字
    res = ""
    for i in range(8):
        res += str(randint(0, 9))
    return res

def apply_code(request):
    # 传递的四个参数
    appid = "1117"
    redirect_uri = quote("https://app1117.acapp.acwing.com.cn/settings/acwing/web/receive_code/")
    scope = "userinfo"
    state = get_state()

    cache.set(state, True, 7200)    # 把随机的状态码存入 redis 中，有效期 2 小时

    apply_code_url = "https://www.acwing.com/third_party/api/oauth2/web/authorize/"

    return JsonResponse({
        'result': "success",
        'apply_code_url': apply_code_url + "?appid=%s&redirect_uri=%s&scope=%s&state=%s" % (appid, redirect_uri, scope, state)
    })
```



`views/settings/acwing/web/receive_code.py`

```python
from django.shortcuts import redirect

def receive_code(request):
    return redirect("index")
```

---

##### urls

创建一个新的文件夹，然后建立路由

`urls/settings/index.py`

```python
from django.urls import path, include
...

urlpatterns = [
    ...
    path("acwing/", include("game.urls.settings.acwing.index")),
]
```



`urls/settings/acwing/index.py`

```python
from django.urls import path
from game.views.settings.acwing.web.apply_code import apply_code
from game.views.settings.acwing.web.receive_code import receive_code


urlpatterns = [
    path("web/apply_code/", apply_code, name="settings_acwing_web_apply_code"),
    path("web/receive_code/", receive_code, name="settings_acwing_web_receive_code"),
]
```

---

##### js

`js/settings/zbase.js`

```javascript
class Settings{
    constructor(...) {
        ...
        this.$acwing_login = this.$settings.find('.ac-game-settings-acwing img'); 
        ...
    }
    ...
    add_listening_events() {
        let outer = this;
        ...
        this.$acwing_login.click(function() {
            outer.acwing_login();
        });
    }
    acwing_login() {
        $.ajax({
            url: "https://app1117.acapp.acwing.com.cn/settings/acwing/web/apply_code/",
            type: "GET",
            success: function(resp) {
                console.log(resp);
                if (resp.result === "success") {
                    window.location.replace(resp.apply_code_url);
                }
            }
        })
    } 
}
```

---

### 申请授权令牌 `access_token` 和用户的 `openid`

请求地址：`https://www.acwing.com/third_party/api/oauth2/access_token/`



**参考示例**：

```
请求方法：GET
https://www.acwing.com/third_party/api/oauth2/access_token/?appid=APPID&secret=APPSECRET&code=CODE
```



**参数说明**

| 参数   | 是否必须 | 说明                                            |
| ------ | -------- | ----------------------------------------------- |
| appid  | 是       | 应用的唯一id，可以在AcWing编辑AcApp的界面里看到 |
| secret | 是       | 应用的秘钥，可以在AcWing编辑AcApp的界面里看到   |
| code   | 是       | 第一步中获取的授权码                            |


**返回说明**

申请成功示例：

```
{ 
    "access_token": "ACCESS_TOKEN", 
    "expires_in": 7200, 
    "refresh_token": "REFRESH_TOKEN",
    "openid": "OPENID", 
    "scope": "SCOPE",
}
```

申请失败示例：

```
{
    "errcode": 40001,
    "errmsg": "code expired",  # 授权码过期
}
```



**返回参数说明**

| 参数          | 说明                                                         |
| ------------- | ------------------------------------------------------------ |
| access_token  | 授权令牌，有效期2小时                                        |
| expires_in    | 授权令牌还有多久过期，单位（秒）                             |
| refresh_token | 用于刷新access_token的令牌，有效期30天                       |
| openid        | 用户的id。每个AcWing用户在每个acapp中授权的openid是唯一的,可用于识别用户。 |
| scope         | 用户授权的范围。目前范围为userinfo，包括用户名、头像         |


**刷新access_token的有效期**

`access_token` 的有效期为2小时，时间较短。`refresh_token` 的有效期为30天，可用于刷新 `access_token`。刷新结果有两种：

如果 `access_token` 已过期，则生成一个新的 `access_token` 。
如果 `access_token` 未过期，则将当前的 `access_token` 的有效期延长为2小时。



**参考示例**：

```
请求方法：GET
https://www.acwing.com/third_party/api/oauth2/refresh_token/?appid=APPID&refresh_token=REFRESH_TOKEN
```

返回结果的格式与申请 access_token 相同。



##### views

`views/settings/acwing/web/receive_code.py`

```python
from django.shortcuts import redirect
from django.core.cache import cache
import requests

def receive_code(request):
    data = request.GET
    code = data.get('code')
    state = data.get('state')

    if not cache.has_key(state):
        return redirect("index")
    cache.delete(state)

    apply_access_token_url = "https://www.acwing.com/third_party/api/oauth2/access_token/"
    params = {
        'appid': "1117",
        'secret': "79021fb1f2344bb6a191237ece84d874",
        'code': code
    }
    access_token_res = requests.get(apply_access_token_url, params=params).json()

    print(access_token_res)

    return redirect("index")
```

---

### 申请用户信息

请求地址：`https://www.acwing.com/third_party/api/meta/identity/getinfo/`



**参考示例**：

请求方法：GET

```
请求方法：GET
https://www.acwing.com/third_party/api/meta/identity/getinfo/?access_token=ACCESS_TOKEN&openid=OPENID
```



**参数说明**

| 参数         | 是否必须 | 说明                     |
| ------------ | -------- | ------------------------ |
| access_token | 是       | 第二步中获取的授权令牌   |
| openid       | 是       | 第二步中获取的用户openid |



**返回说明**

申请成功示例：

```json
{
    'username': "USERNAME",
    'photo': "https:cdn.acwing.com/xxxxx"
}
```

申请失败示例：

```json
{
    'errcode': "40004",
    'errmsg': "access_token expired"  # 授权令牌过期
}
```



##### views

`views/settings/acwing/web/receive_code.py`

```python
from django.shortcuts import redirect
from django.core.cache import cache
from django.contrib.auth.models import User
from game.models.player.player import Player
from django.contrib.auth import login
from random import randint
import requests

def receive_code(request):
    data = request.GET
    code = data.get('code')
    state = data.get('state')

    if not cache.has_key(state):
        return redirect("index")
    cache.delete(state)

    apply_access_token_url = "https://www.acwing.com/third_party/api/oauth2/access_token/"
    params = {
        'appid': "1117",
        'secret': "79021fb1f2344bb6a191237ece84d874",
        'code': code
    }
    access_token_res = requests.get(apply_access_token_url, params=params).json()

    access_token = access_token_res['access_token']
    openid = access_token_res['openid']

    players = Player.objects.filter(openid=openid)
    if players.exists():    # 如果acw账户对应用户已经存在，直接登录
        login(request, players[0].user)
        return redirect("index")

    get_userinfo_url = "https://www.acwing.com/third_party/api/meta/identity/getinfo/"
    params = {
        "access_token": access_token,
        "openid": openid
    }
    userinfo_res = requests.get(get_userinfo_url, params=params).json()
    username = userinfo_res['username']
    photo = userinfo_res['photo']

    while User.objects.filter(username=username).exists():  # 如果重名，额外添加数字填充
        username += str(randint(0, 9))

    user = User.objects.create(username=username)
    player = Player.objects.create(user=user, photo=photo, openid=openid)

    login(request, user)

    return redirect("index")
```

---

### 整体流程分析：

#### 🎭 先用个比喻理解 OAuth2

想象你要参加一个高端酒店的派对：

- **你** = 用户
- **你的应用** = 派对入口的接待处
- **AcWing** = 派对主办方（他们有你的会员信息）
- **授权码(code)** = 临时通行证
- **access_token** = 正式入场券

---

#### 📋 整个流程分解

##### 第一步：用户点击"AcWing登录"按钮

```javascript
// 用户点击登录按钮
acwing_login() {
    $.ajax({
        url: ".../apply_code/",  // 请求我们自己的后端
        ...
    })
}
```

**发生了什么**：

- 用户说："我想用 AcWing 账号登录你的网站"
- 你的前端 JS 先访问**你自己的后端**（不是 AcWing）

##### 第二步：你的后端准备跳转链接

```python
def apply_code(request):
    state = get_state()  # 生成随机码，像个"暗号"
    cache.set(state, True, 7200)  # 存起来，一会儿要验证
    
    # 构造 AcWing 的授权页面地址
    apply_code_url = "https://www.acwing.com/.../authorize/?..."
    return JsonResponse({
        'apply_code_url': apply_code_url
    })
```

**这一步做了什么**：

1. 生成一个随机的 `state`（防止 CSRF 攻击，像个一次性暗号）
2. 把这个暗号存到 Redis（2小时有效）
3. 告诉前端："你该去 AcWing 的授权页面了，地址我给你准备好了"

##### 第三步：浏览器跳转到 AcWing

```javascript
window.location.replace(resp.apply_code_url);
```

**用户体验**：

- 浏览器跳转到 AcWing 网站
- 页面显示："某某应用想要获取你的用户信息，是否同意？"
- 用户点击"同意"

##### 第四步：AcWing 跳回你的网站

用户同意后，AcWing 会让浏览器跳转回你的网站：

```
https://你的网站/receive_code/?code=临时授权码&state=之前的暗号
```

##### 第五步：你的后端接收授权码

```python
def receive_code(request):
    code = data.get('code')    # AcWing 给的临时授权码
    state = data.get('state')  # 之前的暗号
    
    # 验证暗号对不对
    if not cache.has_key(state):
        return redirect("index")  # 暗号不对，可能是攻击
```

**为什么要验证 state**：

- 确保这个请求是刚才我们发起的
- 防止恶意网站伪造请求

##### 第六步：用授权码换取 access_token

```python
# 拿着授权码去 AcWing 换取正式的访问令牌
params = {
    'appid': "1117",
    'secret': "你的密钥",  # 证明你是合法应用
    'code': code           # 刚拿到的授权码
}
access_token_res = requests.get(access_token_url, params=params).json()

access_token = access_token_res['access_token']  # 正式令牌
openid = access_token_res['openid']              # 用户在你应用中的唯一ID
```

**这步很关键**：

- `code` 只能用一次，用完就失效
- `secret` 必须保密，证明你是真正的应用开发者
- 获得 `access_token` 后就能访问用户信息了

##### 第七步：获取用户信息

```python
# 用 access_token 获取用户详细信息
params = {
    "access_token": access_token,
    "openid": openid
}
userinfo_res = requests.get(get_userinfo_url, params=params).json()
username = userinfo_res['username']
photo = userinfo_res['photo']
```

##### 第八步：创建或登录用户

```python
# 检查这个 AcWing 用户是否已经在我们网站注册过
players = Player.objects.filter(openid=openid)
if players.exists():
    # 老用户，直接登录
    login(request, players[0].user)
else:
    # 新用户，创建账号
    user = User.objects.create(username=username)
    player = Player.objects.create(user=user, photo=photo, openid=openid)
    login(request, user)
```

---

#### 🔄 完整流程图

```
用户点击登录 
    ↓
你的网站生成 state 并构造 AcWing 授权链接
    ↓
浏览器跳转到 AcWing（带着你的 appid 和 state）
    ↓
用户在 AcWing 上同意授权
    ↓
AcWing 跳转回你的网站（带着 code 和 state）
    ↓
你的后端验证 state 
    ↓
你的后端用 code + secret 换取 access_token
    ↓
你的后端用 access_token 获取用户信息
    ↓
创建/登录用户，完成！
```

---

#### 💡 关键概念理解

1. **为什么这么麻烦？**
   - 安全！用户的密码永远不会泄露给第三方应用
   - AcWing 可以随时撤销授权
2. **state 的作用**：
   - 防止 CSRF 攻击
   - 像是你和 AcWing 之间的"暗号"
3. **code vs access_token**：
   - code：一次性的，很快过期
   - access_token：可以用 2 小时，用来真正获取数据
4. **openid 的意义**：
   - 同一个 AcWing 用户在不同应用中的 openid 不同
   - 保护用户隐私



## 6.2.1 拓展：尝试做GitHub一键登录

### 📝 准备工作

#### 第一步：在 GitHub 上注册 OAuth 应用

1. **登录你的 GitHub 账号**

2. **进入设置页面**：

   - 点击右上角头像 → Settings
   - 左侧菜单最下方找到 "Developer settings"
   - 点击 "OAuth Apps" → "New OAuth App"

3. **填写应用信息**：

   ```
   Application name: 你的应用名称（比如 "My Django Game"）
   Homepage URL: https://你的域名.com
   Application description: 可选的描述
   Authorization callback URL: https://你的域名.com/settings/github/web/receive_code/
   ```

4. **创建后你会得到**：

   - `Client ID`（相当于 AcWing 的 appid）
   - `Client Secret`（点击生成，相当于 AcWing 的 secret）

⚠️ **重要**：记下这两个值，特别是 Client Secret 只显示一次！

### 🏗️ 开始实现

#### 第二步：更新 Player 模型

既然要支持多种登录方式，我们需要改进一下数据库设计：

```python
# models/player/player.py
class Player(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    photo = models.URLField(max_length=256, blank=True)
    openid = models.CharField(default="", max_length=256, blank=True, null=True)
    
    # 新增字段来支持多平台登录
    github_id = models.CharField(default="", max_length=256, blank=True, null=True)
    github_username = models.CharField(default="", max_length=256, blank=True, null=True)
```

运行数据库迁移：

```bash
python3 manage.py makemigrations
python3 manage.py migrate
```

#### 第三步：创建 GitHub 登录的视图

先创建目录结构：

```
views/settings/github/
├── __init__.py
└── web/
    ├── __init__.py
    ├── apply_code.py
    └── receive_code.py
```

##### 1. apply_code.py

```python
# views/settings/github/web/apply_code.py
from django.http import JsonResponse
from urllib.parse import quote
from django.core.cache import cache
from django.conf import settings
import secrets

def get_state():
    """生成安全的随机状态码"""
    return secrets.token_urlsafe(32)

def apply_code(request):
    # GitHub OAuth 参数
    client_id = settings.GITHUB_CLIENT_ID  # 从配置读取，不要硬编码！
    redirect_uri = quote(settings.GITHUB_REDIRECT_URI)
    scope = "user"  # GitHub 的权限范围
    state = get_state()
    
    # 保存 state 到缓存
    cache.set(f"github_state_{state}", True, 600)  # 10分钟有效
    
    # GitHub 的授权地址
    authorize_url = "https://github.com/login/oauth/authorize"
    
    return JsonResponse({
        'result': "success",
        'apply_code_url': f"{authorize_url}?client_id={client_id}&redirect_uri={redirect_uri}&scope={scope}&state={state}"
    })
```

现在，让我们在 `settings.py` 中添加配置：

```python
# settings.py
import os

# GitHub OAuth 配置
GITHUB_CLIENT_ID = os.environ.get('GITHUB_CLIENT_ID', '你的Client ID')
GITHUB_CLIENT_SECRET = os.environ.get('GITHUB_CLIENT_SECRET', '你的Client Secret')
GITHUB_REDIRECT_URI = "https://你的域名/settings/github/web/receive_code/"
```

💡 **提醒**：生产环境一定要用环境变量，不要把密钥写在代码里！

#### 第四步：处理 GitHub 的回调

##### 2. receive_code.py

这是最核心的部分，我们一段一段来写：

```python
# views/settings/github/web/receive_code.py
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
```

#### 第五步：配置 URL 路由

```python
# urls/settings/github/index.py
from django.urls import path
from game.views.settings.github.web.apply_code import apply_code
from game.views.settings.github.web.receive_code import receive_code

urlpatterns = [
    path("web/apply_code/", apply_code, name="settings_github_web_apply_code"),
    path("web/receive_code/", receive_code, name="settings_github_web_receive_code"),
]
```

在主路由中添加：

```python
# urls/settings/index.py
urlpatterns = [
    path("acwing/", include("game.urls.settings.acwing.index")),
    path("github/", include("game.urls.settings.github.index")),  # 新增
]
```

#### 第六步：前端添加 GitHub 登录按钮

```javascript
// js/settings/zbase.js
class Settings {
    constructor() {
        // ...
        this.$github_login = this.$settings.find('.ac-game-settings-github img');
        this.add_listening_events();
    }
    
    add_listening_events() {
        let outer = this;
        // ...
        this.$github_login.click(function() {
            outer.github_login();
        });
    }
    
    github_login() {
        $.ajax({
            url: "/settings/github/web/apply_code/",
            type: "GET",
            success: function(resp) {
                console.log(resp);
                if (resp.result === "success") {
                    window.location.replace(resp.apply_code_url);
                }
            },
            error: function(xhr, status, error) {
                console.error("GitHub 登录失败:", error);
                alert("GitHub 登录暂时不可用，请稍后重试");
            }
        });
    }
}
```

#### 第七步：添加 HTML 按钮

在你的登录界面 HTML 中添加：

```html
<div class="ac-game-settings-github">
    <img src="GitHub 登录按钮图片地址" alt="GitHub Login">
    <span>使用 GitHub 登录</span>
</div>
```

### 🎯 主要区别总结

GitHub 和 AcWing OAuth 的主要区别：

1. **授权地址不同**：
   - AcWing: `https://www.acwing.com/third_party/api/oauth2/web/authorize/`
   - GitHub: `https://github.com/login/oauth/authorize`

2. **获取 token 的方式**：
   - AcWing: GET 请求
   - GitHub: POST 请求，需要特殊的 Accept header

3. **用户信息 API**：
   - AcWing: 需要传 openid
   - GitHub: 只需要 Authorization header

4. **权限范围(scope)**：
   - AcWing: `userinfo`
   - GitHub: `user` 或 `read:user`



## 6.2.2 拓展：尝试做Gitee一键登录

### 🚀 实现 Gitee 登录

#### 步骤1：注册 Gitee OAuth 应用

1. 登录 [Gitee.com](https://gitee.com)

2. 点击右上角头像 → **设置**

3. 左侧菜单找到 **第三方应用**

4. 点击 **创建应用**

5. 填写信息：

   ```
   应用名称：你的游戏名称
   应用主页：https://app7549.acapp.acwing.com.cn
   应用回调地址：https://app7549.acapp.acwing.com.cn/settings/gitee/web/receive_code/
   权限：勾选 user（获取用户信息）
   ```

6. 创建后记下 **Client ID** 和 **Client Secret**

#### 步骤2：更新 Player 模型

```python
# models/player/player.py
class Player(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    photo = models.URLField(max_length=256, blank=True)
    openid = models.CharField(default="", max_length=256, blank=True, null=True)
    
    # GitHub 字段
    github_id = models.CharField(default="", max_length=256, blank=True, null=True)
    github_username = models.CharField(default="", max_length=256, blank=True, null=True)
    
    # Gitee 字段（新增）
    gitee_id = models.CharField(default="", max_length=256, blank=True, null=True)
    gitee_username = models.CharField(default="", max_length=256, blank=True, null=True)

    def __str__(self):
        return str(self.user.username)
```

运行迁移：

```bash
python3 manage.py makemigrations
python3 manage.py migrate
```

#### 步骤3：添加 Gitee 配置

```python
# settings.py
# Gitee OAuth 配置
GITEE_CLIENT_ID = os.environ.get('GITEE_CLIENT_ID', '你的_Gitee_Client_ID')
GITEE_CLIENT_SECRET = os.environ.get('GITEE_CLIENT_SECRET', '你的_Gitee_Client_Secret')
```

#### 步骤4：创建 Gitee 视图

创建目录结构：

```
game/views/settings/gitee/
├── __init__.py
└── web/
    ├── __init__.py
    ├── apply_code.py
    └── receive_code.py
```

**apply_code.py**

```python
# views/settings/gitee/web/apply_code.py
from django.http import JsonResponse
from urllib.parse import quote
from django.core.cache import cache
from django.conf import settings
import secrets

def apply_code(request):
    """申请 Gitee 授权码"""
    # Gitee OAuth 参数
    client_id = settings.GITEE_CLIENT_ID
    redirect_uri = quote("https://app7549.acapp.acwing.com.cn/settings/gitee/web/receive_code/")
    state = secrets.token_urlsafe(32)
    
    # 保存 state 到缓存
    cache.set(f"gitee_state_{state}", True, 600)  # 10分钟有效
    
    # Gitee 的授权地址
    authorize_url = "https://gitee.com/oauth/authorize"
    
    return JsonResponse({
        'result': "success",
        'apply_code_url': f"{authorize_url}?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&state={state}"
    })
```

**receive_code.py**

```python
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
            'redirect_uri': "https://app7549.acapp.acwing.com.cn/settings/gitee/web/receive_code/",
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
```

#### 步骤5：配置 URL 路由

```python
# urls/settings/gitee/index.py
from django.urls import path
from game.views.settings.gitee.web.apply_code import apply_code
from game.views.settings.gitee.web.receive_code import receive_code

urlpatterns = [
    path("web/apply_code/", apply_code, name="settings_gitee_web_apply_code"),
    path("web/receive_code/", receive_code, name="settings_gitee_web_receive_code"),
]
```

在主路由添加：

```python
# urls/settings/index.py
from django.urls import path, include

urlpatterns = [
    path("acwing/", include("game.urls.settings.acwing.index")),
    path("github/", include("game.urls.settings.github.index")),
    path("gitee/", include("game.urls.settings.gitee.index")),  # 新增
]
```

#### 步骤6：前端添加 Gitee 登录按钮

```javascript
// js/settings/zbase.js
class Settings {
    constructor() {
        // ...
        this.$acwing_login = this.$settings.find('.ac-game-settings-acwing img');
        this.$github_login = this.$settings.find('.ac-game-settings-github img');
        this.$gitee_login = this.$settings.find('.ac-game-settings-gitee img'); // 新增
        
        this.add_listening_events();
    }
    
    add_listening_events() {
        let outer = this;
        
        // AcWing 登录
        this.$acwing_login.click(function() {
            outer.acwing_login();
        });
        
        // GitHub 登录
        this.$github_login.click(function() {
            outer.github_login();
        });
        
        // Gitee 登录（新增）
        this.$gitee_login.click(function() {
            outer.gitee_login();
        });
    }
    
    // Gitee 登录方法
    gitee_login() {
        $.ajax({
            url: "/settings/gitee/web/apply_code/",
            type: "GET",
            success: function(resp) {
                console.log(resp);
                if (resp.result === "success") {
                    window.location.replace(resp.apply_code_url);
                }
            },
            error: function(xhr, status, error) {
                console.error("Gitee 登录失败:", error);
                alert("Gitee 登录暂时不可用，请稍后重试");
            }
        });
    }
}
```

#### 步骤7：更新 HTML 模板

在登录界面添加 Gitee 按钮：

```html
<div class="ac-game-settings-login">
    <!-- AcWing 登录 -->
    <div class="ac-game-settings-acwing">
        <img src="AcWing 图标" alt="AcWing Login">
        <span>AcWing 一键登录</span>
    </div>
    
    <!-- GitHub 登录 -->
    <div class="ac-game-settings-github">
        <img src="GitHub 图标" alt="GitHub Login">
        <span>GitHub 登录</span>
    </div>
    
    <!-- Gitee 登录（新增） -->
    <div class="ac-game-settings-gitee">
        <img src="https://gitee.com/static/images/logo-black.svg" alt="Gitee Login">
        <span>Gitee 登录</span>
    </div>
</div>
```

#### 步骤8：测试 Gitee 登录

1. 重启 Django 服务
2. 点击 Gitee 登录按钮
3. 应该跳转到 Gitee 授权页面
4. 授权后自动登录

#### 完成！

现在你的应用支持三种登录方式：

- ✅ AcWing 登录（可用）
- ⚠️ GitHub 登录（保留代码，网络受限）
- ✅ Gitee 登录（可用）

有问题随时问我！

## 6.3 acapp端AcWing一键登录

实现原理跟上一节课是一样的。只不过申请授权码的方式不一样，上一节课的方法是通过URL申请的，这一节课的方法是通过API来申请的。

首先进入`game/views/settings/acwing/acapp/apply_code.py`，实现**申请授权码**代码跟上一节课的基本相似，所以先直接复制，再进行修改。

```python
from django.http import JsonResponse
from urllib.parse import quote # 引入用于将链接转换为某种格式的工具，把特殊字符比如空格等换成别的表示方式
from random import randint # 引入用于生成随机数的
from django.core.cache import cache

def get_state(): # 获取8位随机数
    res = ""
    for i in range(8):
        res += str(randint(0, 9))
    return res

def apply_code(request):
    appid = "23"
    redirect_uri = quote("https://app23.acapp.acwing.com.cn/settings/acwing/acapp/receive_code/")
    scope = "userinfo"
    state = get_state()

    cache.set(state, True, 7200)

    # apply_url_code = "https://www.acwing.com/third_party/api/oauth2/web/authorize/"

    return JsonResponse({
        'result': "success", 
        # 'apply_code_url' = apply_code_url + "?appid=%s&redirect_uri=%s&scope=%s&state=%s" % (appid, redirect_uri, scope, state)
        # 只要返回这4个参数就行了
        'appid': appid,
        'redirect_uri': redirect_uri,
        'scope': scope,
        'state': state,
    })
```

然后再写一下路由，进入`game/urls/settings/acwing/index.py`，加两个路由，同时解决一下命名冲突。

```coffeescript
from game.views.settings.acwing.web.apply_code import apply_code as web_apply_code
from game.views.settings.acwing.web.receive_code import receive_code as web_receive_code
from game.views.settings.acwing.acapp.apply_code import apply_code as acapp_apply_code
from game.views.settings.acwing.acapp.receive_code import receive_code as acapp_receive_code

urlpatterns = [
    path("web/apply_code/", web_apply_code, name = "settings_acwing_web_apply_code"),
    path("web/receive_code/", web_receive_code, name = "settings_acwing_web_receive_code"),
    path("acapp/apply_code/", acapp_apply_code, name = "settings_acwing_acapp_apply_code"),
    path("acapp/receive_code", acapp_receive_code, name = "settings_acwing_acapp_receive_code"),
]
```

然后进入前端实现这个功能，进入`class Settings`。如果是在`Web`端登录要进行`getinfo()`，如果是在`acapp`端登录，需要单独写一个`getinfo_acapp()`。

```javascript
start()
{
    if (this.platform === "ACAPP") // 如果是在ACAPP端登录
    {
        this.getinfo_acapp();
    }
    else 
    {
        this.getinfo_web();
        this.add_listening_events(); // 这些监听都是那些登陆注册页面那些元素才需要监听，ACAPP直接登录不需要这些页面
    }
}

getinfo_web() // 原来的getinfo()
{
    ...;
}

getinfo_acapp()
{
    let outer = this;

    $.ajax({
        url: "https://app23.acapp.acwing.com.cn/settings/acwing/acapp/apply_code/", // acapp端申请授权码
        type: "GET",
        success: function(resp){
            if (resp.result === "success")
            {
                outer.acapp_login(resp.appid, resp.redirect_uri, resp.scope, resp.state); // 调用acapp端的登录
            }
        }
    })
}

acapp_login(appid, redirect_uri, scope, state)
{
    let outer = this;

    this.root.OS.api.oauth2.authorize(appid, redirect_uri, scope, state, function(resp){ // 照抄讲义上的，调用api，最后一个参数是返回之后调用的函数
        console.log(resp); // 测试
        if (resp.result === "success")
        {
            outer.username = resp.username;
            outer.photo = resp.photo;
            outer.hide();
            outer.root.menu.show();
        }
    });

}
```

我们还要注意后端的`game/views/settings/acwing/acapp/receive_code`，如果用户拒绝了就会返回一个错误码，要再考虑上这个情况。

```python
def receive_code(request):
    data = request.GET

    if "errcode" in data:
        return JsonResponse({
            'result': "apply failed",
            'errcode': data['errcode'],
            'errmsg': data['errmsg'],
        })

    # ...

    if not cache.has_key(state):
        return JsonResponse({
            'result': "state not exist",
        })

    # ... 

    if players.exists():
        # login(...) # 这个是只在浏览器上的settings登录的，我们在acapp的云端上直接登录，不需要每次都登录，更安全。
        player = players[0]
        return JsonResponse({
            'result': "success",
            'username': player.user.username,
            'photo': player.photo
        })

    # ... 

    # login(...)

    return JsonResponse({
        'result': "success",
        'username': player.user.username,
        'photo': player.photo
    })
```

至此，本节课任务完成。

## 7.1 实现联机对战（上）

### 1. 统一长度单位

现在的游戏中可能出现的**一种情况** ：

![屏幕截图 2025-08-04 105220.png](https://cdn.acwing.com/media/article/image/2025/08/04/504252_315cbb0770-%E5%B1%8F%E5%B9%95%E6%88%AA%E5%9B%BE-2025-08-04-105220.png)

多人模式要求不同玩家在一局游戏中，所以地图大小,玩家大小等等游戏界面的所有东西都应该按照玩家电脑界面比例来设定不能够直接确定出实际大小,如若不然某些玩家屏幕大的话,游戏中各种元素的实际大小就偏大,传输数据到小屏幕玩家电脑上造成不协调,同时如果玩家将网页界面缩小,游戏界面内的所有元素同样应该缩小才对,所以我们将原来的游戏界面里每个元素的数据由实际大小变成点前页面比例,这样每次渲染的时候再乘上页面大小就会根据页面大小来确定出实际大小,这样就解决了前面的两种问题,在这里为了保持界面始终是以16 : 9 的比例,我们做出如下操作



#### 让画布长宽比固定为**16：9**

`/home/acs/acapp/game/static/js/src/playground/zbase.js`

```javascript
show(){ // 打开playground界面
    ...
    this.root.$ac_game.append(this.$playground); // 剪切掉这一行
    ...
}
```



把刚才那一行放到 `constructor` 里面

```javascript
constructor(root){
        this.root = root;
        this.$playground =$(`<div class="ac-game-playground"></div>`);

        this.create_confirm_dialog();

        this.hide();
        this.root.$ac_game.append(this.$playground); // 这里
        this.start();
    }
```



实现 `resize` 函数

```javascript
resize() {
        this.width = this.$playground.width();
        this.height = this.$playground.height();
        let unit = Math.min(this.width / 16, this.height / 9);
        this.width = unit * 16;
        this.height = unit * 9;
        this.scale = this.height;

        if(this.game_map) this.game_map.resize();
    }
```



界面打开要 `resize` 一下

```javascript
show(){ // 打开playground界面
        this.$playground.show();

        this.resize();

        ...
    }
```



每次改变窗口大小都 `resize`

```javascript
start(){
        let outer = this;
        $(window).resize(function () {
            outer.resize();
        }); // 当用户改变窗口大小的时候，事件就会触发
    }
```



`/home/acs/acapp/game/static/js/src/playground/game_map/zbase.js`

添加 `resize` 函数

```javascript
resize() {
        this.ctx.canvas.width = this.playground.width;
        this.ctx.canvas.height = this.playground.height;
     }
```



为了让地图 **居中** ，我们改一下`css`

```css
.ac-game-playground > canvas {
    position: relative;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
}
```



`/home/acs/acapp/game/static/js/src/playground/game_map/zbase.js`

```javascript
resize() {
        this.ctx.canvas.width = this.playground.width;
        this.ctx.canvas.height = this.playground.height;
        \\ 去掉渐变效果
        this.ctx.fillStyle = "rgba(0, 0, 0, 1)";
        this.ctx.fillRect(0, 0, this.ctx.canvas.width, this.ctx.canvas.height);
     }

```

---

#### 把所有距离都改成 `相对距离`

即：调整 `particle`,  `player`



##### 先改一下初始化的代码

`/home/acs/acapp/game/static/js/src/playground/zbase.js`

```javascript
show() { // 打开playground界面
        ...
        this.players.push(new Player(this, this.width / 2 / this.scale, 0.5, 0.05, "white", 0.15, true));

        for(let i = 0 ; i < 5 ; i ++){
            this.players.push(new Player(this, this.width / 2 / this.scale, 0.5, 0.05, this.get_random_color(), 0.15, false));
        }
    	
    	...
    }
```

---

##### 修改 `Player` 类

`/home/acs/acapp/game/static/js/src/playground/player/zbase.js`



统一 `eps`

```javascript
constructor(playground, x, y, radius, color, speed, is_me) {
        ...
        this.eps = 0.01;
        ...
    }
```



```javascript
start() {
        if(this.is_me){
            this.add_listening_events();
        }else {
        	// 这里要除上 this.playground.scale
            let tx = Math.random() * this.playground.width / this.playground.scale;
            let ty = Math.random() * this.playground.height / this.playground.scale;
            this.move_to(tx, ty);
        }
    }
```



```javascript
add_listening_events() {
        let outer = this;
        this.playground.game_map.$canvas.on("contextmenu", function() {
            return false;
        });
        this.playground.game_map.$canvas.mousedown(function (e) {
            const rect = outer.ctx.canvas.getBoundingClientRect();

            if (e.which === 3){//移动功能
                outer.move_to((e.clientX - rect.left) / outer.playground.scale, (e.clientY - rect.top) / outer.playground.scale);
            }else if(e.which === 1){
                if(outer.cur_skill == "fireball"){
                    outer.shoot_fireball((e.clientX - rect.left) / outer.playground.scale,  (e.clientY - rect.top) / outer.playground.scale);
                }
                outer.cur_skill = null;
            }
        });
        $(window).keydown(function(e){
            if(e.which === 81){
                outer.cur_skill = "fireball";
                return false;
            }
        });
    }
```



凡是有绝对长度的地方都改成相对长度就好了

```javascript
shoot_fireball(tx, ty){
        let x = this.x;;
        let y = this.y;
        let radius = 0.01;
        let angle = Math.atan2(ty - this.y, tx - this.x);
        let vx = Math.cos(angle), vy = Math.sin(angle);
        let color = "orange";
        let speed = 0.5;
        let move_length =  1.0;
        let damage =  0.01;
        new FireBall(this.playground, this, x, y, radius, vx, vy, color, speed, move_length, damage);
    }
```



```javascript
is_attack(angle, damage){
    ...

    this.radius -= damage;
    if(this.radius < this.eps){ // <--- 改成eps
        this.destroy();
        return false;
    }

    ...
}
```



将 `update()` 里的内容放到 `update_move()` 里面，易于拓展

```javascript
update() {
            this.update_move();
            this.render();
        }

update_move() {
    this.spend_time += this.timedelta / 1000;
    if(!this.is_me && this.spend_time > 5 && Math.random() < 1 / 360.0){
        let player = this.playground.players[Math.floor(Math.random() * this.playground.players.length)];
        let tx = player.x + player.speed * player.vx * this.timedelta / 1000 * 0.3;
        let ty = player.y + player.speed * player.vy * this.timedelta / 1000 * 0.3;
        this.shoot_fireball(tx, ty);
    }
    if (this.damage_speed > this.eps) {   //当前仍处于击退效果中
    this.vx = this.vy = 0;
    this.move_length = 0;
    this.x += this.damage_vx * this.damage_speed * this.timedelta / 1000;
    this.y += this.damage_vy * this.damage_speed * this.timedelta / 1000;
    this.damage_speed *= this.friction; // 击退速度乘以摩擦系数，已达到削减的目的
    } else {
            if (this.move_length < this.eps) {
                this.move_length = 0;
                this.vx = this.vy = 0;
                if (!this.is_me) {
                    let tx = Math.random() * this.playground.width / this.playground.scale; // 这里别忘了除一下
                    let ty = Math.random() * this.playground.height / this.playground.scale; // 这里别忘了除一下
                    this.move_to(tx, ty);
                }

            } else {
                let moved = Math.min(this.move_length, this.speed * this.timedelta / 1000);
                this.x += this.vx * moved;
                this.y += this.vy * moved;

                this.move_length -= moved;
            }
        }
}
```



```javascript
render() {
        let scale = this.playground.scale;
        if (this.is_me) {
            this.ctx.save();
            this.ctx.beginPath();
            this.ctx.arc(this.x * scale, this.y * scale, this.radius * scale, 0, Math.PI * 2, false);
            this.ctx.stroke();
            this.ctx.clip();
            this.ctx.drawImage(this.img, (this.x - this.radius) * scale, (this.y - this.radius) * scale,
                               this.radius * 2 * scale, this.radius * 2 * scale);
            this.ctx.restore();
        } else {
            this.ctx.beginPath();
            this.ctx.arc(this.x * scale, this.y * scale, this.radius * scale, 0, Math.PI * 2, false);
            this.ctx.fillStyle = this.color;
            this.ctx.fill();
        }
    }
```

---

##### 修改 `FireBall` 类

`/home/acs/acapp/game/static/js/src/playground/skill/fireball/zbase.js`



改 `eps`

```javascript
constructor(playground, player, x, y, raidus, vx, vy, color, speed, move_length, damage) {
        ...
        this.eps = 0.01;
    }
```



```javascript
render(){
        let scale = this.playground.scale;
        this.ctx.beginPath();
        this.ctx.arc(this.x * scale, this.y * scale, this.radius * scale, 0, 2 * Math.PI, false);
        this.ctx.fillStyle  = this.color;
        this.ctx.fill();
    }
```

---

##### 修改 `Particle` 类

 `/home/acs/acapp/game/static/js/src/playground/particle/zbase.js`



改`eps`

```javascript
constructor(playground, x, y, radius, vx, vy, color, speed, move_length) {
        ...
        this.eps = 0.01;
        ...
    }
```



```javascript
render(){
    let scale = this.playground.scale;
    this.ctx.beginPath();
    this.ctx.arc(this.x * scale, this.y * scale, this.radius * scale, 0, Math.PI * 2, false);
    this.ctx.fillStyle = this.color;
    this.ctx.fill();
}
```

---

### 2. 增加“联机对战”模式

`/home/acs/acapp/game/static/js/src/menu/zbase.js`

```javascript
add_listening_events() {
        let outer = this;
        this.$single_mode.click(function(){
            outer.hide();
            outer.root.playground.show("single mode");
        });
        this.$multi_mode.click(function(){
            outer.hide();
            outer.root.playground.show("multi mode");
        });
        this.$settings.click(function(){
            console.log("click settings");
        });
        this.$exit.click(function(){
            console.log("exit");
            outer.root.settings.logout_on_remote();
        });
    }
```



##### **将两种模式分开**

`/home/acs/acapp/game/static/js/src/playground/zbase.js`

```javascript
show(mode) { // 打开playground界面
        this.$playground.show();

        this.resize();

        //存下来宽高
        this.width = this.$playground.width();
        this.height = this.$playground.height();
        this.game_map = new GameMap(this);
        this.players = [];
        this.players.push(new Player(this, this.width / 2 / this.scale, 0.5, 0.05, "white", 0.15, true));
        if(mode === "single mode") {
            for (let i = 0; i < 5; i++) {
                this.players.push(new Player(this, this.width / 2 / this.scale, 0.5, 0.05, this.get_random_color(), 0.15, false));
            }
        } else if (mode === "multi mode"){

        }

        // 添加监听函数，为了实现退出游戏的功能
        // this.add_listening_events()
    }
```



##### **区分自己、机器人、和敌人**(还要传入玩家的用户名和头像)

记得把 `this.resize()` 放到 `game_map` 后面

`/home/acs/acapp/game/static/js/src/playground/zbase.js`

```javascript
show(mode) { // 打开playground界面
        this.$playground.show();
        //存下来宽高
        this.width = this.$playground.width();
        this.height = this.$playground.height();
        this.game_map = new GameMap(this);

        this.resize();

        this.players = [];
        this.players.push(new Player(this, this.width / 2 / this.scale, 0.5, 0.05, "white", 0.15, "me", this.root.settings.username, this.root.settings.photo));
        if(mode === "single mode") {
            for (let i = 0; i < 5; i++) {
                this.players.push(new Player(this, this.width / 2 / this.scale, 0.5, 0.05, this.get_random_color(), 0.15, "robot"));
            }
        } else if (mode === "multi mode"){

        }
        ...
    }
```



##### **因为改了参数，所以也要改一下 `Player` 类**

有 `is_me` 的地方都要修改

`/home/acs/acapp/game/static/js/src/playground/player/zbase.js`

```javascript
class Player extends AcGameObject{
    constructor(playground, x, y, radius, color, speed, character, username, photo) {
        ...
        this.character = character;
        this.username = username;
        ...

        if(this.character !== "robot") { // 只有不是机器人 才需要渲染图片
            this.img = new Image();
            this.img.src = this.photo;
        }
    }

    start() {
        if(this.character === "me"){
            this.add_listening_events();
        }
        ...
    }

    ...

    update_move() {
        this.spend_time += this.timedelta / 1000;
        if(this.character === "robot" && this.spend_time > 5 && Math.random() < 1 / 360.0){
            let player = this.playground.players[Math.floor(Math.random() * this.playground.players.length)];
            let tx = player.x + player.speed * player.vx * this.timedelta / 1000 * 0.3;
            let ty = player.y + player.speed * player.vy * this.timedelta / 1000 * 0.3;
            this.shoot_fireball(tx, ty);
        }
        if (this.damage_speed > this.eps) {   //当前仍处于击退效果中
        this.vx = this.vy = 0;
        this.move_length = 0;
        this.x += this.damage_vx * this.damage_speed * this.timedelta / 1000;
        this.y += this.damage_vy * this.damage_speed * this.timedelta / 1000;
        this.damage_speed *= this.friction; // 击退速度乘以摩擦系数，已达到削减的目的
        } else {
                if (this.move_length < this.eps) {
                    this.move_length = 0;
                    this.vx = this.vy = 0;
                    if (this.character === "robot") {
                        let tx = Math.random() * this.playground.width / this.playground.scale;
                        let ty = Math.random() * this.playground.height / this.playground.scale;
                        this.move_to(tx, ty);
                    }

                } else {
                    let moved = Math.min(this.move_length, this.speed * this.timedelta / 1000);
                    this.x += this.vx * moved;
                    this.y += this.vy * moved;

                    this.move_length -= moved;
                }
            }
    }

    render() {
        let scale = this.playground.scale;
        if (this.character !== "robot") {
            this.ctx.save();
            this.ctx.beginPath();
            this.ctx.arc(this.x * scale, this.y * scale, this.radius * scale, 0, Math.PI * 2, false);
            this.ctx.stroke();
            this.ctx.clip();
            this.ctx.drawImage(this.img, (this.x - this.radius) * scale, (this.y - this.radius) * scale,
                               this.radius * 2 * scale, this.radius * 2 * scale);
            this.ctx.restore();
        } else {
            this.ctx.beginPath();
            this.ctx.arc(this.x * scale, this.y * scale, this.radius * scale, 0, Math.PI * 2, false);
            this.ctx.fillStyle = this.color;
            this.ctx.fill();
        }
    }

    ...
}
```

### 3. 配置channels_redis

#### 1\. 安装`channels_redis`：

```nginx
pip install channels_redis
```

* * *

#### 2\. 配置`acapp/asgi.py`

内容如下：

```coffeescript
import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from game.routing import websocket_urlpatterns

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'acapp.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(URLRouter(websocket_urlpatterns))
})
```

* * *

#### 3\. 配置`acapp/settings.py`

在`INSTALLED_APPS`中添加`channels`，添加后如下所示：

```nginx
INSTALLED_APPS = [ 
    'channels',
    'game.apps.GameConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]
```

然后在文件末尾添加：

```bash
ASGI_APPLICATION = 'acapp.asgi.application'
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("127.0.0.1", 6379)],
        },
    },
}
```

* * *

#### 4\. 配置`game/routing.py`

这一部分的作用相当于`http`的`urls`。  
内容如下：

```coffeescript
from django.urls import path

websocket_urlpatterns = [
]
```

* * *

#### 5\. 编写`game/consumers`

这一部分的作用相当于`http`的`views`。

参考示例：

```python
from channels.generic.websocket import AsyncWebsocketConsumer
import json

class MultiPlayer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        print('accept')

        self.room_name = "room"
        await self.channel_layer.group_add(self.room_name, self.channel_name)

    async def disconnect(self, close_code):
        print('disconnect')
        await self.channel_layer.group_discard(self.room_name, self.channel_name)


    async def receive(self, text_data):
        data = json.loads(text_data)
        print(data)
```

#### 6\. 启动`django_channels`

在`~/acapp`目录下执行：

```css
daphne -b 0.0.0.0 -p 5015 acapp.asgi:application
```

---

#### 7. 建立 WSS 连接

##### 路由 routing

`game/routing.py`

```python
from django.urls import path
from game.consumers.multiplayer.index import MultiPlayer

websocket_urlpatterns = [
        path("wss/multiplayer/", MultiPlayer.as_asgi(), name = "wss_multiplayer"),
        ]

```

##### 前端js

`playground/zbase.js`

```javascript
class AcGamePlayground{
    ...

    show(mode) { // 打开playground界面
        let outer = this;
        this.$playground.show();
        //存下来宽高
        this.width = this.$playground.width();
        this.height = this.$playground.height();
        this.game_map = new GameMap(this);

        this.resize();

        this.players = [];
        this.players.push(new Player(this, this.width / 2 / this.scale, 0.5, 0.05, "white", 0.15, "me", this.root.settings.username, this.root.settings.photo));
        if(mode === "single mode") {
            for (let i = 0; i < 5; i++) {
                this.players.push(new Player(this, this.width / 2 / this.scale, 0.5, 0.05, this.get_random_color(), 0.15, "robot"));
            }
        } else if (mode === "multi mode"){
            this.mps = new MultiPlayerSocket(this);

            this.mps.ws.onopen = function () {
                outer.mps.send_create_player();
            };
        }
        ...
    }
    
    ...
}
```



`playground/socket/multiplayer/zbase.js`

```javascript
class MultiPlayerSocket {
    constructor(playground) {
        this.playground = playground;

        this.ws = new WebSocket("wss://app7549.acapp.acwing.com.cn/wss/multiplayer/");

        this.start();
    }

    start() {

    }

    send_create_player() {
        this.ws.send(JSON.stringify({
            'message': 'hello acapp server',
        }));
    }

    receive_create_player() {

    }
}
```

---

### 4. 编写同步函数

修改 `AcGameObject` 类

为了实现以后的功能，我们先要为每一个物体创建一个编号

```javascript
let AC_GAME_OBJECTS = []; //用于记录当前画布中，需要渲染的对象有哪些

class AcGameObject{
    constructor() {
        ...
		this.uuid = this.create_uuid();
        console.log(this.uuid);
    }

    create_uuid() {
        let res = "";
        for(let i = 0 ; i < 8 ; i ++){
            let x = parseInt(Math.floor(Math.random() * 10)); // 返回[0,1) 之间的数
            res += x;
        }
        return res;
    }

    ...
}


requestAnimationFrame(AC_GAME_ANIMATION); // js提供的api，其功能请见笔记
```



这样我们会发现有一个问题，不同的玩家用不同的浏览器，同一个物体，对应的 `uuid` 是不一样的。在这里，我们需要用通信的方式保持一致。原则是：**谁创建的，`uuid`就用谁的**



下面开始写同步函数。在这里，我们选择同步**操作**，而不是同步坐标。目的是为了减轻服务器压力。



我们先实现：**所有的窗口里都可以显示所有的玩家**

这里我们有**房间**的概念，按顺序看每个房间。如果这个房间没有到达人数上限，就加入这个房间。



先在 `settings.py` 里面设置房间人数上限



`/home/acs/acapp/acapp/settings.py`

```python
ROOM_CAPACITY = 3
```



#### 后端

`/home/acs/acapp/game/consumers/multiplayer/index.py`

```python
from channels.generic.websocket import AsyncWebsocketConsumer
import json
from django.conf import settings
from django.core.cache import cache

class MultiPlayer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = None

        for i in range(1000):
            name = "room-%d" % i
            if not cache.has_key(name) or len(cache.get(name)) < settings.ROOM_CAPACITY:
                self.room_name = name
                break

        if not self.room_name:
            return

        await self.accept()

        if not cache.has_key(self.room_name):
            cache.set(self.room_name, [], 3600) # 有效期1小时

        for player in cache.get(self.room_name):
            await self.send(text_data=json.dumps({
                'event': "create_player",
                'uuid': player['uuid'],
                'username': player['username'],
                'photo': player['photo'],
            }))

        await self.channel_layer.group_add(self.room_name, self.channel_name)

    async def disconnect(self, close_code):
        print('disconnect')
        await self.channel_layer.group_discard(self.room_name, self.channel_name)

    async def create_player(self, data):
        players = cache.get(self.room_name, [])
        players.append({
            'uuid': data['uuid'],
            'username': data['username'],
            'photo': data['photo'],
        })
        cache.set(self.room_name, players, 3600)
        await self.channel_layer.group_send(
            self.room_name,
            {
                'type': "group_create_player",
                'event': "create_player",
                'uuid': data['uuid'],
                'username': data['username'],
                'photo': data['photo'],
            }
        )

    async def group_create_player(self, data):
        await self.send(text_data=json.dumps(data))

    async def receive(self, text_data):
        data = json.loads(text_data)
        event = data['event']
        if event == 'create_player':
            await self.create_player(data)
```



#### 前端

`/home/acs/acapp/game/static/js/src/playground/socket/multiplayer/zbase.js`

```javascript
class MultiPlayerSocket {
    constructor(playground) {
        this.playground = playground;

        this.ws = new WebSocket("wss://app7549.acapp.acwing.com.cn/wss/multiplayer/");

        this.start();
    }

    start() {
        this.receive();
    }

    receive() {
        let outer = this;
        this.ws.onmessage = function(e) {
            let data = JSON.parse(e.data);
            let uuid = data.uuid;

            if (uuid === outer.uuid) return false;

            let event = data.event;
            if (event === "create_player") {
                outer.receive_create_player(uuid, data.username, data.photo);
            }
        };
    }

    send_create_player(username, photo) {
        let outer = this;
        this.ws.send(JSON.stringify({
            'event': "create_player",
            'uuid': outer.uuid,
            'username': username,
            'photo': photo,
        }));
    }

    receive_create_player(uuid, username, photo) {
        let player = new Player(
            this.playground,
            this.playground.width / 2 / this.playground.scale,
            0.5,
            0.05,
            "white",
            0.15,
            "enemy",
            username,
            photo,
        );
        player.uuid =  uuid;
        this.playground.players.push(player);
    }
}
```

---

### 同步函数详细执行流程

#### 1. **玩家点击"多人模式"按钮**

**文件**: `/home/acs/acapp/game/static/js/src/menu/zbase.js`

```javascript
// 第10-14行
this.$multi_mode.click(function(){
    outer.hide();
    outer.root.playground.show("multi mode");
});
```

#### 2. **进入多人模式游戏界面**

**文件**: `/home/acs/acapp/game/static/js/src/playground/zbase.js`

```javascript
// 第23-35行
show(mode) {
    // ... 省略部分代码
    
    // 第30行：创建自己的角色
    this.players.push(new Player(this, this.width / 2 / this.scale, 0.5, 0.05, 
        "white", 0.15, "me", this.root.settings.username, this.root.settings.photo));
    
    // 第35-40行：如果是多人模式
    } else if (mode === "multi mode"){
        // 创建 WebSocket 连接
        this.mps = new MultiPlayerSocket(this);
        
        // 设置连接成功后的回调
        this.mps.ws.onopen = function () {
            outer.mps.send_create_player();
        };
    }
}
```

#### 3. **建立 WebSocket 连接**

**文件**: `/home/acs/acapp/game/static/js/src/playground/socket/multiplayer/zbase.js`

```javascript
// 第1-10行
class MultiPlayerSocket {
    constructor(playground) {
        this.playground = playground;
        
        // 第5行：创建 WebSocket 连接
        this.ws = new WebSocket("wss://app7549.acapp.acwing.com.cn/wss/multiplayer/");
        
        this.start();
    }
}
```

#### 4. **后端接受连接**

**文件**: `/home/acs/acapp/game/consumers/multiplayer/index.py`

```python
# 第7-27行
async def connect(self):
    # 第8-14行：查找可用房间
    self.room_name = None
    for i in range(1000):
        name = "room-%d" % i
        if not cache.has_key(name) or len(cache.get(name)) < settings.ROOM_CAPACITY:
            self.room_name = name
            break
    
    # 第18行：接受连接
    await self.accept()
    
    # 第20-21行：初始化房间缓存
    if not cache.has_key(self.room_name):
        cache.set(self.room_name, [], 3600)
    
    # 第23-29行：向新玩家发送房间内已有玩家信息
    for player in cache.get(self.room_name):
        await self.send(text_data=json.dumps({
            'event': "create_player",
            'uuid': player['uuid'],
            'username': player['username'],
            'photo': player['photo'],
        }))
    
    # 第31行：将新玩家加入广播组
    await self.channel_layer.group_add(self.room_name, self.channel_name)
```

#### 5. **前端接收已有玩家信息**

**文件**: `/home/acs/acapp/game/static/js/src/playground/socket/multiplayer/zbase.js`

```javascript
// 第16-30行
receive() {
    let outer = this;
    this.ws.onmessage = function(e) {
        let data = JSON.parse(e.data);
        let uuid = data.uuid;
        
        // 第22行：如果是自己则忽略
        if (uuid === outer.uuid) return false;
        
        let event = data.event;
        // 第25-27行：如果是创建玩家事件
        if (event === "create_player") {
            outer.receive_create_player(uuid, data.username, data.photo);
        }
    };
}

// 第42-56行：创建其他玩家
receive_create_player(uuid, username, photo) {
    let player = new Player(
        this.playground,
        this.playground.width / 2 / this.playground.scale,
        0.5,
        0.05,
        "white",
        0.15,
        "enemy",  // 注意这里是 "enemy"
        username,
        photo,
    );
    player.uuid = uuid;
    this.playground.players.push(player);
}
```

#### 6. **连接成功后发送自己的信息**

**文件**: `/home/acs/acapp/game/static/js/src/playground/zbase.js`

```javascript
// 第38-40行
this.mps.ws.onopen = function () {
    outer.mps.send_create_player();
};
```

**文件**: `/home/acs/acapp/game/static/js/src/playground/socket/multiplayer/zbase.js`

```javascript
// 第32-40行
send_create_player(username, photo) {
    let outer = this;
    this.ws.send(JSON.stringify({
        'event': "create_player",
        'uuid': outer.uuid,
        'username': username,
        'photo': photo,
    }));
}
```

#### 7. **后端接收并广播新玩家信息**

**文件**: `/home/acs/acapp/game/consumers/multiplayer/index.py`

```python
# 第57-62行：接收消息
async def receive(self, text_data):
    data = json.loads(text_data)
    event = data['event']
    if event == 'create_player':
        await self.create_player(data)

# 第37-55行：处理创建玩家
async def create_player(self, data):
    # 第38-43行：将新玩家加入缓存
    players = cache.get(self.room_name, [])
    players.append({
        'uuid': data['uuid'],
        'username': data['username'],
        'photo': data['photo'],
    })
    cache.set(self.room_name, players, 3600)
    
    # 第44-53行：向房间内所有人广播
    await self.channel_layer.group_send(
        self.room_name,
        {
            'type': "group_create_player",
            'event': "create_player",
            'uuid': data['uuid'],
            'username': data['username'],
            'photo': data['photo'],
        }
    )

# 第55-56行：处理组广播
async def group_create_player(self, data):
    await self.send(text_data=json.dumps(data))
```

#### 8. **所有玩家接收广播并创建新玩家**

这又回到了第5步的前端接收逻辑，每个在房间内的玩家都会执行 `receive_create_player()` 来在自己的界面上创建新加入的玩家。

---

#### 关键文件路径总结

- **前端 WebSocket**: `/home/acs/acapp/game/static/js/src/playground/socket/multiplayer/zbase.js`
- **后端 Consumer**: `/home/acs/acapp/game/consumers/multiplayer/index.py`
- **游戏主界面**: `/home/acs/acapp/game/static/js/src/playground/zbase.js`
- **菜单界面**: `/home/acs/acapp/game/static/js/src/menu/zbase.js`



## 7.2 实现联机对战（下）

一开始，先删掉 `js` 文件里的 `console.log()` 调试信息



**给我们之前的内容做个补充**

**在AcApp里的菜单页面点击退出，可以实现关闭窗口**。

`/home/acs/acapp/game/static/js/src/settings/zbase.js`

```javascript
class Settings {
    ...

    logout_on_remote() { // 在远程服务器上登出
        if(this.platform === "ACAPP") {
            this.root.AcWingOS.api.window.close();
        }

        ...
    }
    
    ...
}

```

---

### 1. move_to

#### 前端

**仿照上节课的流程**

`/home/acs/acapp/game/static/js/src/playground/socket/multiplayer/zbase.js`



仿照 `send_create_player` 和 `receive_create_player`

写一下 `send_move_to` 和 `receive_move_to`

```javascript
class MultiPlayerSocket {
    ...

    receive() {
        let outer = this;
        this.ws.onmessage = function(e) {
            ...
            
            else if(event === "move_to") {
                outer.receive_move_to(uuid, data.tx, data.ty);
            } 
            
            ...
        };
    }

    ...

    get_player(uuid) {
        let players = this.playground.players;
        for(let i = 0 ;  i < players.length ; i ++) {
            let player = players[i];
            if(player.uuid === uuid)
                return player;
        }
        return null;
    }

    send_move_to(tx, ty) {
        let outer = this;
        this.ws.send(JSON.stringify({
            'event': "move_to",
            'uuid': outer.uuid,
            'tx': tx,
            'ty': ty,
        }));
    }

    receive_move_to(uuid, tx, ty) {
        let player = this.get_player(uuid);

        if(player) {
            player.move_to(tx, ty);
        }
    }

    ...
}
```



记录下当前的模式。因为只有在多人模式下才会触发**通信**。

`/home/acs/acapp/game/static/js/src/playground/zbase.js`

```javascript
class AcGamePlayground{
    ...

    show(mode) { // 打开playground界面
        ...
        this.mode = mode;
        ...
    }
    
   ...

}


```



`/home/acs/acapp/game/static/js/src/playground/player/zbase.js`

```javascript
class Player extends AcGameObject{
    ...

    add_listening_events() {
        ...
        this.playground.game_map.$canvas.mousedown(function (e) {
            const rect = outer.ctx.canvas.getBoundingClientRect();

            if (e.which === 3){//移动功能
                let tx = (e.clientX - rect.left) / outer.playground.scale;
                let ty = (e.clientY - rect.top) / outer.playground.scale;
                outer.move_to(tx, ty);

                if(outer.playground.mode === "multi mode") {
                    outer.playground.mps.send_move_to(tx, ty); // 调用函数
                }
            }else if(e.which === 1){
                if(outer.cur_skill == "fireball"){
                    outer.shoot_fireball((e.clientX - rect.left) / outer.playground.scale,  (e.clientY - rect.top) / outer.playground.scale);
                }
                outer.cur_skill = null;
            }
        });
        ...
    }

    ...
}
```



---

#### 后端

`/home/acs/acapp/game/consumers/multiplayer/index.py`



所有需要广播的函数都是一样的，所以我们可以做出如下更改

把 `group_create_player` 改成 `group_send_event`



同时

```python
    async def create_player(self, data):
        players = cache.get(self.room_name, [])
        players.append({
            'uuid': data['uuid'],
            'username': data['username'],
            'photo': data['photo'],
        })
        cache.set(self.room_name, players, 3600)
        await self.channel_layer.group_send(
            self.room_name,
            {
                'type': "group_send_event", // 改一下这里
                'event': "create_player",
                'uuid': data['uuid'],
                'username': data['username'],
                'photo': data['photo'],
            }
        )
```



```python
from channels.generic.websocket import AsyncWebsocketConsumer
import json
from django.conf import settings
from django.core.cache import cache

class MultiPlayer(AsyncWebsocketConsumer):
    ...

    async def move_to(self, data):
        await self.channel_layer.group_send(
            self.room_name,
            {
                'type': "group_send_event",
                'event': "move_to",
                'uuid': data['uuid'],
                'tx': data['tx'],
                'ty': data['ty'],
            }
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        event = data['event']
        if event == 'create_player':
            await self.create_player(data)
        elif event == 'move_to': // 加路由
            await self.move_to(data)
```

---

### 2. shoot_fireball

#### 前端

`/home/acs/acapp/game/static/js/src/playground/player/zbase.js`

```javascript
class Player extends AcGameObject{
    constructor(playground, x, y, radius, color, speed, character, username, photo) {
        ...
        this.fireballs = [];
		...
    }

    ...

    add_listening_events() {
        let outer = this;
        this.playground.game_map.$canvas.on("contextmenu", function() {
            return false;
        });
        this.playground.game_map.$canvas.mousedown(function (e) {
            const rect = outer.ctx.canvas.getBoundingClientRect();

            if (e.which === 3){//移动功能
                let tx = (e.clientX - rect.left) / outer.playground.scale;
                let ty = (e.clientY - rect.top) / outer.playground.scale;
                outer.move_to(tx, ty);

                if(outer.playground.mode === "multi mode") {
                    outer.playground.mps.send_move_to(tx, ty);
                }
            }else if(e.which === 1){
                let tx = (e.clientX - rect.left) / outer.playground.scale;
                let ty =  (e.clientY - rect.top) / outer.playground.scale;
                if(outer.cur_skill == "fireball"){
                    let fireball = outer.shoot_fireball(tx, ty);
                    if(outer.playground.mode === "multi mode") {
                        outer.playground.mps.send_shoot_fireball(tx, ty, fireball.uuid);
                    }
                }
                outer.cur_skill = null;
            }
        });
        $(window).keydown(function(e){
            if(e.which === 81){
                outer.cur_skill = "fireball";
                return false;
            }
        });
    }

    shoot_fireball(tx, ty){
        ...
        let fireball = new FireBall(this.playground, this, x, y, radius, vx, vy, color, speed, move_length, damage);
        this.fireballs.push(fireball);

        return fireball; // 为了获取到子弹的uuid
    }

    destroy_fireball(uuid) {
        for(let i = 0; i < this.fireballs.length; i ++) {
            let fireball = this.fireballs[i];
            if (fireball.uuid === uuid) {
                fireball.destory();
                break;
            }
        }
    }

    ...
}
```



`/home/acs/acapp/game/static/js/src/playground/skill/fireball/zbase.js`

```javascript
class FireBall extends AcGameObject {
    ...

    update() {
        if (this.move_length < this.eps) {
            this.destroy();
            return false;
        }
        this.update_move();
        this.update_attack();

        this.render();
    }

    update_move() {
        let moved = Math.min(this.move_length, this.speed * this.timedelta / 1000);
        this.x += this.vx * moved;
        this.y += this.vy * moved;
        this.move_length -= moved;
    }

    update_attack() {
        for (let i = 0; i < this.playground.players.length; i++) {
            let player = this.playground.players[i];
            if (this.player !== player && this.is_collision(player)) {
                this.attack(player);
                break;
            }
        }
    }


    ...

    on_destroy() {
        let fireballs = this.player.fireballs;
        for (let i = 0; i < fireballs.length; i++) {
            if (fireballs[i] === this) {
                fireballs.splice(i, 1);
                break;
            }
        }
    }
}
```



`/home/acs/acapp/game/static/js/src/playground/socket/multiplayer/zbase.js`

```javascript
class MultiPlayerSocket {
    ...

    receive() {
        let outer = this;
        this.ws.onmessage = function(e) {
            ...
            else if(event === "shoot_fireball") {
                outer.receive_shoot_fireball(uuid, data.tx, data.ty, data.ball_uuid);
            }
        };
    }

    ...

    send_shoot_fireball(tx, ty, ball_uuid) {
        let outer = this;
        this.ws.send(JSON.stringify({
            'event': "shoot_fireball",
            'uuid': outer.uuid,
            'tx': tx,
            'ty': ty,
            'ball_uuid': ball_uuid,
        }));
    }

    receive_shoot_fireball(uuid, tx, ty, ball_uuid) {
        let player = this.get_player(uuid);
        if(player) {
            let fireball = player.shoot_fireball(tx, ty);
            fireball.uuid = ball_uuid;
        }
    }
}
```

---

#### 后端

`/home/acs/acapp/game/consumers/multiplayer/index.py`

```
from channels.generic.websocket import AsyncWebsocketConsumer
import json
from django.conf import settings
from django.core.cache import cache

class MultiPlayer(AsyncWebsocketConsumer):
    ...

    async def shoot_fireball(self, data):
        await self.channel_layer.group_send(
            self.room_name,
            {
                'type': "group_send_event",
                'event': "shoot_fireball",
                'uuid': data['uuid'],
                'tx': data['tx'],
                'ty': data['ty'],
                'ball_uuid': data['ball_uuid'],
            }
        )

    async def receive(self, text_data):
        ...
        elif event == 'shoot_fireball':
            await self.shoot_fireball(data)
```

---

### 3. attack

为了只让一个客户端进行攻击命中的判断，因此只有发出方的火球才做碰撞检测

其他客户端对于该火球只有动画效果

又由于碰撞检测是在一台客户端上进行的，因此多端之间可能会存在同步上的延迟

为此的解决方法是：碰撞检测成功时，强制把被击中玩家移动到发起方客户端中的位置，以避免击中延迟上发生的事情

#### 前端

`/home/acs/acapp/game/static/js/src/playground/skill/fireball/zbase.js`

```javascript
class FireBall extends AcGameObject {
    ...

    update() {
        if (this.move_length < this.eps) {
            this.destroy();
            return false;
        }
        this.update_move();

        if(this.player.character !== "enemy") {
            this.update_attack();
        }

        this.render();
    }

    ...

    attack(player) {
        ...

        if(this.playground.mode === "multi mode") {
            this.playground.mps.send_attack(player.uuid, player.x, player.y, angle, this.damage, this.uuid);
        }

        ...
    }

    ...
}
```



`/home/acs/acapp/game/static/js/src/playground/player/zbase.js`

```javascript
class Player extends AcGameObject{
    ...

    receive_attack(x, y, angle, damage, ball_uuid, attacker) {
        attacker.destroy_fireball(ball_uuid);
        this.x = x;
        this.y = y;
        this.is_attack(angle, damage);
    }

    ...
}
```



`/home/acs/acapp/game/static/js/src/playground/socket/multiplayer/zbase.js`

```javascript
class MultiPlayerSocket {
    ...

    receive() {
        let outer = this;
        this.ws.onmessage = function(e) {
            ...
            else if (event === "attack") {
                outer.receive_attack(uuid, data.attackee_uuid, data.x, data.y, data.angle, data.damage, data.ball_uuid);
            }
        };
    }

    ...

    send_attack(attackee_uuid, x, y, angle, damage, ball_uuid) {
        let outer = this;
        this.ws.send(JSON.stringify({
            'event': "attack",
            'uuid': outer.uuid,
            'attackee_uuid': attackee_uuid,
            'x': x,
            'y': y,
            'angle' : angle,
            'damage': damage,
            'ball_uuid': ball_uuid,
        }));
    }

    receive_attack(uuid, attackee_uuid, x, y, angle, damage, ball_uuid) {
        let attacker = this.get_player(uuid);
        let attackee = this.get_player(attackee_uuid);
        if (attacker && attackee) {
            attackee.receive_attack(x, y, angle, damage, ball_uuid, attacker);
        }
    }
}
```



#### 后端

`/home/acs/acapp/game/consumers/multiplayer/index.py`

```python
from channels.generic.websocket import AsyncWebsocketConsumer
import json
from django.conf import settings
from django.core.cache import cache

class MultiPlayer(AsyncWebsocketConsumer):
    ...

    async def attack(self, data):
        await self.channel_layer.group_send(
            self.room_name,
            {
                'type': "group_send_event",
                'event': "attack",
                'uuid': data['uuid'],
                'attackee_uuid': data['attackee_uuid'],
                'x': data['x'],
                'y': data['y'],
                'angle': data['angle'],
                'damage': data['damage'],
                'ball_uuid': data['ball_uuid'],
            }
        )

    async def receive(self, text_data):
        ...
        elif event == 'attack':
            await self.attack(data)
```

---

### 4. 游戏的优化

#### 多人模式下游戏没有开始前，玩家不可以移动

为此我们先引入一个状态机：`'waiting' -> 'fighting' -> 'over'` 来标识当前游戏进行的状态

然后用一个 `notice_board` 计分板在前端显示出来

实现的逻辑就是：游戏初始时为 `waiting` 状态，房间内人数满 3 人时，才会进入 `fighting`，角色死亡时为 `over`

且发射火球，移动等行为，当且仅当玩家状态为 `fighting` 时，才可以做



`/home/acs/acapp/game/static/js/src/playground/notice_board/zbase.js`

```javascript
class NoticeBoard extends AcGameObject {
    constructor(playground) {
        super();

        this.playground = playground;
        this.ctx = this.playground.game_map.ctx;
        this.text = "已就绪：0人";
    }

    start() {

    }

    write(text) {
        this.text = text;
    }

    update() {
        this.render();
    }

    render() {
        this.ctx.font = "20px serif";
        this.ctx.fillStyle = "white";
        this.ctx.textAlign = "center";
        this.ctx.fillText(this.text, this.playground.width / 2, 20);
    }
}
```



`/home/acs/acapp/game/static/js/src/playground/zbase.js`

```javascript
class AcGamePlayground{
    ...

    show(mode) { // 打开playground界面
        ...
        this.mode = mode;
        this.state = "waiting"; // waiting - fighting - over
        this.notice_board = new NoticeBoard(this);
        this.player_count = 0;
        ...
    }
    ...
}


```



`/home/acs/acapp/game/static/js/src/playground/player/zbase.js`

```javascript
class Player extends AcGameObject{
    ...

    start() {
        this.playground.player_count ++;
        this.playground.notice_board.write("已就绪：" + this.playground.player_count + "人");

        if(this.playground.player_count >= 3) {
            this.playground.state = "fighting";
            this.playground.notice_board.write("Fighting");
        }
        ...
    }

    add_listening_events() {
        ...
        this.playground.game_map.$canvas.mousedown(function (e) {
            if (outer.playground.state !== "fighting")
                return false;

            ...
        });
        $(window).keydown(function(e){
            if (outer.playground.state !== "fighting")
                return false;
            ...
        });
    }

    ...
}
```

---

#### 技能CD

给火球技能设置 `3s` 的 `cd`，实现逻辑很简单，设定一个 `cool_time` 变量，每次渲染的时候减去上次渲染的时间间隔

然后 `cool_time` 为 `0` 时，技能才可以成功释放

另外修改冷却时间，只用修改自己的即可



`/home/acs/acapp/game/static/js/src/playground/player/zbase.js`

```javascript
class Player extends AcGameObject {
    constructor(playground, x, y, radius, color, speed, character, username, photo) {
        ...

        if (this.character === "me") {
            this.fireball_coldtime = 3; // 单位： s
        }
    }

    ...

    add_listening_events() {
        ...
        this.playground.game_map.$canvas.mousedown(function (e) {
            ...
            else if (e.which === 1) {
                if (outer.fireball_coldtime > outer.eps)
                        return false;
                ...
            }
        });
            
        $(window).keydown(function (e) {
            ...
            if (outer.fireball_coldtime >= outer.eps)
                return false;
            ...
        });
    }

    ...

    update() {
        this.spend_time += this.timedelta / 1000;

        if (this.character === "me" && this.playground.state === "fighting") {
            this.update_coldtime();
        }
        this.update_move();
        this.render();
    }

    update_coldtime() {
        this.fireball_coldtime -= this.timedelta / 1000;
        this.fireball_coldtime = Math.max(this.fireball_coldtime, 0);
    }

    ...
    
    shoot_fireball(tx, ty) {
        ...
        this.fireball_coldtime = 3;
        ...
    }
}
```

---

#### 用图片来渲染技能CD

`/home/acs/acapp/game/static/js/src/playground/player/zbase.js`

```javascript
class Player extends AcGameObject {
    constructor(...) {
        ...
        if (this.character === "me") {
            this.fireball_coldtime = 3; // 单位：s
            this.fireball_img = new Image();
            this.fireball_img.src = "https://cdn.acwing.com/media/article/image/2021/12/02/1_9340c86053-fireball.png";
        }
    }
    ...
    render() {
        ...
        if (this.character === "me" && this.playground.state === "fighting") {
            this.render_skill_coldtime();
        }
    }
     render_skill_coldtime() {
        let scale = this.playground.scale;
        let x = 1.5, y = 0.9, r = 0.04;

        // 渲染技能图标
        this.ctx.save();
        this.ctx.beginPath();
        this.ctx.arc(x * scale, y * scale, r * scale, 0, Math.PI * 2, false);
        this.ctx.stroke();
        this.ctx.clip();
        this.ctx.drawImage(this.fireball_img, (x - r) * scale, (y - r) * scale, r * 2 * scale, r * 2 * scale);
        this.ctx.restore();

        // 渲染冷却指示
        if (this.fireball_coldtime >= this.eps){
            this.ctx.beginPath();
            this.ctx.moveTo(x * scale, y * scale);
            this.ctx.arc(x * scale, y * scale, r * scale, 0 - Math.PI / 2, Math.PI * 2 * (1 - this.fireball_coldtime / 3) - Math.PI / 2, true);
            this.ctx.lineTo(x * scale, y * scale);
            this.ctx.fillStyle = "rgba(0, 0, 255, 0.6)";
            this.ctx.fill();
        }
    }
    ...
```

---

#### 添加一个闪现技能

##### 单机部分

`js/src/playground/player/zbase.js`

```
class Player extends AcGameObject {
    constructor(...) {
        ...
        if (this.character === "me") {
            ...
            this.blink_coldtime = 5;
            this.blink_img = new Image();
            this.blink_img.src = "https://cdn.acwing.com/media/article/image/2021/12/02/1_daccabdc53-blink.png";
        }
    }
    add_listening_events() {
        ...
        this.playground.game_map.$canvas.mousedown(function(e) {
            ...
            else if (e.which === 1) {
                ...
                else if (outer.cur_skill === "blink") {
                    outer.blink(tx, ty);
                    // 同步函数
                    if (outer.playground.mode === "multi mode") {
                        outer.playground.mps.send_blink(tx, ty);
                    }
                    outer.blink_coldtime = 5;
                }
            }
            outer.cur_skill = null; //清空当前技能
        });
        $(window).keydown(function(e) {
            ...
            else if (e.which === 70) {    //f键
                if (outer.blink_coldtime >= outer.eps) return true;
                outer.cur_skill = "blink";
                return false;
            }
        });
    }
    ...
    blink(tx, ty) {
        let d = this.get_dist(this.x, this.y, tx, ty);
        d = Math.min(d, 0.5);
        let angle = Math.atan2(ty - this.y, tx - this.x);
        this.x += d * Math.cos(angle);
        this.y += d * Math.sin(angle);

        this.move_length = 0;   //闪现完停下来
    }
    ...
    render_skill_coldtime() {
        ...
        x = 1.62, y = 0.9, r = 0.04;
        // 闪现技能
        // 渲染技能图标
        this.ctx.save();
        this.ctx.beginPath();
        this.ctx.arc(x * scale, y * scale, r * scale, 0, Math.PI * 2, false);
        this.ctx.stroke();
        this.ctx.clip();
        this.ctx.drawImage(this.blink_img, (x - r) * scale, (y - r) * scale, r * 2 * scale, r * 2 * scale);
        this.ctx.restore();
    
        // 渲染冷却指示
        if (this.blink_coldtime >= this.eps){
            this.ctx.beginPath();
            this.ctx.moveTo(x * scale, y * scale);
            this.ctx.arc(x * scale, y * scale, r * scale, 0 - Math.PI / 2, Math.PI * 2 * (1 - this.blink_coldtime / 5) - Math.PI / 2, true);
            this.ctx.lineTo(x * scale, y * scale);
            this.ctx.fillStyle = "rgba(0, 0, 255, 0.6)";
            this.ctx.fill();
        }
    }
}
```

---

##### 联机部分

```
js/src/playground/socket/acgame/


class MultiPlayerSocket {
    ...
    send_blink(tx, ty) {
        let outer = this;
        this.ws.send(JSON.stringify({
            'event': "blink",
            'uuid': outer.uuid,
            'tx': tx,
            'ty': ty,
        }));
    }
    receive_blink(uuid, tx, ty) {
        let player = this.get_player(uuid);
        if (player) {
            player.blink(tx, ty);
        }
    }
}
consumers/multiplayer/index.py


...
class MultiPlayer(AsyncWebsocketConsumer):
    ...
    async def blink(self, data):
        await self.channel_layer.group_send(
            self.room_name,
            {
                'type': "group_send_event",
                'event': "blink",
                'uuid': data['uuid'],
                'tx': data['tx'],
                'ty': data['ty'],
            }
        )

```



## 8. 实现聊天系统

### 优化键盘绑定事件

这部分算是之前的遗留问题，先前的 `keydown` 监听事件绑定在了 `window` 上会出现一个问题



如果在一个浏览器内打开多个 `ACAPP`，此时按下键位触发 `keydown` 事件，会被浏览器内所有的 `ACAPP` 都捕获到



之前影响不大，但对此次要实现的聊天系统就有着致命的影响，即打开一个 `ACAPP` 的聊天栏，其他都会被打开



所有我们要将 `keydown` 监听事件绑定到 `canvas` 上

`/home/acs/acapp/game/static/js/src/playground/player/zbase.js`

```javascript
class Player extends AcGameObject {
    ...

    add_listening_events() {
        ...
        this.playground.game_map.$canvas.keydown(function (e) {
            if (outer.playground.state !== "fighting")
                return true;

            if (e.which === 81) { // q
                if (outer.fireball_coldtime >= outer.eps)
                    return true;
                outer.cur_skill = "fireball";
                return false;
            } else if (e.which === 70) { // f
                if (outer.blink_coldtime >= outer.eps)
                    return true;
                outer.cur_skill = "blink";
                return false;
            }
        });
    }

    ...
}
```



`/home/acs/acapp/game/static/js/src/playground/game_map/zbase.js`

```javascript
class GameMap extends AcGameObject {
    constructor(playground) {
        ...
        this.$canvas = $(`<canvas tabindex=0></canvas>`);
        ...
    }
    start() {
        this.$canvas.focus();
    }
}
```

---

### 本地前端

要实现两个部分：

1. 文本输入框（让用户输入要发送的信息）
2. 历史记录显示框（之前用户发送的信息的显示框）

欲实现逻辑：用户按下 `<Enter>` 后，游戏界面弹出文本输入框，然后聚焦于文本输入框，且同时弹出历史记录显示框 3 秒

然后用户输入信息后，按下 `<Enter>` 后发出信息，接着信息会显示在历史记录显示框最下方，并弹出历史记录显示框 3 秒

`/home/acs/acapp/game/static/js/src/playground/chat_field/zbase.js`

```javascript
class ChatField {
    constructor(playground) {
        this.playground = playground;

        this.$history = $(`<div class="ac-game-chat-field-history"></div>`);
        this.$input = $(`<input type="text" class="ac-game-chat-field-input">`);

        this.$history.hide();
        this.$input.hide();

        this.func_id = null;

        this.playground.$playground.append(this.$history);
        this.playground.$playground.append(this.$input);

        this.start();
    }

    start() {
        this.add_listening_events();
    }
    add_listening_events() {
        let outer = this;
        this.$input.keydown(function(e) {
            if (e.which === 27) {   //ESC
                outer.hide_input();
                return false;
            } else if (e.which === 13) {
                let username = outer.playground.root.settings.username;
                let text = outer.$input.val();
                if (text) {
                    outer.$input.val("");
                    outer.add_message(username, text);
                }
                return false;
            }
        });
    }
    show_history() {
        let outer = this;
        this.$history.fadeIn();
        if (this.func_id) clearTimeout(this.func_id);
        this.func_id = setTimeout(function() {
            outer.$history.fadeOut();
            outer.func_id = null;
        }, 3000);
    }
    render_message(message) {
        return $(`<div>${message}</div>`);
    }
    add_message(username, text) {
        this.show_history();
        let message = `[${username}] ${text}`;
        this.$history.append(this.render_message(message));
        this.$history.scrollTop(this.$history[0].scrollHeight);
    }
    show_input() {
        this.show_history();
        this.$input.show();
        this.$input.focus();    //输入时，聚焦于输入框
    }
    hide_input() {
        this.$input.hide();
        this.playground.game_map.$canvas.focus();   //退出时，聚焦回游戏界面
    }
}
```



`/home/acs/acapp/game/static/js/src/playground/zbase.js`

```javascript
class AcGamePlayground {
    ...
    show(mode) {    //打开 playground 界面
        ...
        else if (mode === "multi mode") {
            this.chat_field = new ChatField(this);
            ...
        }

    }
}
```





`/home/acs/acapp/game/static/js/src/playground/player/zbase.js`

```javascript
class Player extends AcGameObject {
    ...
    add_listening_events() {
        ...
        this.playground.game_map.$canvas.keydown(function(e) {
            if (e.which === 13) {   // enter (显示对话框)
                if (outer.playground.mode === "multi mode") {
                    outer.playground.chat_field.show_input();
                    return false;
                }
            } else if (e.which === 27) {    //esc（关闭对话框）
                if (outer.playground.mode === "multi mode") {
                    outer.playground.chat_field.hide_input();
                    return false;
                }
            }
            ...
        }
    }
}
```



`/home/acs/acapp/game/static/css/game.css`

```css
...
.ac-game-chat-field-history {
    position: absolute;
    top: 66%;
    left: 20%;
    transform: translate(-50%, -50%);
    width: 20%;
    height: 32%;
    color: white;
    font-size: 2vh;
    padding: 5px;
    overflow: auto;
}

.ac-game-chat-field-history::-webkit-scrollbar {
    width: 0;
}

.ac-game-chat-field-input {
    position: absolute;
    top: 86%;
    left: 20%;
    transform: translate(-50%, -50%);
    width: 20%;
    height: 3vh;
    color: white;
    font-size: 2vh;
    background-color: rgba(222,225,230, 0.2);
}
```

---

### 联机聊天窗

经过前几节课的洗礼，这个就很简单了，不需要看视频相信也可以独立完成

#### 前端

`playground/chat_field/zbase.js`

```javascript
class ChatField {
    ...
    add_listening_events() {
        ...
        this.$input.keydown(function(e) {
            ...
            else if (e.which === 13) {
                ...
                if (text) {
                    ...
                    outer.playground.mps.send_message(text);
                }
                ...
            }
        });
    }
    ...
}
```

`js/src/playground/socket/multiplayer/`

```javascript
class MultiPlayerSocket {
    ...
    send_message(text) {
        let outer = this;
        this.ws.send(JSON.stringify({
            'event': "message",
            'uuid': outer.uuid,
            'username': outer.playground.root.settings.username,
            'text': text,
        }));
    }
    receive_message(username, text) {
        this.playground.chat_field.add_message(username, text);
    }
}
```

---

#### 后端

`consumers/multiplayer/index.py`

```python
class MultiPlayer(AsyncWebsocketConsumer):
    ...
    async def message(self, data):
        await self.channel_layer.group_send(
            self.room_name,
            {
                'type': "group_send_event",
                'event': "message",
                'uuid': data['uuid'],
                'username': data['username'],
                'text': data['text'],
            }
        )
```

---

## 8.1 拓展：实现聊天室

基于现有的多人模式聊天系统，我们可以创建一个独立的聊天室。

### 第1步：修改菜单界面 - 添加聊天室按钮

在 `game/static/js/src/menu/zbase.js` 中：

```javascript
// 在 AcGameMenu 类的构造函数中，修改 $menu 的 HTML 结构
// 在多人模式按钮后面添加聊天室按钮：

this.$menu = $(`
<div class="ac-game-menu">
     <div class="ac-game-menu-guide">
            <!-- 操作指南内容保持不变 -->
     </div>

    <div class="ac-game-menu-field">
        <div class="ac-game-menu-field-item ac-game-menu-field-item-single-mode">
            单人模式
        </div>
        <br>
        <div class="ac-game-menu-field-item ac-game-menu-field-item-multi-mode">
            多人模式
        </div>
        <br>
        <div class="ac-game-menu-field-item ac-game-menu-field-item-chatroom">
            聊天室
        </div>
        <br>
        <div class="ac-game-menu-field-item ac-game-menu-field-item-settings">
            设置
        </div>
        <br>
        <div class="ac-game-menu-field-item ac-game-menu-field-item-exit">
            退出登录
        </div>
    </div>
</div>
`);

// 在构造函数中添加聊天室按钮的引用
this.$chatroom = this.$menu.find('.ac-game-menu-field-item-chatroom');

// 在 add_listening_events() 方法中添加聊天室按钮的点击事件
this.$chatroom.click(function () {
    outer.hide();
    outer.root.chatroom.show();  // 显示聊天室界面
});
```

---

### 第2步：创建聊天室类

创建新文件 `game/static/js/src/chatroom/zbase.js`：

```javascript
class AcGameChatRoom {
    constructor(root) {
        this.root = root;
        this.$chatroom = $(`
            <div class="ac-game-chatroom">
                <div class="ac-game-chatroom-container">
                    <div class="ac-game-chatroom-header">
                        <h2>游戏聊天室</h2>
                        <button class="ac-game-chatroom-close">×</button>
                    </div>
                    <div class="ac-game-chatroom-messages">
                        <!-- 消息将显示在这里 -->
                    </div>
                    <div class="ac-game-chatroom-input-area">
                        <input type="text" class="ac-game-chatroom-input" placeholder="输入消息...">
                        <button class="ac-game-chatroom-send">发送</button>
                    </div>
                    <div class="ac-game-chatroom-online-users">
                        <h3>在线用户</h3>
                        <div class="ac-game-chatroom-users-list">
                            <!-- 在线用户列表 -->
                        </div>
                    </div>
                </div>
            </div>
        `);
        
        this.$chatroom.hide();
        this.root.$ac_game.append(this.$chatroom);
        
        // 获取DOM元素引用
        this.$messages = this.$chatroom.find('.ac-game-chatroom-messages');
        this.$input = this.$chatroom.find('.ac-game-chatroom-input');
        this.$send_btn = this.$chatroom.find('.ac-game-chatroom-send');
        this.$close_btn = this.$chatroom.find('.ac-game-chatroom-close');
        this.$users_list = this.$chatroom.find('.ac-game-chatroom-users-list');
        
        this.socket = null;  // WebSocket连接
        this.start();
    }
    
    start() {
        this.add_listening_events();
    }
    
    add_listening_events() {
        let outer = this;
        
        // 关闭按钮
        this.$close_btn.click(function() {
            outer.hide();
            outer.root.menu.show();
        });
        
        // 发送按钮
        this.$send_btn.click(function() {
            outer.send_message();
        });
        
        // 输入框回车发送
        this.$input.keydown(function(e) {
            if (e.which === 13) {  // Enter键
                outer.send_message();
                return false;
            }
        });
        
        // ESC键退出
        $(window).keydown(function(e) {
            if (e.which === 27 && outer.$chatroom.is(':visible')) {  // ESC键
                outer.hide();
                outer.root.menu.show();
            }
        });
    }
    
    send_message() {
        let message = this.$input.val().trim();
        if (message && this.socket) {
            this.socket.send_message(message);
            this.$input.val('');
        }
    }
    
    add_message(username, message, is_system = false) {
        let message_class = is_system ? 'system-message' : 'user-message';
        let $message = $(`
            <div class="ac-game-chatroom-message ${message_class}">
                <span class="message-username">${username}:</span>
                <span class="message-content">${message}</span>
            </div>
        `);
        
        this.$messages.append($message);
        // 自动滚动到底部
        this.$messages.scrollTop(this.$messages[0].scrollHeight);
    }
    
    update_users_list(users) {
        this.$users_list.empty();
        for (let user of users) {
            let $user = $(`
                <div class="ac-game-chatroom-user">
                    <img src="${user.photo}" alt="${user.username}">
                    <span>${user.username}</span>
                </div>
            `);
            this.$users_list.append($user);
        }
    }
    
    show() {
        this.$chatroom.show();
        this.$input.focus();
        
        // 连接WebSocket
        if (!this.socket) {
            this.socket = new ChatRoomSocket(this);
        }
    }
    
    hide() {
        this.$chatroom.hide();
        
        // 断开WebSocket连接
        if (this.socket) {
            this.socket.close();
            this.socket = null;
        }
    }
}
```

---

### 第3步：创建聊天室WebSocket类

创建新文件 `game/static/js/src/chatroom/socket/zbase.js`：

```javascript
class ChatRoomSocket {
    constructor(chatroom) {
        this.chatroom = chatroom;
        this.ws = new WebSocket("wss://app7549.acapp.acwing.com.cn/wss/chatroom/");
        
        this.username = this.chatroom.root.settings.username;
        this.photo = this.chatroom.root.settings.photo;
        
        this.start();
    }
    
    start() {
        this.add_listening_events();
    }
    
    add_listening_events() {
        let outer = this;
        
        // 连接建立
        this.ws.onopen = function() {
            console.log("聊天室连接已建立");
            // 发送用户信息
            outer.send_join();
        };
        
        // 接收消息
        this.ws.onmessage = function(e) {
            let data = JSON.parse(e.data);
            outer.receive(data);
        };
        
        // 连接关闭
        this.ws.onclose = function() {
            console.log("聊天室连接已关闭");
        };
        
        // 连接错误
        this.ws.onerror = function(e) {
            console.error("聊天室连接错误:", e);
        };
    }
    
    receive(data) {
        let event = data.event;
        
        switch(event) {
            case "join":
                this.receive_join(data);
                break;
            case "leave":
                this.receive_leave(data);
                break;
            case "message":
                this.receive_message(data);
                break;
            case "users_list":
                this.receive_users_list(data);
                break;
        }
    }
    
    // 发送加入聊天室消息
    send_join() {
        this.ws.send(JSON.stringify({
            'event': 'join',
            'username': this.username,
            'photo': this.photo
        }));
    }
    
    // 发送聊天消息
    send_message(message) {
        this.ws.send(JSON.stringify({
            'event': 'message',
            'username': this.username,
            'message': message
        }));
    }
    
    // 发送离开消息
    send_leave() {
        if (this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                'event': 'leave',
                'username': this.username
            }));
        }
    }
    
    // 接收用户加入
    receive_join(data) {
        this.chatroom.add_message('系统', `${data.username} 加入了聊天室`, true);
    }
    
    // 接收用户离开
    receive_leave(data) {
        this.chatroom.add_message('系统', `${data.username} 离开了聊天室`, true);
    }
    
    // 接收聊天消息
    receive_message(data) {
        this.chatroom.add_message(data.username, data.message);
    }
    
    // 接收在线用户列表
    receive_users_list(data) {
        this.chatroom.update_users_list(data.users);
    }
    
    // 关闭连接
    close() {
        this.send_leave();
        this.ws.close();
    }
}
```

---

### 第4步：添加CSS样式

创建新文件 `game/static/css/chatroom.css`：

```javascript
.ac-game-chatroom {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.8);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
}

.ac-game-chatroom-container {
    width: 90%;
    max-width: 900px;
    height: 80%;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 15px;
    display: grid;
    grid-template-rows: 60px 1fr 80px;
    grid-template-columns: 1fr 250px;
    overflow: hidden;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.ac-game-chatroom-header {
    grid-column: 1 / -1;
    background: rgba(255, 255, 255, 0.1);
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0 20px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.2);
}

.ac-game-chatroom-header h2 {
    color: white;
    margin: 0;
    font-size: 24px;
}

.ac-game-chatroom-close {
    background: transparent;
    border: none;
    color: white;
    font-size: 30px;
    cursor: pointer;
    padding: 5px 10px;
    transition: all 0.3s;
}

.ac-game-chatroom-close:hover {
    background: rgba(255, 255, 255, 0.2);
    border-radius: 5px;
}

.ac-game-chatroom-messages {
    background: rgba(255, 255, 255, 0.95);
    padding: 20px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
}

.ac-game-chatroom-message {
    margin-bottom: 10px;
    padding: 10px;
    border-radius: 10px;
    background: rgba(102, 126, 234, 0.1);
    animation: slideIn 0.3s ease;
}

@keyframes slideIn {
    from {
        opacity: 0;
        transform: translateX(-20px);
    }
    to {
        opacity: 1;
        transform: translateX(0);
    }
}

.ac-game-chatroom-message.system-message {
    background: rgba(255, 193, 7, 0.2);
    text-align: center;
    font-style: italic;
}

.message-username {
    font-weight: bold;
    color: #667eea;
    margin-right: 10px;
}

.message-content {
    color: #333;
}

.ac-game-chatroom-input-area {
    background: rgba(255, 255, 255, 0.1);
    padding: 20px;
    display: flex;
    gap: 10px;
    border-top: 1px solid rgba(255, 255, 255, 0.2);
}

.ac-game-chatroom-input {
    flex: 1;
    padding: 12px 20px;
    border: none;
    border-radius: 25px;
    background: rgba(255, 255, 255, 0.9);
    font-size: 16px;
    outline: none;
    transition: all 0.3s;
}

.ac-game-chatroom-input:focus {
    background: white;
    box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
}

.ac-game-chatroom-send {
    padding: 12px 30px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    border-radius: 25px;
    font-size: 16px;
    font-weight: bold;
    cursor: pointer;
    transition: all 0.3s;
}

.ac-game-chatroom-send:hover {
    transform: scale(1.05);
    box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
}

.ac-game-chatroom-online-users {
    grid-row: 2 / 4;
    background: rgba(255, 255, 255, 0.1);
    padding: 20px;
    border-left: 1px solid rgba(255, 255, 255, 0.2);
}

.ac-game-chatroom-online-users h3 {
    color: white;
    margin: 0 0 20px 0;
    font-size: 18px;
    text-align: center;
}

.ac-game-chatroom-users-list {
    overflow-y: auto;
    max-height: calc(100% - 40px);
}

.ac-game-chatroom-user {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px;
    margin-bottom: 10px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 10px;
    transition: all 0.3s;
}

.ac-game-chatroom-user:hover {
    background: rgba(255, 255, 255, 0.2);
}

.ac-game-chatroom-user img {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    border: 2px solid white;
}

.ac-game-chatroom-user span {
    color: white;
    font-size: 14px;
    font-weight: 500;
}

/* 滚动条样式 */
.ac-game-chatroom-messages::-webkit-scrollbar,
.ac-game-chatroom-users-list::-webkit-scrollbar {
    width: 8px;
}

.ac-game-chatroom-messages::-webkit-scrollbar-track,
.ac-game-chatroom-users-list::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 10px;
}

.ac-game-chatroom-messages::-webkit-scrollbar-thumb,
.ac-game-chatroom-users-list::-webkit-scrollbar-thumb {
    background: rgba(102, 126, 234, 0.5);
    border-radius: 10px;
}

.ac-game-chatroom-messages::-webkit-scrollbar-thumb:hover,
.ac-game-chatroom-users-list::-webkit-scrollbar-thumb:hover {
    background: rgba(102, 126, 234, 0.8);
}
```

---

### 第5步：在主游戏类中初始化聊天室

修改 `game/static/js/src/zbase.js`：

```javascript
export class AcGame{
    constructor(id, AcWingOS){
        this.id = id;
        this.$ac_game = $('#' + id);
        this.AcWingOS = AcWingOS;

        this.settings = new Settings(this);
        this.menu = new AcGameMenu(this);
        this.playground = new AcGamePlayground(this);
        this.chatroom = new AcGameChatRoom(this);  // 添加聊天室实例

        this.start();
    }

    start(){
    }
}
```

---

### 第6步：后端WebSocket处理（Django Channels）

创建后端处理文件 `game/consumers/chatroom/index.py`：

```python
from channels.generic.websocket import AsyncWebsocketConsumer
import json

class ChatRoomConsumer(AsyncWebsocketConsumer):
    # 存储在线用户
    online_users = {}
    
    async def connect(self):
        self.room_group_name = 'chatroom'
        
        # 加入聊天室组
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        # 从在线用户中移除
        if self.channel_name in self.online_users:
            username = self.online_users[self.channel_name]['username']
            del self.online_users[self.channel_name]
            
            # 通知其他用户
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_leave',
                    'username': username
                }
            )
            
            # 更新在线用户列表
            await self.send_users_list()
        
        # 离开聊天室组
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        event = data['event']
        
        if event == 'join':
            await self.handle_join(data)
        elif event == 'message':
            await self.handle_message(data)
        elif event == 'leave':
            await self.handle_leave(data)
    
    async def handle_join(self, data):
        # 添加到在线用户
        self.online_users[self.channel_name] = {
            'username': data['username'],
            'photo': data['photo']
        }
        
        # 通知所有用户有新用户加入
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_join',
                'username': data['username']
            }
        )
        
        # 发送在线用户列表
        await self.send_users_list()
    
    async def handle_message(self, data):
        # 广播消息给所有用户
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'username': data['username'],
                'message': data['message']
            }
        )
    
    async def handle_leave(self, data):
        # 处理用户主动离开
        if self.channel_name in self.online_users:
            del self.online_users[self.channel_name]
            
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_leave',
                    'username': data['username']
                }
            )
            
            await self.send_users_list()
    
    async def send_users_list(self):
        # 发送在线用户列表给所有用户
        users_list = list(self.online_users.values())
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'users_list_update',
                'users': users_list
            }
        )
    
    # 处理从channel layer接收的消息
    async def user_join(self, event):
        await self.send(text_data=json.dumps({
            'event': 'join',
            'username': event['username']
        }))
    
    async def user_leave(self, event):
        await self.send(text_data=json.dumps({
            'event': 'leave',
            'username': event['username']
        }))
    
    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'event': 'message',
            'username': event['username'],
            'message': event['message']
        }))
    
    async def users_list_update(self, event):
        await self.send(text_data=json.dumps({
            'event': 'users_list',
            'users': event['users']
        }))
```

---

### 第7步：配置WebSocket路由

在 `game/routing.py` 中添加：

```python
from django.urls import path
from game.consumers.multiplayer.index import MultiPlayer
from game.consumers.chatroom.index import ChatRoomConsumer  # 新增

websocket_urlpatterns = [
    path("wss/multiplayer/", MultiPlayer.as_asgi(), name="wss_multiplayer"),
    path("wss/chatroom/", ChatRoomConsumer.as_asgi(), name="wss_chatroom"),  # 新增
]
```

---

### 实现总结

现在我来总结一下整个实现流程：

#### 📝 **文件结构**

```
game/
├── static/
│   ├── js/
│   │   └── src/
│   │       ├── menu/zbase.js (修改)
│   │       ├── chatroom/
│   │       │   ├── zbase.js (新建)
│   │       │   └── socket/
│   │       │       └── zbase.js (新建)
│   │       └── zbase.js (修改)
│   └── css/
│       └── chatroom.css (新建)
└── consumers/
    └── chatroom/
        └── index.py (新建)
```

#### 🔧 **具体实施步骤**

1. **修改菜单**：在菜单中添加"聊天室"按钮
2. **创建聊天室类**：实现聊天室的UI和基本功能
3. **WebSocket通信**：创建客户端WebSocket连接类
4. **样式美化**：添加CSS让聊天室更美观
5. **主类集成**：在AcGame主类中初始化聊天室
6. **后端处理**：创建Django Channels消费者处理WebSocket连接
7. **路由配置**：配置WebSocket路由

#### 💡 **关键功能说明**

1. **用户加入/离开通知**：当用户进入或离开聊天室时，系统会通知所有在线用户
2. **实时消息传输**：使用WebSocket实现消息的实时推送
3. **在线用户列表**：右侧显示当前在线的所有用户
4. **优雅的UI**：采用渐变背景和动画效果，提供良好的用户体验

#### ⚠️ **注意事项**

1. 确保Django Channels已正确安装和配置
2. WebSocket URL需要根据你的服务器配置进行调整
3. 记得在HTML模板中引入新的CSS文件
4. 如果使用打包工具，确保新文件被正确打包

#### 🚀 **测试步骤**

1. 重启Django服务器
2. 登录游戏
3. 点击菜单中的"聊天室"按钮
4. 输入消息并发送
5. 打开多个浏览器窗口测试多用户聊天

## 9.1 实现匹配系统——thrift服务

### `thrift` 接口文件

`/home/acs/acapp/match_system/thrift/match.thrift`

```
namespace py match_service

service Match {
    i32 add_player(1: i32 score, 2: string uuid, 3: string username, 4: string photo, 5: string channel_name),
}
```

在 `/home/acs/acapp/match_system/src` 下执行 `thrift --gen py ../thrift/match.thrift`

之后改个名字, 叫`match_server`

---

### 服务端

配置 `asgi.py` 让服务端进程可以调用客户端进程里的函数

`acapp/acapp/asgi.py`

```
import os

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'acapp.settings')
django.setup()
...
from channels.layers import get_channel_layer
channel_layer = get_channel_layer()
...
```

---

`acapp/match_system/src/main.py` 



大家如果是在 `Pycharm` 里写的代码，在终端执行 `main.py` 时可能会出现`/usr/bin/env: 'python3\r': No such file or directory`的错误信息

解决方法：

```
1. sudo apt-get install dos2unix
2. dos2unix main.py
```





```
#! /usr/bin/env python3

import glob
import sys
sys.path.insert(0, glob.glob('../../')[0])

from match_server.match_service import Match

from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol
from thrift.server import TServer

from queue import Queue
from time import sleep
from threading import Thread

from acapp.asgi import channel_layer
from asgiref.sync import async_to_sync
from django.core.cache import cache

queue = Queue()  # 消息队列

class Player:
    def __init__(self, score, uuid, username, photo, channel_name):
        self.score = score
        self.uuid = uuid
        self.username = username
        self.photo = photo
        self.channel_name = channel_name
        self.waiting_time = 0  # 等待时间


class Pool:
    def __init__(self):
        self.players = []

    def add_player(self, player):
        self.players.append(player)
    
    def check_match(self, a, b):
        dt = abs(a.score - b.score)
        a_max_dif = a.waiting_time * 50
        b_max_dif = b.waiting_time * 50
        return dt <= a_max_dif and dt <= b_max_dif
    
    def match_success(self, ps):
        print("Match Success: %s %s %s" % (ps[0].username, ps[1].username, ps[2].username))
        room_name = "room-%s-%s-%s" % (ps[0].uuid, ps[1].uuid, ps[2].uuid)
        players = []
        for p in ps:
            async_to_sync(channel_layer.group_add)(room_name, p.channel_name)
            players.append({
                'uuid': p.uuid,
                'username': p.username,
                'photo': p.photo,
                'hp': 100,
            })
        cache.set(room_name, players, 3600)  # 有效时间：1小时
        for p in ps:
            async_to_sync(channel_layer.group_send)(
                room_name,
                {
                    'type': "group_send_event",
                    'event': "create_player",
                    'uuid': p.uuid,
                    'username': p.username,
                    'photo': p.photo,
                }
            )
    
    def increase_waiting_time(self):
        for player in self.players:
            player.waiting_time += 1
    
    def match(self):
        while len(self.players) >= 3:
            self.players = sorted(self.players, key=lambda p: p.score)
            flag = False
            for i in range(len(self.players) - 2):
                a, b, c = self.players[i], self.players[i + 1], self.players[i + 2]
                if self.check_match(a, b) and self.check_match(a, c) and self.check_match(b, c):
                    self.match_success([a, b, c])
                    self.players = self.players[:i] + self.players[i + 3:]
                    flag = True
                    break
            if not flag:
                break
    
        self.increase_waiting_time()



class MatchHandler:
    def add_player(self, score, uuid, username, photo, channel_name):
        print("Add Player: %s %d" % (username, score))
        player = Player(score, uuid, username, photo, channel_name)
        queue.put(player)
        return 0


def get_player_from_queue():
    try:
        return queue.get_nowait()
    except:
        return None


def worker():
    pool = Pool()
    while True:
        player = get_player_from_queue()
        if player:
            pool.add_player(player)
        else:
            pool.match()
            sleep(1)



if __name__ == '__main__':
    handler = MatchHandler()
    processor = Match.Processor(handler)
    transport = TSocket.TServerSocket(host='127.0.0.1', port=9090)
    tfactory = TTransport.TBufferedTransportFactory()
    pfactory = TBinaryProtocol.TBinaryProtocolFactory()

    server = TServer.TThreadedServer(
        processor, transport, tfactory, pfactory)
    
    Thread(target=worker, daemon=True).start()
    
    print('Starting the server...')
    server.serve()
    print('done.')
```

---

### 客户端

扩展数据库表，让其可以存放 `rank分` 的信息

`game/models/player/player.py`

```
...
class Player(models.Model):
    ...
    score = models.IntegerField(default=1500)
    ...
```

---

`consumers/multiplayer/index.py`

```
from channels.generic.websocket import AsyncWebsocketConsumer
import json
from django.conf import settings
from django.core.cache import cache

from thrift import Thrift
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol

from match_system.src.match_server.match_service import Match
from game.models.player.player import Player
from channels.db import database_sync_to_async

class MultiPlayer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def disconnect(self, close_code):
        if self.room_name:
            await self.channel_layer.group_discard(self.room_name, self.channel_name)
    
    async def create_player(self, data):
        self.room_name = None
        self.uuid = data['uuid']
        # Make socket
        transport = TSocket.TSocket('127.0.0.1', 9090)
        # Buffering is critical. Raw sockets are very slow
        transport = TTransport.TBufferedTransport(transport)
    
        # Wrap in a protocol
        protocol = TBinaryProtocol.TBinaryProtocol(transport)
    
        # Create a client to use the protocol encoder
        client = Match.Client(protocol)
    
        def db_get_player():
            return Player.objects.get(user__username=data['username'])
    
        player = await database_sync_to_async(db_get_player)()
    
        # Connect!
        transport.open()
    
        client.add_player(player.score, data['uuid'], data['username'], data['photo'], self.channel_name)
    
        # Close!
        transport.close()
    
    async def group_send_event(self, data):
        if not self.room_name:
            keys = cache.keys('*%s*' % (self.uuid))
            if keys:
                self.room_name = keys[0]
        await self.send(text_data=json.dumps(data))
    ...
```

## 9.2 实现匹配系统——项目收尾

### 1. 加密、压缩 `js` 代码

安装 `terser` :

```
sudo apt-get update
sudo apt-get install npm
sudo npm install terser -g
```



`terser` 不仅支持文件输入，也支持标准输入。结果会输出到标准输出中。

使用方式：

```
terser xxx.js -c -m
```


我们将整合 js 文件的脚本修改一下即可：

`scripts/compress_game_js.sh`

```bash
#! /bin/bash

JS_PATH=/home/acs/acapp/game/static/js/
JS_PATH_DIST=${JS_PATH}dist/
JS_PATH_SRC=${JS_PATH}src/

find $JS_PATH_SRC -type f -name '*.js' | sort | xargs cat | terser -c -m > ${JS_PATH_DIST}game.js

echo "yes" | python3 manage.py collectstatic
```

---

### 2. 清理监听函数

在 `AcAPP` 关闭之前触发的事件可以通过如下api添加：

```javascript
AcWingOS.api.window.on_close(func);
```




注意：

* 同一个页面中，多个`acapp`引入的 `js` 代码只会加载一次，因此 `AC_GAME_OBJECTS` 等全局变量是同一个页面、同一个 `acapp` 的所有窗口共用的。
* 各自创建的局部变量是独立的，比如 `new AcGame()` 创建出的对象各个窗口是独立的。
  我们给每一个窗口创建一个 `uid` 然后根据不同的 `uid` 进行事件解绑

 `playground/zbase.js`

```javascript
class AcGamePlayground {
    ...
    create_uuid() {
        let res = "";
        for (let i = 0; i < 8; i ++ ) {
            let x = parseInt(Math.floor(Math.random() * 10));   //[0, 10)
            res += x;
        }
        return res;
    }
    start() {
        let outer = this;
        let uuid = this.create_uuid();
        $(window).on(`resize.${uuid}`, function() {
            outer.resize();
        });

        if (this.root.AcWingOS) {
            outer.root.AcWingOS.api.window.on_close(function() {
                $(window).off(`resize.${uuid}`);
            });
        }
    }
    ...
}
```

---

### 3. 编写每局游戏的结束界面

单独创建一个结束界面，然后游戏结束的时候渲染出该结束界面即可

因为结束界面要覆盖在游戏界面之上，因此我们需要先修改一下游戏引擎，添加一个 `late_update`

在每一帧渲染的内容最后再渲染，从而实现结束界面叠加在游戏界面之上的效果



`ac_game_object/zbase.js`


```
...
class AcGameObject {
    ...
    late_update() { //每一帧均会执行一次，且在所有 update 执行完后才执行

    }
    ...
}
...
let AC_GAME_ANIMATION = function(timestamp) {
    ...
    for (let i = 0; i < AC_GAME_OBJECTS.length; i ++ ) {
        let obj = AC_GAME_OBJECTS[i];
        obj.late_update();
    }
    ...
}
...
```


然后我们做一个渲染出结束界面的类

`playground/score_board/zbase.js`

```
class ScoreBoard extends AcGameObject {
    constructor(playground) {
        super();
        this.playground = playground;
        this.ctx = this.playground.game_map.ctx;

        this.state = null;  // win-胜利；lose-失败
    
        this.win_img = new Image();
        this.win_img.src = "https://cdn.acwing.com/media/article/image/2021/12/17/1_8f58341a5e-win.png";
    
        this.lose_img = new Image();
        this.lose_img.src = "https://cdn.acwing.com/media/article/image/2021/12/17/1_9254b5f95e-lose.png";
    }
    start() {
    }
    
    add_listening_events() {    //点击后，返回主页面
        let outer = this;
        let $canvas = this.playground.game_map.$canvas;
    
        $canvas.on('click', function() {
            outer.playground.hide();
            outer.playground.root.menu.show();
        });
    }
    
    win() {
        this.state = "win";
        let outer = this;
        setTimeout(function() {
            outer.add_listening_events();
        }, 1000);   //1秒后监听点击事件
    }
    
    lose() {
        this.state = "lose";
        let outer = this;
        setTimeout(function() {
            outer.add_listening_events();
        }, 1000);   //1秒后监听点击事件
    }
    
    late_update() {
        this.render();  //渲染在图层最上方
    }
    render() {
        let len = this.playground.height / 2;
        if (this.state === "win") {
            this.ctx.drawImage(this.win_img, this.playground.width / 2 - len / 2, this.playground.height / 2 - len / 2, len, len);
        } else if (this.state === "lose") {
            this.ctx.drawImage(this.lose_img, this.playground.width / 2 - len / 2, this.playground.height / 2 - len / 2, len, len);
        }
    }
}
```


通过游戏结束的逻辑判断，渲染结束界面，同时在结束并返回主菜单的时候，重置游戏元素

#### 游戏元素重置

`playground/zbase.js`

```
class AcGamePlayground {
    ...
    show(mode) {    //打开 playground 界面
        ...
        this.score_board = new ScoreBoard(this);
        ...
    }
    ...
    hide() {
        //清空所有游戏元素
        while (this.players && this.players.length > 0) {
            this.players[0].destroy();
        }
        if (this.game_map) {
            this.game_map.destroy();
            this.game_map = null;
        }
        if (this.notice_board) {
            this.notice_board.destroy();
            this.notice_board = null;
        }
        if (this.score_board) {
            this.score_board.destroy();
            this.score_board = null;
        }
        this.$playground.empty();   //清空所有html标签
        this.$playground.hide();
    }
}
```



#### 游戏结束的逻辑判断

`playground/player/zbase.js`

```
class Player extends AcGameObject {
    ...
    update() {
        ...
        this.update_win();
        ...
    }
    update_win() {
        // 竞赛状态，且只有一名玩家，且改名玩家就是我，则胜利
        if (this.playground.state === "fighting" && this.character === "me" && this.playground.players.length === 1) {
            this.playground.state = "over";
            this.playground.score_board.win();
        }
    }
    ...
    on_destroy() {
        // 我死亡，且游戏处于竞赛状态，则失败
        if (this.character === "me" && this.playground.state === "fighting") {
            this.playground.state = "over"
            this.playground.score_board.lose();
        }
        ...
    }
}
```

---

### 更新战绩

这里我们完全交给后端来判断

在处理广播的 `attack` 信息的时候，先前我们额外留了一个参数 `hp`

围绕该 `hp` 进行续写，若当前房间内 `hp` 大于 0 的玩家少于等于 1 个

则对于所有 `hp` 为 0 的玩家减 rank 分，大于 0 的玩家加 rank 分



`consumers/multiplayer/index.py`

```python
...
class MultiPlayer(AsyncWebsocketConsumer):
    ...
    async def attack(self, data):
        if not self.room_name:
            return
        players = cache.get(self.room_name)

        if not players:
            return

        for player in players:
            if player['uuid'] == data['attackee_uuid']:
                player['hp'] -= 25

        remain_cnt = 0
        for player in players:
            if player['hp'] > 0:
                remain_cnt += 1

        if remain_cnt > 1:  # 继续进行游戏
            if self.room_name:
                cache.set(self.room_name, players, 3600)
        else:   # 结算 
            def db_update_player_score(username, score):
                player = Player.objects.get(user__username=username)
                player.score += score
                player.save()
            for player in players:
                if player['hp'] <= 0:
                    await database_sync_to_async(db_update_player_score)(player['username'], -5)
                else:
                    await database_sync_to_async(db_update_player_score)(player['username'], 10)
        ...
    ...
```





# 拓展功能1：Leaderboard

## 第一步：创建后端API接口

首先，我们需要创建一个获取排行榜数据的API接口。

### 1.1 创建排行榜视图文件

创建文件 `game/views/settings/ranklist.py`：

```python
from django.http import JsonResponse
from django.core.paginator import Paginator
from game.models.player.player import Player

def get_ranklist(request):
    """获取排行榜数据"""
    try:
        # 获取页码，默认第1页
        page = request.GET.get('page', 1)
        page_size = 20  # 每页显示20条
        
        # 按score降序排序获取所有玩家
        players = Player.objects.all().order_by('-score')
        
        # 创建分页器
        paginator = Paginator(players, page_size)
        
        # 获取当前页数据
        try:
            current_page = paginator.page(page)
        except:
            current_page = paginator.page(1)
        
        # 构建返回数据
        ranklist = []
        # 计算当前页第一条数据的排名
        base_rank = (current_page.number - 1) * page_size
        
        for index, player in enumerate(current_page.object_list):
            ranklist.append({
                'rank': base_rank + index + 1,
                'username': player.user.username,
                'photo': player.photo,
                'score': player.score,
            })
        
        return JsonResponse({
            'result': 'success',
            'ranklist': ranklist,
            'total_players': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': current_page.number,
            'has_next': current_page.has_next(),
            'has_previous': current_page.has_previous(),
        })
        
    except Exception as e:
        return JsonResponse({
            'result': 'error',
            'message': str(e)
        })
```

### 1.2 添加URL路由

修改 `game/urls/settings/index.py`，添加排行榜路由：

```python
from django.urls import path, include
from game.views.settings.getinfo import getinfo
from game.views.settings.login import signin
from game.views.settings.logout import signout
from game.views.settings.register import register
from game.views.settings.ranklist import get_ranklist  # 新增导入

urlpatterns = [
    path('getinfo/', getinfo, name='settings_getinfo'),
    path('login/', signin, name='settings_login'),
    path('logout/', signout, name='settings_logout'),
    path('register/', register, name='settings_register'),
    path('ranklist/', get_ranklist, name='settings_ranklist'),  # 新增路由
    path("acwing/", include("game.urls.settings.acwing.index")),
    path("github/", include("game.urls.settings.github.index")),
    path("gitee/", include("game.urls.settings.gitee.index")),
]
```

## 第二步：创建前端排行榜组件

### 2.1 创建排行榜JavaScript文件

创建文件 `game/static/js/src/leaderboard/zbase.js`：

```javascript
class AcGameLeaderboard {
    constructor(root) {
        this.root = root;
        this.current_page = 1;
        this.total_pages = 1;
        
        this.$leaderboard = $(`
            <div class="ac-game-leaderboard" style="display: none;">
                <div class="ac-game-leaderboard-container">
                    <div class="ac-game-leaderboard-header">
                        <h2 class="ac-game-leaderboard-title">
                            <span class="ac-game-leaderboard-icon">🏆</span>
                            排行榜
                        </h2>
                        <button class="ac-game-leaderboard-close">×</button>
                    </div>
                    <div class="ac-game-leaderboard-content">
                        <div class="ac-game-leaderboard-table"></div>
                    </div>
                    <div class="ac-game-leaderboard-pagination">
                        <div class="ac-game-leaderboard-page-info"></div>
                        <div class="ac-game-leaderboard-page-buttons"></div>
                    </div>
                </div>
            </div>
        `);
        
        this.$leaderboard.hide();
        this.root.$ac_game.append(this.$leaderboard);
        
        this.$table = this.$leaderboard.find('.ac-game-leaderboard-table');
        this.$page_info = this.$leaderboard.find('.ac-game-leaderboard-page-info');
        this.$page_buttons = this.$leaderboard.find('.ac-game-leaderboard-page-buttons');
        this.$close_btn = this.$leaderboard.find('.ac-game-leaderboard-close');
        
        this.start();
    }
    
    start() {
        this.add_listening_events();
    }
    
    add_listening_events() {
        let outer = this;
        
        // 关闭按钮
        this.$close_btn.click(function() {
            outer.hide();
            outer.root.menu.show();
        });
        
        // ESC键关闭
        $(window).keydown(function(e) {
            if (e.which === 27 && outer.$leaderboard.is(':visible')) {
                outer.hide();
                outer.root.menu.show();
            }
        });
    }
    
    show() {
        this.$leaderboard.show();
        this.load_ranklist(1);
    }
    
    hide() {
        this.$leaderboard.hide();
    }
    
    load_ranklist(page) {
        let outer = this;
        
        // 显示加载中
        this.$table.html('<div class="ac-game-leaderboard-loading">加载中...</div>');
        
        $.ajax({
            url: "https://app7549.acapp.acwing.com.cn/settings/ranklist/",
            type: "GET",
            data: {
                page: page
            },
            success: function(resp) {
                if (resp.result === "success") {
                    outer.render_ranklist(resp);
                } else {
                    outer.$table.html('<div class="ac-game-leaderboard-empty">加载失败</div>');
                }
            },
            error: function() {
                outer.$table.html('<div class="ac-game-leaderboard-empty">网络错误</div>');
            }
        });
    }
    
    render_ranklist(data) {
        let outer = this;
        
        // 清空表格
        this.$table.empty();
        
        // 渲染排行榜数据
        if (data.ranklist.length === 0) {
            this.$table.html(`
                <div class="ac-game-leaderboard-empty">
                    <div class="ac-game-leaderboard-empty-icon">📭</div>
                    <div>暂无数据</div>
                </div>
            `);
            return;
        }
        
        // 渲染每一行
        data.ranklist.forEach(function(player) {
            let rank_class = "";
            if (player.rank === 1) rank_class = "rank-1";
            else if (player.rank === 2) rank_class = "rank-2";
            else if (player.rank === 3) rank_class = "rank-3";
            
            let rank_display = player.rank;
            if (player.rank <= 3) {
                rank_display = player.rank;
            }
            
            let $row = $(`
                <div class="ac-game-leaderboard-row ${rank_class}">
                    <div class="ac-game-leaderboard-rank">${rank_display}</div>
                    <div class="ac-game-leaderboard-user">
                        <img class="ac-game-leaderboard-avatar" 
                             src="${player.photo}" 
                             alt="${player.username}"
                             onerror="this.src='https://app7549.acapp.acwing.com.cn/static/image/favicon/favicon.png'">
                        <span class="ac-game-leaderboard-username">${player.username}</span>
                    </div>
                    <div class="ac-game-leaderboard-score">${player.score}</div>
                </div>
            `);
            
            outer.$table.append($row);
        });
        
        // 更新分页信息
        this.current_page = data.current_page;
        this.total_pages = data.total_pages;
        
        // 更新分页显示
        let start = (data.current_page - 1) * 20 + 1;
        let end = Math.min(data.current_page * 20, data.total_players);
        this.$page_info.html(`显示 ${start}-${end} 名，共 ${data.total_players} 名玩家`);
        
        // 渲染分页按钮
        this.render_pagination(data);
    }
    
    render_pagination(data) {
        let outer = this;
        this.$page_buttons.empty();
        
        // 上一页按钮
        let $prev = $('<button class="ac-game-leaderboard-page-btn">上一页</button>');
        if (!data.has_previous) {
            $prev.prop('disabled', true);
        } else {
            $prev.click(function() {
                outer.load_ranklist(outer.current_page - 1);
            });
        }
        this.$page_buttons.append($prev);
        
        // 页码按钮
        let start_page = Math.max(1, data.current_page - 2);
        let end_page = Math.min(data.total_pages, data.current_page + 2);
        
        if (start_page > 1) {
            this.add_page_button(1);
            if (start_page > 2) {
                this.$page_buttons.append('<button class="ac-game-leaderboard-page-btn" disabled>...</button>');
            }
        }
        
        for (let i = start_page; i <= end_page; i++) {
            this.add_page_button(i);
        }
        
        if (end_page < data.total_pages) {
            if (end_page < data.total_pages - 1) {
                this.$page_buttons.append('<button class="ac-game-leaderboard-page-btn" disabled>...</button>');
            }
            this.add_page_button(data.total_pages);
        }
        
        // 下一页按钮
        let $next = $('<button class="ac-game-leaderboard-page-btn">下一页</button>');
        if (!data.has_next) {
            $next.prop('disabled', true);
        } else {
            $next.click(function() {
                outer.load_ranklist(outer.current_page + 1);
            });
        }
        this.$page_buttons.append($next);
    }
    
    add_page_button(page) {
        let outer = this;
        let $btn = $(`<button class="ac-game-leaderboard-page-btn">${page}</button>`);
        
        if (page === this.current_page) {
            $btn.addClass('active');
        } else {
            $btn.click(function() {
                outer.load_ranklist(page);
            });
        }
        
        this.$page_buttons.append($btn);
    }
}
```

## 第三步：添加排行榜样式

### 3.1 在 `game/static/css/game.css` 文件末尾添加排行榜样式

在文件末尾添加以下CSS代码：

```css
/* 排行榜样式 */
.ac-game-leaderboard {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.5);
    backdrop-filter: blur(10px);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
}

.ac-game-leaderboard-container {
    width: 90%;
    max-width: 900px;
    height: 85%;
    max-height: 700px;
    background: linear-gradient(135deg, #ffffff 0%, #f5f7fa 100%);
    border-radius: 20px;
    box-shadow: 0 25px 50px rgba(0, 0, 0, 0.15);
    display: flex;
    flex-direction: column;
    overflow: hidden;
    animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
    from {
        transform: translateY(-30px);
        opacity: 0;
    }
    to {
        transform: translateY(0);
        opacity: 1;
    }
}

.ac-game-leaderboard-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 25px 30px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.2);
}

.ac-game-leaderboard-title {
    color: white;
    font-size: 28px;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 12px;
    margin: 0;
}

.ac-game-leaderboard-icon {
    font-size: 32px;
}

.ac-game-leaderboard-close {
    background: rgba(255, 255, 255, 0.2);
    border: 2px solid rgba(255, 255, 255, 0.3);
    color: white;
    width: 40px;
    height: 40px;
    border-radius: 50%;
    font-size: 24px;
    cursor: pointer;
    transition: all 0.3s ease;
    display: flex;
    align-items: center;
    justify-content: center;
}

.ac-game-leaderboard-close:hover {
    background: rgba(255, 255, 255, 0.3);
    transform: rotate(90deg);
}

.ac-game-leaderboard-content {
    flex: 1;
    overflow-y: auto;
    padding: 20px;
}

.ac-game-leaderboard-table {
    width: 100%;
}

.ac-game-leaderboard-row {
    display: flex;
    align-items: center;
    padding: 15px 20px;
    margin-bottom: 10px;
    background: white;
    border-radius: 12px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
    transition: all 0.3s ease;
    position: relative;
    overflow: hidden;
}

.ac-game-leaderboard-row:hover {
    transform: translateX(5px);
    box-shadow: 0 4px 20px rgba(102, 126, 234, 0.15);
}

.ac-game-leaderboard-row.rank-1 {
    background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
    color: white;
}

.ac-game-leaderboard-row.rank-2 {
    background: linear-gradient(135deg, #C0C0C0 0%, #B8B8B8 100%);
    color: white;
}

.ac-game-leaderboard-row.rank-3 {
    background: linear-gradient(135deg, #CD7F32 0%, #B87333 100%);
    color: white;
}

.ac-game-leaderboard-rank {
    width: 60px;
    font-size: 20px;
    font-weight: bold;
    display: flex;
    align-items: center;
    justify-content: center;
}

.ac-game-leaderboard-row.rank-1 .ac-game-leaderboard-rank::after,
.ac-game-leaderboard-row.rank-2 .ac-game-leaderboard-rank::after,
.ac-game-leaderboard-row.rank-3 .ac-game-leaderboard-rank::after {
    content: "👑";
    margin-left: 5px;
}

.ac-game-leaderboard-user {
    flex: 1;
    display: flex;
    align-items: center;
    gap: 15px;
}

.ac-game-leaderboard-avatar {
    width: 50px;
    height: 50px;
    border-radius: 50%;
    object-fit: cover;
    border: 3px solid white;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.ac-game-leaderboard-username {
    font-size: 18px;
    font-weight: 500;
}

.ac-game-leaderboard-score {
    font-size: 22px;
    font-weight: bold;
    color: #667eea;
    min-width: 100px;
    text-align: right;
}

.ac-game-leaderboard-row.rank-1 .ac-game-leaderboard-score,
.ac-game-leaderboard-row.rank-2 .ac-game-leaderboard-score,
.ac-game-leaderboard-row.rank-3 .ac-game-leaderboard-score {
    color: white;
}

.ac-game-leaderboard-pagination {
    padding: 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: white;
    border-top: 1px solid #e5e7eb;
}

.ac-game-leaderboard-page-info {
    color: #6b7280;
    font-size: 14px;
}

.ac-game-leaderboard-page-buttons {
    display: flex;
    gap: 10px;
}

.ac-game-leaderboard-page-btn {
    padding: 8px 16px;
    background: white;
    border: 2px solid #e5e7eb;
    border-radius: 8px;
    color: #374151;
    font-size: 14px;
    cursor: pointer;
    transition: all 0.3s ease;
}

.ac-game-leaderboard-page-btn:hover:not(:disabled) {
    background: #667eea;
    color: white;
    border-color: #667eea;
}

.ac-game-leaderboard-page-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.ac-game-leaderboard-page-btn.active {
    background: #667eea;
    color: white;
    border-color: #667eea;
}

.ac-game-leaderboard-content::-webkit-scrollbar {
    width: 8px;
}

.ac-game-leaderboard-content::-webkit-scrollbar-track {
    background: #f1f1f1;
    border-radius: 10px;
}

.ac-game-leaderboard-content::-webkit-scrollbar-thumb {
    background: #667eea;
    border-radius: 10px;
}

.ac-game-leaderboard-content::-webkit-scrollbar-thumb:hover {
    background: #764ba2;
}

.ac-game-leaderboard-loading {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 200px;
    color: #667eea;
    font-size: 18px;
}

.ac-game-leaderboard-empty {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    height: 200px;
    color: #9ca3af;
}

.ac-game-leaderboard-empty-icon {
    font-size: 48px;
    margin-bottom: 10px;
}
```

## 第四步：集成到主项目

### 4.1 修改菜单文件，添加排行榜按钮

修改 `game/static/js/src/menu/zbase.js`，在菜单中添加排行榜按钮：

```javascript
class AcGameMenu {
    constructor(root) {
        this.root = root;
        this.$menu = $(`
<div class="ac-game-menu">
     <div class="ac-game-menu-guide">
            <!-- 操作指南保持不变 -->
            ...
        </div>

    <div class="ac-game-menu-field">
        <div class="ac-game-menu-field-item ac-game-menu-field-item-single-mode">
            单人模式
        </div>
        <br>
        <div class="ac-game-menu-field-item ac-game-menu-field-item-multi-mode">
            多人模式
        </div>
        <br>
        <div class="ac-game-menu-field-item ac-game-menu-field-item-chatroom">
            聊天室
        </div>
        <br>
        <div class="ac-game-menu-field-item ac-game-menu-field-item-leaderboard">
            排行榜
        </div>
        <br>
        <div class="ac-game-menu-field-item ac-game-menu-field-item-settings">
            设置
        </div>
        <br>
        <div class="ac-game-menu-field-item ac-game-menu-field-item-exit">
            退出登录
        </div>
    </div>
</div>
`);
        // ... 其他代码保持不变
        
        this.$leaderboard = this.$menu.find('.ac-game-menu-field-item-leaderboard'); // 新增
        
        this.start();
    }

    add_listening_events() {
        let outer = this;
        // ... 其他事件保持不变
        
        // 添加排行榜点击事件
        this.$leaderboard.click(function() {
            outer.hide();
            outer.root.leaderboard.show();
        });
        
        // ... 其他代码保持不变
    }
}
```

### 4.2 修改主文件，初始化排行榜

修改 `game/static/js/src/zbase.js`：

```javascript
export class AcGame{
    constructor(id, AcWingOS){
        this.id = id;
        this.$ac_game = $('#' + id);
        this.AcWingOS = AcWingOS;

        this.settings = new Settings(this);
        this.menu = new AcGameMenu(this);
        this.playground = new AcGamePlayground(this);
        this.chatroom = new AcGameChatRoom(this);
        this.leaderboard = new AcGameLeaderboard(this);  // 新增

        this.start();
    }

    start(){
    }
}
```

### 4.3 为排行榜按钮添加样式

在 `game/static/css/game.css` 中，找到菜单按钮的hover效果部分，为排行榜按钮添加特殊颜色：

```css
/* 排行榜 - 紫金色 */
.ac-game-menu-field-item:nth-of-type(4):hover::after {
    background: linear-gradient(90deg, #667eea, #764ba2);
}
```

## 第五步：编译和测试

### 5.1 编译JavaScript文件

运行编译脚本：

```bash
./scripts/compress_game_js.sh
```

### 5.2 重启服务

重启uwsgi和nginx服务：

```bash
uwsgi --ini scripts/uwsgi.ini
sudo /etc/init.d/nginx restart
```

现在排行榜功能应该已经成功集成到项目中了！你可以：

1. 访问你的网站
2. 登录后进入菜单
3. 点击"排行榜"按钮
4. 查看排行榜数据和分页功能

# 拓展功能2：Settings

## 第一步：配置媒体文件存储

### 1.1 修改 Django 设置

```
# 媒体文件配置 - 存储在项目目录外
MEDIA_ROOT = '/home/acs/media/'  # 项目目录外的独立目录
MEDIA_URL = '/media/'

# 头像上传配置
AVATAR_UPLOAD_PATH = 'avatars/'  # 头像存储子目录
AVATAR_MAX_SIZE = 2 * 1024 * 1024  # 最大2MB
AVATAR_ALLOWED_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif']
```

### 1.2 创建媒体目录和设置权限

在终端中执行：

bash

```bash
# 创建媒体目录
mkdir -p /home/acs/media/avatars

# 设置权限（让 web 服务器可以写入）
chmod 755 /home/acs/media
chmod 755 /home/acs/media/avatars
```

### 1.3 配置 Nginx 处理媒体文件

编辑你的 Nginx 配置文件，添加媒体文件的处理：

nginx

```nginx
location /media {
    alias /home/acs/media;
}
```

## 第二步：安装必要的库

在终端安装 Pillow（用于图片处理）：

```bash
pip install Pillow
```

## 第三步：创建设置相关的后端 API

### 3.1 创建获取用户信息的 API

`game/views/settings/get_user_settings.py`

```python
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
```

### 3.2 创建检查用户名是否可用的 API

 `game/views/settings/check_username.py`

```python
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

@login_required
def check_username(request):
    """检查用户名是否可用"""
    username = request.GET.get('username', '').strip()
    
    if not username:
        return JsonResponse({
            'result': 'error',
            'available': False,
            'message': '用户名不能为空'
        })
    
    if len(username) < 3:
        return JsonResponse({
            'result': 'error',
            'available': False,
            'message': '用户名至少需要3个字符'
        })
    
    if len(username) > 20:
        return JsonResponse({
            'result': 'error',
            'available': False,
            'message': '用户名不能超过20个字符'
        })
    
    # 检查是否是当前用户的用户名
    if username == request.user.username:
        return JsonResponse({
            'result': 'success',
            'available': True,
            'message': '当前用户名'
        })
    
    # 检查用户名是否已存在
    if User.objects.filter(username=username).exists():
        return JsonResponse({
            'result': 'error',
            'available': False,
            'message': '用户名已被使用'
        })
    
    return JsonResponse({
        'result': 'success',
        'available': True,
        'message': '用户名可用'
    })
```

### 3.3 创建更新用户名的 API

`game/views/settings/update_username.py`

```python
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
```

### 3.4 创建更新密码的 API

`game/views/settings/update_password.py`

```python
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
```

### 3.5 创建上传头像的 API

```python
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.conf import settings
from game.models.player.player import Player
from PIL import Image
import os
import uuid

@require_POST
@login_required
def upload_avatar(request):
    """上传用户头像"""
    try:
        # 获取上传的文件
        avatar_file = request.FILES.get('avatar')
        
        if not avatar_file:
            return JsonResponse({
                'result': 'error',
                'message': '请选择要上传的图片'
            })
        
        # 检查文件大小
        if avatar_file.size > settings.AVATAR_MAX_SIZE:
            return JsonResponse({
                'result': 'error',
                'message': f'图片大小不能超过{settings.AVATAR_MAX_SIZE // (1024*1024)}MB'
            })
        
        # 检查文件格式
        file_ext = avatar_file.name.split('.')[-1].lower()
        if file_ext not in settings.AVATAR_ALLOWED_EXTENSIONS:
            return JsonResponse({
                'result': 'error',
                'message': f'只支持以下格式：{", ".join(settings.AVATAR_ALLOWED_EXTENSIONS)}'
            })
        
        # 生成唯一文件名
        filename = f'{request.user.id}_{uuid.uuid4().hex[:8]}.{file_ext}'
        filepath = os.path.join(settings.MEDIA_ROOT, settings.AVATAR_UPLOAD_PATH, filename)
        
        # 确保目录存在
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # 处理图片
        try:
            img = Image.open(avatar_file)
            
            # 转换为RGB（处理PNG透明通道等问题）
            if img.mode in ('RGBA', 'LA', 'P'):
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = rgb_img
            
            # 生成正方形缩略图（保持比例，裁剪中心）
            img.thumbnail((300, 300), Image.Resampling.LANCZOS)
            
            # 如果不是正方形，裁剪为正方形
            if img.width != img.height:
                min_side = min(img.width, img.height)
                left = (img.width - min_side) // 2
                top = (img.height - min_side) // 2
                right = left + min_side
                bottom = top + min_side
                img = img.crop((left, top, right, bottom))
                img = img.resize((300, 300), Image.Resampling.LANCZOS)
            
            # 保存图片
            img.save(filepath, 'JPEG', quality=85, optimize=True)
            
        except Exception as e:
            return JsonResponse({
                'result': 'error',
                'message': f'图片处理失败：{str(e)}'
            })
        
        # 删除旧头像（如果是本地上传的）
        player = Player.objects.get(user=request.user)
        old_photo = player.photo
        if old_photo and '/media/avatars/' in old_photo:
            old_filename = old_photo.split('/')[-1]
            old_filepath = os.path.join(settings.MEDIA_ROOT, settings.AVATAR_UPLOAD_PATH, old_filename)
            if os.path.exists(old_filepath):
                try:
                    os.remove(old_filepath)
                except:
                    pass  # 删除失败也不影响
        
        # 更新数据库
        new_photo_url = f'{settings.MEDIA_URL}{settings.AVATAR_UPLOAD_PATH}{filename}'
        # 构建完整URL
        new_photo_url = f'https://app7549.acapp.acwing.com.cn{new_photo_url}'
        player.photo = new_photo_url
        player.save()
        
        return JsonResponse({
            'result': 'success',
            'message': '头像上传成功',
            'photo': new_photo_url
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
```

## 第四步：配置 URL 路由

### 4.1 更新设置相关的 URL

```python
from django.urls import path, include
from game.views.settings.getinfo import getinfo
from game.views.settings.login import signin
from game.views.settings.logout import signout
from game.views.settings.register import register
from game.views.settings.ranklist import get_ranklist
from game.views.settings.get_user_settings import get_user_settings
from game.views.settings.check_username import check_username
from game.views.settings.update_username import update_username
from game.views.settings.update_password import update_password
from game.views.settings.upload_avatar import upload_avatar

urlpatterns = [
        path('getinfo/', getinfo, name='settings_getinfo'),
        path('login/', signin, name='settings_login'),
        path('logout/', signout, name='settings_logout'),
        path('register/', register, name='settings_register'),
        path("acwing/", include("game.urls.settings.acwing.index")),
        path("github/", include("game.urls.settings.github.index")),
        path("gitee/", include("game.urls.settings.gitee.index")),
        path('ranklist/', get_ranklist, name='settings_ranklist'),
        # 新增的设置相关路由
        path('get_user_settings/', get_user_settings, name='settings_get_user'),
        path('check_username/', check_username, name='settings_check_username'),
        path('update_username/', update_username, name='settings_update_username'),
        path('update_password/', update_password, name='settings_update_password'),
        path('upload_avatar/', upload_avatar, name='settings_upload_avatar'),
]
```

## 第五步：创建前端设置页面

### 5.1 创建设置页面的 CSS

`game/static/css/user-settings.css`

```css
.ac-game-user-settings {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.5);
    backdrop-filter: blur(10px);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
}

.ac-game-user-settings-container {
    width: 90%;
    max-width: 600px;
    max-height: 90vh;
    background: linear-gradient(135deg, rgba(25, 25, 35, 0.95), rgba(35, 35, 45, 0.9));
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 16px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5),
                inset 0 1px 0 rgba(255, 255, 255, 0.08);
    backdrop-filter: blur(20px);
    overflow: hidden;
    display: flex;
    flex-direction: column;
}

.ac-game-user-settings-header {
    background: linear-gradient(135deg, rgba(52, 152, 219, 0.1), rgba(41, 128, 185, 0.05));
    padding: 20px 25px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.ac-game-user-settings-title {
    color: #e4e4e7;
    font-size: 24px;
    font-weight: 500;
    font-family: 'Inter', 'Roboto', sans-serif;
    margin: 0;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.ac-game-user-settings-close {
    background: transparent;
    border: none;
    color: rgba(255, 255, 255, 0.6);
    font-size: 28px;
    cursor: pointer;
    padding: 0;
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s ease;
}

.ac-game-user-settings-close:hover {
    color: rgba(255, 255, 255, 0.9);
    transform: rotate(90deg);
}

.ac-game-user-settings-content {
    flex: 1;
    overflow-y: auto;
    padding: 25px;
}

/* 设置区块 */
.ac-game-user-settings-section {
    margin-bottom: 30px;
    padding-bottom: 20px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.ac-game-user-settings-section:last-child {
    border-bottom: none;
}

.ac-game-user-settings-section-title {
    color: #3498db;
    font-size: 16px;
    font-weight: 500;
    margin-bottom: 20px;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-family: 'Inter', 'Roboto', sans-serif;
}

/* 头像部分 */
.ac-game-user-settings-avatar-section {
    display: flex;
    align-items: center;
    gap: 25px;
}

.ac-game-user-settings-avatar-preview {
    position: relative;
    width: 100px;
    height: 100px;
}

.ac-game-user-settings-avatar-img {
    width: 100%;
    height: 100%;
    border-radius: 50%;
    object-fit: cover;
    border: 3px solid rgba(52, 152, 219, 0.3);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.ac-game-user-settings-avatar-upload {
    flex: 1;
}

.ac-game-user-settings-upload-btn {
    display: inline-block;
    padding: 10px 20px;
    background: linear-gradient(135deg, rgba(52, 152, 219, 0.8), rgba(41, 128, 185, 0.7));
    color: white;
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 8px;
    cursor: pointer;
    font-size: 14px;
    font-family: 'Inter', 'Roboto', sans-serif;
    transition: all 0.2s ease;
}

.ac-game-user-settings-upload-btn:hover {
    background: linear-gradient(135deg, rgba(52, 152, 219, 0.9), rgba(41, 128, 185, 0.8));
    transform: translateY(-1px);
    box-shadow: 0 4px 16px rgba(52, 152, 219, 0.3);
}

.ac-game-user-settings-upload-input {
    display: none;
}

.ac-game-user-settings-upload-info {
    color: rgba(228, 228, 231, 0.5);
    font-size: 12px;
    margin-top: 8px;
}

/* 表单组 */
.ac-game-user-settings-form-group {
    margin-bottom: 20px;
}

.ac-game-user-settings-label {
    display: block;
    color: rgba(228, 228, 231, 0.8);
    font-size: 14px;
    margin-bottom: 8px;
    font-family: 'Inter', 'Roboto', sans-serif;
}

.ac-game-user-settings-input-wrapper {
    position: relative;
}

.ac-game-user-settings-input {
    width: 100%;
    padding: 12px 16px;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    color: #e4e4e7;
    font-size: 14px;
    font-family: 'Inter', 'Roboto', sans-serif;
    transition: all 0.2s ease;
    box-sizing: border-box;
}

.ac-game-user-settings-input:focus {
    outline: none;
    background: rgba(255, 255, 255, 0.08);
    border-color: rgba(52, 152, 219, 0.5);
    box-shadow: 0 0 0 2px rgba(52, 152, 219, 0.1);
}

.ac-game-user-settings-input:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

/* 用户名验证状态 */
.ac-game-user-settings-username-status {
    position: absolute;
    right: 12px;
    top: 50%;
    transform: translateY(-50%);
    font-size: 18px;
}

.ac-game-user-settings-username-status.checking {
    color: #f39c12;
}

.ac-game-user-settings-username-status.available {
    color: #27ae60;
}

.ac-game-user-settings-username-status.unavailable {
    color: #e74c3c;
}

/* 提示信息 */
.ac-game-user-settings-hint {
    color: rgba(228, 228, 231, 0.5);
    font-size: 12px;
    margin-top: 6px;
}

.ac-game-user-settings-error {
    color: #e74c3c;
    font-size: 12px;
    margin-top: 6px;
}

.ac-game-user-settings-success {
    color: #27ae60;
    font-size: 12px;
    margin-top: 6px;
}

/* 按钮 */
.ac-game-user-settings-btn {
    padding: 12px 24px;
    background: linear-gradient(135deg, rgba(52, 152, 219, 0.8), rgba(41, 128, 185, 0.7));
    color: white;
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 8px;
    cursor: pointer;
    font-size: 14px;
    font-family: 'Inter', 'Roboto', sans-serif;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    transition: all 0.2s ease;
}

.ac-game-user-settings-btn:hover:not(:disabled) {
    background: linear-gradient(135deg, rgba(52, 152, 219, 0.9), rgba(41, 128, 185, 0.8));
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(52, 152, 219, 0.4);
}

.ac-game-user-settings-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.ac-game-user-settings-btn.secondary {
    background: rgba(255, 255, 255, 0.08);
    border-color: rgba(255, 255, 255, 0.2);
}

.ac-game-user-settings-btn.secondary:hover:not(:disabled) {
    background: rgba(255, 255, 255, 0.12);
}

/* 认证类型标签 */
.ac-game-user-settings-auth-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 500;
    background: rgba(255, 255, 255, 0.1);
    color: rgba(255, 255, 255, 0.8);
    margin-left: 10px;
}

.ac-game-user-settings-auth-badge.github {
    background: rgba(36, 41, 46, 0.8);
    color: #fff;
}

.ac-game-user-settings-auth-badge.gitee {
    background: rgba(200, 55, 44, 0.8);
    color: #fff;
}

.ac-game-user-settings-auth-badge.acwing {
    background: rgba(0, 122, 204, 0.8);
    color: #fff;
}

/* 滚动条样式 */
.ac-game-user-settings-content::-webkit-scrollbar {
    width: 6px;
}

.ac-game-user-settings-content::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.02);
}

.ac-game-user-settings-content::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 3px;
}

.ac-game-user-settings-content::-webkit-scrollbar-thumb:hover {
    background: rgba(255, 255, 255, 0.15);
}
```

### 5.2 创建设置页面的 JavaScript 类

`game/static/js/src/settings/user_settings/zbase.js`

```javascript
class AcGameUserSettings {
    constructor(root) {
        this.root = root;
        this.username_check_timer = null;
        this.$settings = $(`
            <div class="ac-game-user-settings" style="display: none;">
                <div class="ac-game-user-settings-container">
                    <div class="ac-game-user-settings-header">
                        <h2 class="ac-game-user-settings-title">用户设置</h2>
                        <button class="ac-game-user-settings-close">×</button>
                    </div>
                    <div class="ac-game-user-settings-content">
                        <!-- 头像设置 -->
                        <div class="ac-game-user-settings-section">
                            <h3 class="ac-game-user-settings-section-title">头像设置</h3>
                            <div class="ac-game-user-settings-avatar-section">
                                <div class="ac-game-user-settings-avatar-preview">
                                    <img class="ac-game-user-settings-avatar-img" src="" alt="头像">
                                </div>
                                <div class="ac-game-user-settings-avatar-upload">
                                    <label class="ac-game-user-settings-upload-btn">
                                        选择图片
                                        <input type="file" class="ac-game-user-settings-upload-input" accept="image/*">
                                    </label>
                                    <div class="ac-game-user-settings-upload-info">
                                        支持 JPG、PNG、GIF 格式，大小不超过 2MB
                                    </div>
                                    <div class="ac-game-user-settings-avatar-message"></div>
                                </div>
                            </div>
                        </div>

                        <!-- 基本信息 -->
                        <div class="ac-game-user-settings-section">
                            <h3 class="ac-game-user-settings-section-title">
                                基本信息
                                <span class="ac-game-user-settings-auth-badge"></span>
                            </h3>
                            <div class="ac-game-user-settings-form-group">
                                <label class="ac-game-user-settings-label">用户名</label>
                                <div class="ac-game-user-settings-input-wrapper">
                                    <input type="text" class="ac-game-user-settings-input ac-game-user-settings-username" placeholder="输入新用户名">
                                    <span class="ac-game-user-settings-username-status"></span>
                                </div>
                                <div class="ac-game-user-settings-username-message"></div>
                            </div>
                            <button class="ac-game-user-settings-btn ac-game-user-settings-username-btn">
                                更新用户名
                            </button>
                        </div>

                        <!-- 密码修改（仅本地用户显示） -->
                        <div class="ac-game-user-settings-section ac-game-user-settings-password-section" style="display: none;">
                            <h3 class="ac-game-user-settings-section-title">修改密码</h3>
                            <div class="ac-game-user-settings-form-group">
                                <label class="ac-game-user-settings-label">当前密码</label>
                                <input type="password" class="ac-game-user-settings-input ac-game-user-settings-old-password" placeholder="输入当前密码">
                            </div>
                            <div class="ac-game-user-settings-form-group">
                                <label class="ac-game-user-settings-label">新密码</label>
                                <input type="password" class="ac-game-user-settings-input ac-game-user-settings-new-password" placeholder="输入新密码（至少6位）">
                            </div>
                            <div class="ac-game-user-settings-form-group">
                                <label class="ac-game-user-settings-label">确认新密码</label>
                                <input type="password" class="ac-game-user-settings-input ac-game-user-settings-confirm-password" placeholder="再次输入新密码">
                            </div>
                            <div class="ac-game-user-settings-password-message"></div>
                            <button class="ac-game-user-settings-btn ac-game-user-settings-password-btn">
                                更新密码
                            </button>
                        </div>

                        <!-- 账号信息 -->
                        <div class="ac-game-user-settings-section">
                            <h3 class="ac-game-user-settings-section-title">账号信息</h3>
                            <div class="ac-game-user-settings-form-group">
                                <label class="ac-game-user-settings-label">积分</label>
                                <input type="text" class="ac-game-user-settings-input ac-game-user-settings-score" disabled>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `);

        this.$settings.hide();
        this.root.$ac_game.append(this.$settings);

        // 获取DOM元素
        this.$close_btn = this.$settings.find('.ac-game-user-settings-close');
        this.$avatar_img = this.$settings.find('.ac-game-user-settings-avatar-img');
        this.$avatar_input = this.$settings.find('.ac-game-user-settings-upload-input');
        this.$avatar_message = this.$settings.find('.ac-game-user-settings-avatar-message');
        
        this.$username_input = this.$settings.find('.ac-game-user-settings-username');
        this.$username_status = this.$settings.find('.ac-game-user-settings-username-status');
        this.$username_message = this.$settings.find('.ac-game-user-settings-username-message');
        this.$username_btn = this.$settings.find('.ac-game-user-settings-username-btn');
        
        this.$password_section = this.$settings.find('.ac-game-user-settings-password-section');
        this.$old_password = this.$settings.find('.ac-game-user-settings-old-password');
        this.$new_password = this.$settings.find('.ac-game-user-settings-new-password');
        this.$confirm_password = this.$settings.find('.ac-game-user-settings-confirm-password');
        this.$password_message = this.$settings.find('.ac-game-user-settings-password-message');
        this.$password_btn = this.$settings.find('.ac-game-user-settings-password-btn');
        
        this.$auth_badge = this.$settings.find('.ac-game-user-settings-auth-badge');
        this.$score_input = this.$settings.find('.ac-game-user-settings-score');

        this.start();
    }

    start() {
        this.add_listening_events();
    }

    add_listening_events() {
        let outer = this;

        // 关闭按钮
        this.$close_btn.click(function() {
            outer.hide();
            outer.root.menu.show();
        });

        // ESC键关闭
        $(window).keydown(function(e) {
            if (e.which === 27 && outer.$settings.is(':visible')) {
                outer.hide();
                outer.root.menu.show();
            }
        });

        // 头像上传
        this.$avatar_input.change(function() {
            outer.upload_avatar(this.files[0]);
        });

        // 用户名输入检查
        this.$username_input.on('input', function() {
            outer.check_username();
        });

        // 更新用户名按钮
        this.$username_btn.click(function() {
            outer.update_username();
        });

        // 更新密码按钮
        this.$password_btn.click(function() {
            outer.update_password();
        });
    }

    show() {
        this.$settings.show();
        this.load_user_settings();
    }

    hide() {
        this.$settings.hide();
        this.clear_messages();
    }

    clear_messages() {
        this.$avatar_message.empty();
        this.$username_message.empty();
        this.$password_message.empty();
        this.$username_status.empty();
        this.$old_password.val('');
        this.$new_password.val('');
        this.$confirm_password.val('');
    }

    load_user_settings() {
        let outer = this;
        
        $.ajax({
            url: "https://app7549.acapp.acwing.com.cn/settings/get_user_settings/",
            type: "GET",
            success: function(resp) {
                if (resp.result === "success") {
                    // 设置头像
                    outer.$avatar_img.attr('src', resp.photo);
                    
                    // 设置用户名
                    outer.$username_input.val(resp.username);
                    
                    // 设置积分
                    outer.$score_input.val(resp.score);
                    
                    // 设置认证类型标签
                    let badge_text = '';
                    let badge_class = '';
                    
                    if (resp.auth_type === 'github') {
                        badge_text = 'GitHub';
                        badge_class = 'github';
                    } else if (resp.auth_type === 'gitee') {
                        badge_text = 'Gitee';
                        badge_class = 'gitee';
                    } else if (resp.auth_type === 'acwing') {
                        badge_text = 'AcWing';
                        badge_class = 'acwing';
                    } else {
                        badge_text = '本地账号';
                        badge_class = 'local';
                    }
                    
                    outer.$auth_badge.text(badge_text).attr('class', 'ac-game-user-settings-auth-badge ' + badge_class);
                    
                    // 显示/隐藏密码修改区域
                    if (resp.can_change_password) {
                        outer.$password_section.show();
                    } else {
                        outer.$password_section.hide();
                    }
                }
            },
            error: function() {
                outer.$username_message.html('<div class="ac-game-user-settings-error">加载用户信息失败</div>');
            }
        });
    }

    check_username() {
        let outer = this;
        let username = this.$username_input.val().trim();
        
        // 清除之前的定时器
        if (this.username_check_timer) {
            clearTimeout(this.username_check_timer);
        }
        
        // 清空状态
        this.$username_status.empty();
        this.$username_message.empty();
        
        if (!username) {
            return;
        }
        
        // 显示检查中状态
        this.$username_status.html('⏳').attr('class', 'ac-game-user-settings-username-status checking');
        
        // 延迟检查（避免频繁请求）
        this.username_check_timer = setTimeout(function() {
            $.ajax({
                url: "https://app7549.acapp.acwing.com.cn/settings/check_username/",
                type: "GET",
                data: { username: username },
                success: function(resp) {
                    if (resp.available) {
                        outer.$username_status.html('✓').attr('class', 'ac-game-user-settings-username-status available');
                        if (resp.message !== '当前用户名') {
                            outer.$username_message.html('<div class="ac-game-user-settings-success">' + resp.message + '</div>');
                        }
                    } else {
                        outer.$username_status.html('✗').attr('class', 'ac-game-user-settings-username-status unavailable');
                        outer.$username_message.html('<div class="ac-game-user-settings-error">' + resp.message + '</div>');
                    }
                }
            });
        }, 500);
    }

    update_username() {
        let outer = this;
        let username = this.$username_input.val().trim();
        
        if (!username) {
            this.$username_message.html('<div class="ac-game-user-settings-error">请输入用户名</div>');
            return;
        }
        
        this.$username_btn.prop('disabled', true);
        
        $.ajax({
            url: "https://app7549.acapp.acwing.com.cn/settings/update_username/",
            type: "POST",
            headers: {
                'X-CSRFToken': this.get_csrf_token()
            },
            data: JSON.stringify({ username: username }),
            contentType: 'application/json',
            success: function(resp) {
                if (resp.result === "success") {
                    outer.$username_message.html('<div class="ac-game-user-settings-success">' + resp.message + '</div>');
                    // 更新本地存储的用户名
                    outer.root.settings.username = resp.username;
                } else {
                    outer.$username_message.html('<div class="ac-game-user-settings-error">' + resp.message + '</div>');
                }
            },
            error: function() {
                outer.$username_message.html('<div class="ac-game-user-settings-error">更新失败，请重试</div>');
            },
            complete: function() {
                outer.$username_btn.prop('disabled', false);
            }
        });
    }

    update_password() {
        let outer = this;
        let old_password = this.$old_password.val();
        let new_password = this.$new_password.val();
        let confirm_password = this.$confirm_password.val();
        
        // 清空之前的错误信息
        this.$password_message.empty();
        
        // 验证
        if (!old_password || !new_password || !confirm_password) {
            this.$password_message.html('<div class="ac-game-user-settings-error">请填写所有密码字段</div>');
            return;
        }
        
        if (new_password !== confirm_password) {
            this.$password_message.html('<div class="ac-game-user-settings-error">两次输入的新密码不一致</div>');
            return;
        }
        
        if (new_password.length < 6) {
            this.$password_message.html('<div class="ac-game-user-settings-error">密码长度至少为6个字符</div>');
            return;
        }
        
        this.$password_btn.prop('disabled', true);
        
        $.ajax({
            url: "https://app7549.acapp.acwing.com.cn/settings/update_password/",
            type: "POST",
            headers: {
                'X-CSRFToken': this.get_csrf_token()
            },
            data: JSON.stringify({
                old_password: old_password,
                new_password: new_password,
                confirm_password: confirm_password
            }),
            contentType: 'application/json',
            success: function(resp) {
                if (resp.result === "success") {
                    outer.$password_message.html('<div class="ac-game-user-settings-success">' + resp.message + '</div>');
                    // 清空密码输入框
                    outer.$old_password.val('');
                    outer.$new_password.val('');
                    outer.$confirm_password.val('');
                } else {
                    outer.$password_message.html('<div class="ac-game-user-settings-error">' + resp.message + '</div>');
                }
            },
            error: function() {
                outer.$password_message.html('<div class="ac-game-user-settings-error">更新失败，请重试</div>');
            },
            complete: function() {
                outer.$password_btn.prop('disabled', false);
            }
        });
    }

    upload_avatar(file) {
        let outer = this;
        
        if (!file) {
            return;
        }
        
        // 验证文件大小
        if (file.size > 2 * 1024 * 1024) {
            this.$avatar_message.html('<div class="ac-game-user-settings-error">图片大小不能超过2MB</div>');
            return;
        }
        
        // 验证文件类型
        let allowed_types = ['image/jpeg', 'image/png', 'image/gif'];
        if (!allowed_types.includes(file.type)) {
            this.$avatar_message.html('<div class="ac-game-user-settings-error">只支持 JPG、PNG、GIF 格式</div>');
            return;
        }
        
        let formData = new FormData();
        formData.append('avatar', file);
        
        this.$avatar_message.html('<div class="ac-game-user-settings-hint">上传中...</div>');
        
        $.ajax({
            url: "https://app7549.acapp.acwing.com.cn/settings/upload_avatar/",
            type: "POST",
            headers: {
                'X-CSRFToken': this.get_csrf_token()
            },
            data: formData,
            processData: false,
            contentType: false,
            success: function(resp) {
                if (resp.result === "success") {
                    outer.$avatar_message.html('<div class="ac-game-user-settings-success">' + resp.message + '</div>');
                    // 更新头像显示
                    outer.$avatar_img.attr('src', resp.photo);
                    // 更新本地存储的头像
                    outer.root.settings.photo = resp.photo;
                } else {
                    outer.$avatar_message.html('<div class="ac-game-user-settings-error">' + resp.message + '</div>');
                }
            },
            error: function() {
                outer.$avatar_message.html('<div class="ac-game-user-settings-error">上传失败，请重试</div>');
            }
        });
    }

    get_csrf_token() {
        // 从cookie中获取CSRF token
        let cookieValue = null;
        let name = 'csrftoken';
        if (document.cookie && document.cookie !== '') {
            let cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                let cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
}
```

## 第六步：集成到游戏中

### 6.1 更新主游戏类，添加用户设置

```javascript
export class AcGame{
    constructor(id, AcWingOS){
        this.id = id;
        this.$ac_game = $('#' + id);
        this.AcWingOS = AcWingOS;

        this.settings = new Settings(this);
        this.menu = new AcGameMenu(this);
        this.playground = new AcGamePlayground(this);
        this.chatroom = new AcGameChatRoom(this);
        this.leaderboard = new AcGameLeaderboard(this);
        this.user_settings = new AcGameUserSettings(this);

        this.start();
    }

    start(){
    }
}
```

### 6.2 更新菜单类，添加设置按钮功能

```javascript
add_listening_events() {
        let outer = this;
        this.$single_mode.click(function () {
            outer.hide();
            outer.root.playground.show("single mode");
        });
        this.$multi_mode.click(function () {
            outer.hide();
            outer.root.playground.show("multi mode");
        });
        this.$leaderboard.click(function () {
            outer.hide();
            outer.root.leaderboard.show();
        });
        this.$chatroom.click(function () {
            outer.hide();
            outer.root.chatroom.show();
        })
        this.$settings.click(function () {
            outer.hide();
            outer.root.user_settings.show();
        });
        this.$exit.click(function () {
            outer.root.settings.logout_on_remote();
        });
```

### 6.3 更新HTML模板，引入新的CSS文件

```html
<link rel="stylesheet" href="{% static 'css/chat-field.css' %}">
    <link rel="stylesheet" href="{% static 'css/chatroom.css' %}">
    <link rel="stylesheet" href="{% static 'css/leaderboard.css' %}">
    <link rel="stylesheet" href="{% static 'css/user-settings.css' %}">
    <link rel="stylesheet" href="{% static 'css/media.css' %}">
    <link rel="stylesheet" href="{% static 'css/menu.css' %}">
    <link rel="stylesheet" href="{% static 'css/playground.css' %}">
    <link rel="stylesheet" href="{% static 'css/settings.css' %}">
```

## 第七步：执行和测试

现在所有代码都已经写好了，让我们执行以下步骤：

### 7.1 创建目录和设置权限

bash

```bash
# 创建媒体目录
mkdir -p /home/acs/media/avatars

# 设置权限
chmod 755 /home/acs/media
chmod 755 /home/acs/media/avatars
```

### 7.2 安装 Pillow

bash

```bash
pip install Pillow
```

### 7.3 压缩 JavaScript 文件

bash

```bash
./scripts/compress_game_js.sh
```

### 7.4 重启服务

bash

```bash
# 重启 uwsgi
uwsgi --ini scripts/uwsgi.ini

# 重启 nginx（如果需要）
sudo /etc/init.d/nginx restart
```

### 7.5 配置 Nginx（如果还没配置）

在你的 Nginx 配置文件中添加：

nginx

```nginx
location /media {
    alias /home/acs/media;
}
```

## 功能说明

现在你的设置功能包含：

1. 头像上传
   - 支持 JPG、PNG、GIF 格式
   - 最大 2MB
   - 自动裁剪为正方形
   - 存储在服务器 `/home/acs/media/avatars/` 目录
2. 用户名修改
   - 实时检查用户名是否可用
   - 3-20 个字符限制
   - 防止重复
3. 密码修改
   - 仅本地注册用户可用
   - 需要输入旧密码验证
   - 新密码需要二次确认
   - 至少 6 个字符
4. 账号信息显示
   - 显示认证类型（本地/GitHub/Gitee/AcWing）
   - 显示用户积分

## 注意事项

1. 确保服务器有写入 `/home/acs/media/` 的权限
2. 第三方登录用户不能修改密码
3. 上传的头像会自动压缩和裁剪
4. 修改用户名后，其他地方显示的用户名会在页面刷新后更新

# 拓展功能3：User Avatar Menu Block

## 步骤 1: 创建 CSS 样式

首先，我们需要为用户信息小方块创建样式。在 `game/static/css/menu.css` 文件中添加以下样式：

```css
/* 用户信息块样式 - 添加到 menu.css 文件末尾 */

/* 用户信息块 */
.ac-game-menu-user-info {
    position: fixed;
    top: 2vh;
    left: 2vw;
    z-index: 100;
    display: flex;
    align-items: center;
    gap: 0.8vw;
    padding: 0.8vh 1.2vw;
    background: linear-gradient(135deg, rgba(25, 25, 35, 0.7), rgba(35, 35, 45, 0.6));
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    cursor: pointer;
    backdrop-filter: blur(12px);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.4),
                inset 0 1px 0 rgba(255, 255, 255, 0.06);
    transition: all 0.3s ease;
    user-select: none;
    will-change: transform, box-shadow;
    backface-visibility: hidden;
}

/* 用户头像 */
.ac-game-menu-user-avatar {
    width: 3.5vh;
    height: 3.5vh;
    min-width: 28px;
    min-height: 28px;
    max-width: 40px;
    max-height: 40px;
    border-radius: 50%;
    object-fit: cover;
    border: 2px solid rgba(255, 255, 255, 0.2);
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3);
}

/* 用户名 */
.ac-game-menu-user-name {
    color: #e4e4e7;
    font-size: clamp(12px, 1.8vh, 16px);
    font-weight: 400;
    font-family: 'Inter', 'Roboto', sans-serif;
    letter-spacing: 0.03em;
    max-width: 150px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

/* 悬停效果 */
.ac-game-menu-user-info:hover {
    transform: translateY(-2px);
    background: linear-gradient(135deg, rgba(30, 30, 40, 0.8), rgba(40, 40, 50, 0.7));
    border-color: rgba(255, 255, 255, 0.2);
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.5),
                0 0 20px rgba(52, 152, 219, 0.1),
                inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

.ac-game-menu-user-info:hover .ac-game-menu-user-avatar {
    border-color: rgba(52, 152, 219, 0.5);
}

.ac-game-menu-user-info:hover .ac-game-menu-user-name {
    color: #ffffff;
    text-shadow: 0 1px 3px rgba(0, 0, 0, 0.5);
}

/* 点击效果 */
.ac-game-menu-user-info:active {
    transform: translateY(0);
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.5),
                inset 0 2px 4px rgba(0, 0, 0, 0.3);
}

/* 闪光效果 */
.ac-game-menu-user-info::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg,
        transparent,
        rgba(255, 255, 255, 0.03),
        rgba(255, 255, 255, 0.06),
        rgba(255, 255, 255, 0.03),
        transparent);
    transition: left 0.5s ease;
    will-change: transform;
    border-radius: 12px;
}

.ac-game-menu-user-info:hover::before {
    left: 100%;
}
```



## 步骤 2: 修改菜单 JavaScript 文件

现在让我们修改 `game/static/js/src/menu/zbase.js` 文件，添加用户信息块的 HTML 结构和事件监听：

```javascript
class AcGameMenu {
    constructor(root) {
        this.root = root;
        this.$menu = $(`
<div class="ac-game-menu">
    <!-- 用户信息块 - 新增 -->
    <div class="ac-game-menu-user-info">
        <img class="ac-game-menu-user-avatar" src="" alt="用户头像">
        <span class="ac-game-menu-user-name"></span>
    </div>

    <!-- 操作指南 -->
    <div class="ac-game-menu-guide">
        <div class="ac-game-menu-guide-toggle">
            <span class="ac-game-menu-guide-text">操作指南</span>
            <span class="ac-game-menu-guide-arrow">▼</span>
        </div>
        <div class="ac-game-menu-guide-content">
            <h3>游戏操作说明</h3>
            <div class="ac-game-menu-guide-item">
                <strong>移动：</strong>鼠标<span class="ac-game-menu-guide-key">右键</span>控制角色移动
            </div>
            <div class="ac-game-menu-guide-item">
                <strong>火球：</strong>按下<span class="ac-game-menu-guide-key">Q</span>键选择技能，<span class="ac-game-menu-guide-key">左键</span>发射
            </div>
            <div class="ac-game-menu-guide-item">
                <strong>闪现：</strong>按下<span class="ac-game-menu-guide-key">F</span>键选择技能，<span class="ac-game-menu-guide-key">左键</span>释放
            </div>
            <div class="ac-game-menu-guide-item">
                <strong>多人模式聊天窗：</strong>按下<span class="ac-game-menu-guide-key">ENTER</span>键打开聊天窗，<span class="ac-game-menu-guide-key">ESC</span>键关闭
            </div>
            <div class="ac-game-menu-guide-item">
                <strong>游戏结束后：</strong>点击<span class="ac-game-menu-guide-key">任意位置</span>回到<span class="ac-game-menu-guide-key">菜单</span>
            </div>
        </div>
    </div>

    <!-- 菜单选项 -->
    <div class="ac-game-menu-field">
        <div class="ac-game-menu-field-item ac-game-menu-field-item-single-mode">
            单人模式
        </div>
        <br>
        <div class="ac-game-menu-field-item ac-game-menu-field-item-multi-mode">
            多人模式
        </div>
        <br>
        <div class="ac-game-menu-field-item ac-game-menu-field-item-leaderboard">
            排行榜
        </div>
        <br>
        <div class="ac-game-menu-field-item ac-game-menu-field-item-chatroom">
            聊天室
        </div>
        <br>
        <div class="ac-game-menu-field-item ac-game-menu-field-item-settings">
            设置
        </div>
        <br>
        <div class="ac-game-menu-field-item ac-game-menu-field-item-exit">
            退出登录
        </div>
    </div>
</div>
`);
        this.$menu.hide()
        this.root.$ac_game.append(this.$menu);
        
        // 用户信息块元素 - 新增
        this.$user_info = this.$menu.find('.ac-game-menu-user-info');
        this.$user_avatar = this.$menu.find('.ac-game-menu-user-avatar');
        this.$user_name = this.$menu.find('.ac-game-menu-user-name');
        
        // 菜单项元素
        this.$single_mode = this.$menu.find('.ac-game-menu-field-item-single-mode');
        this.$multi_mode = this.$menu.find('.ac-game-menu-field-item-multi-mode');
        this.$leaderboard = this.$menu.find(`.ac-game-menu-field-item-leaderboard`);
        this.$chatroom = this.$menu.find('.ac-game-menu-field-item-chatroom');
        this.$settings = this.$menu.find('.ac-game-menu-field-item-settings');
        this.$exit = this.$menu.find('.ac-game-menu-field-item-exit');

        // 操作指南元素
        this.$guide_toggle = this.$menu.find('.ac-game-menu-guide-toggle');
        this.$guide_content = this.$menu.find('.ac-game-menu-guide-content');
        this.$guide_arrow = this.$menu.find('.ac-game-menu-guide-arrow');

        this.start();
    }

    start() {
        this.add_listening_events();
        this.update_user_info(); // 新增：更新用户信息
    }

    // 新增：更新用户信息方法
    update_user_info() {
        // 从 settings 获取用户信息
        if (this.root.settings && this.root.settings.username && this.root.settings.photo) {
            this.$user_avatar.attr('src', this.root.settings.photo);
            this.$user_name.text(this.root.settings.username);
        }
    }

    add_listening_events() {
        let outer = this;
        
        // 用户信息块点击事件 - 新增
        this.$user_info.click(function() {
            outer.hide();
            outer.root.user_settings.show();
        });
        
        // 其他菜单项事件
        this.$single_mode.click(function () {
            outer.hide();
            outer.root.playground.show("single mode");
        });
        
        this.$multi_mode.click(function () {
            outer.hide();
            outer.root.playground.show("multi mode");
        });
        
        this.$leaderboard.click(function () {
            outer.hide();
            outer.root.leaderboard.show();
        });
        
        this.$chatroom.click(function () {
            outer.hide();
            outer.root.chatroom.show();
        });
        
        this.$settings.click(function () {
            outer.hide();
            outer.root.user_settings.show();
        });
        
        this.$exit.click(function () {
            outer.root.settings.logout_on_remote();
        });
        
        // 操作指南事件
        this.$guide_toggle.click(function () {
            outer.$guide_content.toggleClass('active');
            outer.$guide_arrow.toggleClass('active');
        });

        $(document).click(function (e) {
            if (!$(e.target).closest('.ac-game-menu-guide').length) {
                if (outer.$guide_content.hasClass('active')) {
                    outer.$guide_content.removeClass('active');
                    outer.$guide_arrow.removeClass('active');
                }
            }
        });
    }

    show() {
        // 显示menu界面
        this.$menu.show();
        // 每次显示时更新用户信息
        this.update_user_info();
    }

    hide() {
        // 关闭menu界面
        this.$menu.hide();
    }
}
```

## 步骤 3: 添加响应式媒体查询

让我们在 `game/static/css/media.css` 中添加用户信息块的响应式样式：

```css
/* 用户信息块响应式样式 - 添加到 media.css 文件中相应位置 */

/* 平板横屏和小屏幕笔记本 */
@media screen and (max-width: 1024px) {
    .ac-game-menu-user-info {
        top: 2.5vh;
        left: 2.5vw;
        padding: 0.7vh 1vw;
    }
    
    .ac-game-menu-user-avatar {
        width: 3.2vh;
        height: 3.2vh;
        min-width: 26px;
        min-height: 26px;
    }
}

/* 平板竖屏 */
@media screen and (max-width: 768px) {
    .ac-game-menu-user-info {
        top: 2vh;
        left: 2vw;
        gap: 0.6vw;
        padding: 0.6vh 0.8vw;
    }
    
    .ac-game-menu-user-avatar {
        width: 3vh;
        height: 3vh;
        min-width: 24px;
        min-height: 24px;
    }
    
    .ac-game-menu-user-name {
        font-size: clamp(11px, 1.6vh, 14px);
        max-width: 120px;
    }
}

/* 手机横屏 */
@media screen and (max-width: 667px) and (orientation: landscape) {
    .ac-game-menu-user-info {
        top: 1.5vh;
        left: 1.5vw;
        padding: 0.5vh 0.8vw;
    }
    
    .ac-game-menu-user-avatar {
        width: 2.8vh;
        height: 2.8vh;
        min-width: 22px;
        min-height: 22px;
    }
}

/* 手机竖屏 */
@media screen and (max-width: 480px) {
    .ac-game-menu-user-info {
        top: 1.5vh;
        left: 2vw;
        gap: 0.5vw;
        padding: 0.5vh 0.8vw;
    }
    
    .ac-game-menu-user-avatar {
        width: 2.5vh;
        height: 2.5vh;
        min-width: 20px;
        min-height: 20px;
        max-width: 30px;
        max-height: 30px;
    }
    
    .ac-game-menu-user-name {
        font-size: clamp(10px, 1.5vh, 13px);
        max-width: 100px;
    }
}

/* 小屏手机 */
@media screen and (max-width: 360px) {
    .ac-game-menu-user-info {
        left: 1vw;
        padding: 0.4vh 0.6vw;
    }
    
    .ac-game-menu-user-name {
        max-width: 80px;
    }
}
```

## 步骤 4: 实施步骤

现在让我为你总结一下实施步骤：

### 1. **更新 CSS 文件**

- 将上面"用户信息块 CSS 样式"的内容添加到 `game/static/css/menu.css` 文件的末尾
- 将"用户信息块响应式 CSS"的内容添加到 `game/static/css/media.css` 文件中

### 2. **更新 JavaScript 文件**

- 用上面"更新后的菜单 JavaScript"的内容替换 `game/static/js/src/menu/zbase.js` 文件的全部内容

### 3. **重新编译 JavaScript**

运行压缩脚本：

bash

```bash
./scripts/compress_game_js.sh
```

### 4. **收集静态文件**

bash

```bash
python3 manage.py collectstatic --noinput
```

### 5. **重启服务**

bash

```bash
# 重启 uwsgi
uwsgi --ini scripts/uwsgi.ini

# 重启 nginx（如果需要）
sudo /etc/init.d/nginx restart
```

## 功能特点

这个用户信息块具有以下特点：

1. **位置**：固定在菜单界面的左上角
2. **内容**：显示用户头像和用户名
3. **交互**：
   - 鼠标悬停时有视觉反馈（上移、发光效果）
   - 点击后打开设置界面（与点击"设置"按钮效果相同）
4. **样式**：
   - 半透明背景，与菜单整体风格保持一致
   - 圆形头像，带边框
   - 用户名自动截断（过长时显示省略号）
5. **响应式**：在不同屏幕尺寸下自动调整大小
6. **动态更新**：每次显示菜单时自动更新用户信息
