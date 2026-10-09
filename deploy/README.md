# 一键部署

把"手工上传、迁移、重启、验证"变成一条命令。服务器上的脚本自己做预演、备份、应用、验证，**任何一步失败都会自动回滚**。

```
python deploy/deploy.py              # 部署当前提交 (HEAD)
python deploy/deploy.py --dry-run    # 只做预演，不改线上
python deploy/deploy.py status       # 进程、最近几次部署、健康检查
python deploy/deploy.py rollback     # 把上一次部署前的文件放回去
```

## 它每次部署都做什么

1. **打包**：`git archive` 当前提交的 `acapp game match_system static manage.py`（只部署已提交的文件）。
2. **校验发布包**（服务器端）：只接受这几个目录下的普通文件；拒绝 `..`、绝对路径、符号链接、可疑文件名。
3. **比对**：只处理内容真正变化的文件；没有变化就什么都不做。
4. **预演**（在服务器容器的临时目录里，用线上数据库的副本）：编译、`manage.py check`、检查"改了模型但没写迁移"、执行迁移、跑全部测试。**任何一项失败：线上完全不动**。
5. **健康基线**：部署前先检查首页、`getinfo` 和 daphne 都正常；不正常就拒绝部署。
6. **备份**：数据库一致性快照（含完整性检查）+ 将被替换的文件，放在 `/var/backups/acapp/<时间>/`，保留最近 10 次。
7. **应用**：只解压变化的文件，执行迁移。
8. **按需重载**：只改了模板/静态文件 → 不重载任何进程；改了 Python → 平滑重载 uwsgi（HUP）+ 在原来的 tmux 窗格里重启 daphne（在线 WebSocket 玩家会断开几秒）。
9. **验证**：首页、接口、静态文件、花瓣模式路由。**失败 → 自动回滚文件、重载、再验证**。

退出码：`0` 成功或无事可做；`1` 失败但已恢复旧版；`2` 失败且回滚没验证通过（需要人工）；`3` 被拒绝或预演失败（线上没动）；`255` SSH 连不上或密钥被拒。

## 一次性安装（只做一次）

需要 root 密码一次，**不会保存**：

```
SSH_PW='服务器密码' python deploy/install_server.py
```

它在服务器**宿主机**上改动的只有这三样（`--uninstall` 可以全部撤销）：

| 位置 | 内容 |
|---|---|
| `/usr/local/bin/acapp-deploy` | 服务器端脚本（root，0700） |
| `/var/backups/acapp/` | 部署备份 |
| `/root/.ssh/authorized_keys` | 追加两行**受限密钥**：`command="/usr/local/bin/acapp-deploy",no-port-forwarding,no-X11-forwarding,no-agent-forwarding,no-pty`，即这把密钥**只能**运行部署脚本，不能开 shell。原文件先备份为 `authorized_keys.bak-<时间>`，你自己的密钥不动 |

同时在本机生成 `~/.ssh/acapp_deploy`（你用）和 `~/.ssh/acapp_deploy_ci`（给 GitHub 用），并把服务器的主机密钥写进 `deploy/known_hosts`（直接从服务器的 `/etc/ssh` 读取，不是第一次连接时盲目信任）。最后它会自检：密钥能登录、`status` 能运行、通过密钥执行任意命令（如 `id`）会被拒绝。

装完之后请把 `deploy/known_hosts` 提交到仓库（里面只有公开的主机密钥）。

## 出问题时会怎样

| 情况 | 结果 |
|---|---|
| 测试失败 / 迁移出错 / 改了模型没写迁移 | 预演阶段拦下，退出码 3，线上没动 |
| 部署前网站本来就不正常 | 拒绝部署，退出码 3 |
| 页面接口出错（测试没覆盖到） | 部署后验证失败 → 自动回滚，退出码 1 |
| 代码只在 uwsgi 下才崩 | uwsgi 重载失败 → 自动回滚，退出码 1 |
| daphne 起不来 | 重启失败 → 自动回滚（在记住的原窗格里重新启动旧版），退出码 1 |
| 回滚也没验证通过 | 退出码 2，日志里写明备份位置，需要人工 |
| 两个部署同时进行 | 后来的被拒绝（锁文件，30 分钟后视为过期） |

以上每一种都有自动化场景测试（见下）。

## 备份与手动恢复

每次部署在 `/var/backups/acapp/<时间>/` 下有：`db.sqlite3`（部署前的数据库快照）、`files.tar`（被替换文件的旧版本）、`meta.json`。

- 只恢复文件：`python deploy/deploy.py rollback`。
- 数据库：回滚不会动数据库（迁移都是只增不改的）。确实要恢复数据库时，在**容器内**停服务后用快照替换 `/home/acs/acapp/db.sqlite3`，会丢失快照之后的所有新数据，请谨慎。

## GitHub 自动部署（可选）

`.github/workflows/deploy.yml`：每次推送到 `master` 先跑测试；测试通过且**你打开了开关**才会部署。

1. 运行过 `install_server.py`，并已提交 `deploy/known_hosts`。
2. 仓库 Settings → Secrets and variables → Actions：
   - 新建 **Secret** `DEPLOY_SSH_KEY`，内容是本机 `~/.ssh/acapp_deploy_ci` 的全部文本（私钥）。
   - 新建 **Variable** `AUTO_DEPLOY`，值为 `true`（不设就只跑测试，不部署）。
3. 想要"人工点一下再上线"：Settings → Environments → `production` → Required reviewers。

注意：因为仓库是公开的，**不要**把这个工作流改成对 `pull_request` 触发。当前只有 push 到 `master` 才有机会读取密钥。

## 安全说明

- 部署密钥只能触发部署脚本，但**部署本身等于在你的服务器上运行发布包里的代码**。所以谁能推送到 `master`，谁就能上线；私钥只放在你的电脑和 GitHub 加密变量里，丢了就在服务器上删掉对应那一行。
- 密码只在安装时用一次，从不写入文件。

## 在本地验证这套工具

`deploy/replica/` 是一个和线上同版本的复刻环境（Ubuntu 20.04、Python 3.8、nginx、redis、tmux 里的 uwsgi/daphne、sshd）。

```
python deploy/replica/setup_replica.py              # 构建并启动 (acapp_replica，ssh 在 127.0.0.1:2222)
python deploy/tests/replica_scenarios.py            # 25 项场景：成功、静态更新、各种失败与自动回滚、手动回滚
python -m unittest deploy.tests.test_release_validation   # 发布包校验、命令注入、锁
```

## 修复 nginx 的 `/static` 漏洞（一次性）

线上 `location /static {` 配合以斜杠结尾的 `alias`，会让 `/static../db.sqlite3` 这类地址下载到整个数据库和 `.git`。

```
SSH_PW='服务器密码' python deploy/fix_nginx.py
```

只改那一行（加斜杠）、`nginx -t` 通过才热重载、并验证；之前会先统计日志里有没有人用过这个漏洞。每次部署的验证也会在漏洞仍然存在时给出 `WARN`。

## 已知限制

- 重启 daphne 会让在线的 WebSocket 玩家断开几秒；花瓣世界在内存里，重启后怪物重置（玩家进度已存库）。
- 不删除服务器上多余的旧文件（只新增和覆盖）。
- 回滚不会撤销已应用的迁移。
- nginx / uwsgi / 系统配置不在这套工具的管理范围内。
