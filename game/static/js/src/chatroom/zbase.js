class AcGameChatRoom {
    constructor(root) {
        this.root = root;
        this.$chatroom = $(`
            <div class="ac-game-chatroom">
                <div class="ac-game-chatroom-container">
                    <div class="ac-game-chatroom-header">
                        <h2>BallBlitz聊天室</h2>
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
                        <div class="ac-game-chatroom-admin-button">
                            <div class="ac-game-chatroom-admin-icon">✉</div>
                            <span class="ac-game-chatroom-admin-text">私信管理员</span>
                            <span class="ac-game-chatroom-admin-badge" style="display: none;">0</span>
                        </div>
                        <h3>在线用户</h3>
                        <div class="ac-game-chatroom-users-list">
                            <!-- 在线用户列表 -->
                        </div>
                    </div>
                </div>
            </div>
        `);

        this.$admin_message = $(`
            <div class="ac-game-admin-message">
                <div class="ac-game-admin-message-header">
                    <h3 class="ac-game-admin-message-title">私信管理员</h3>
                    <button class="ac-game-admin-message-close">×</button>
                </div>
                <div class="ac-game-admin-message-content">
                    <div class="ac-game-admin-message-loading">加载中...</div>
                </div>
                <div class="ac-game-admin-message-input-area">
                    <input type="text" class="ac-game-admin-message-input" placeholder="输入消息...">
                    <button class="ac-game-admin-message-send">发送</button>
                </div>
            </div>
        `);

        this.$chatroom.hide();
        this.$admin_message.hide();

        this.root.$ac_game.append(this.$chatroom);
        this.root.$ac_game.append(this.$admin_message);

        this.$messages = this.$chatroom.find('.ac-game-chatroom-messages');
        this.$input = this.$chatroom.find('.ac-game-chatroom-input');
        this.$send_btn = this.$chatroom.find('.ac-game-chatroom-send');
        this.$close_btn = this.$chatroom.find('.ac-game-chatroom-close');
        this.$users_list = this.$chatroom.find('.ac-game-chatroom-users-list');

        this.$admin_button = this.$chatroom.find('.ac-game-chatroom-admin-button');
        this.$admin_badge = this.$chatroom.find('.ac-game-chatroom-admin-badge');
        this.$admin_message_content = this.$admin_message.find('.ac-game-admin-message-content');
        this.$admin_message_input = this.$admin_message.find('.ac-game-admin-message-input');
        this.$admin_message_send = this.$admin_message.find('.ac-game-admin-message-send');
        this.$admin_message_close = this.$admin_message.find('.ac-game-admin-message-close');

        this.socket = null;
        this.admin_messages = [];
        this.start();
    }

    // 格式化时间为本地时间
    formatLocalTime(timestamp) {
        // 如果时间戳格式是 "YYYY-MM-DD HH:MM:SS"
        // 可以直接显示，因为后端已经转换了
        return timestamp;

        // 或者如果需要进一步格式化
        // const date = new Date(timestamp);
        // return date.toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' });
    }

    start() {
        this.add_listening_events();

        // 每30秒检查一次未读消息
        setInterval(() => {
            if (this.$chatroom.is(':visible')) {
                this.check_unread_messages();
            }
        }, 30000);
    }

    add_listening_events() {
        let outer = this;

        // 关闭按钮
        this.$close_btn.click(function () {
            outer.hide();
            outer.root.menu.show();
        });

        // 发送按钮
        this.$send_btn.click(function () {
            outer.send_message();
        });

        // 回车键发送
        this.$input.keydown(function (e) {
            if (e.which === 13) {
                outer.send_message();
                return false;
            }
        });

        // 私信管理员按钮点击事件
        this.$admin_button.click(function () {
            outer.show_admin_message();
        });

        // 私信窗口关闭按钮
        this.$admin_message_close.click(function () {
            outer.hide_admin_message();
        });

        // 私信发送按钮
        this.$admin_message_send.click(function () {
            outer.send_admin_message();
        });

        // 私信输入框回车发送
        this.$admin_message_input.keydown(function (e) {
            if (e.which === 13) {
                outer.send_admin_message();
                return false;
            }
        });

        // ESC退出
        $(window).keydown(function (e) {
            if (e.which === 27) {
                if (outer.$admin_message.is(':visible')) {
                    outer.hide_admin_message();
                } else if (outer.$chatroom.is(':visible')) {
                    outer.hide();
                    outer.root.menu.show();
                }
            }
        });
    }

    // 显示私信管理员窗口
    show_admin_message() {
        this.$admin_message.css('display', 'flex');
        this.load_admin_messages();
        this.$admin_message_input.focus();

        // 用户查看了消息，立即隐藏未读徽章
        this.$admin_badge.hide();
    }

    // 隐藏私信管理员窗口
    hide_admin_message() {
        this.$admin_message.hide();
    }

    // 加载历史私信
    load_admin_messages() {
        let outer = this;

        // 显示加载中状态
        this.$admin_message_content.html('<div class="ac-game-admin-message-loading">加载中...</div>');

        $.ajax({
            url: AC_ORIGIN + "/settings/get_admin_messages/",
            type: "GET",
            success: function (resp) {
                if (resp.result === "success") {
                    outer.render_admin_messages(resp.messages);
                } else {
                    outer.$admin_message_content.html('<div class="ac-game-admin-message-empty">加载失败</div>');
                }
            },
            error: function () {
                outer.$admin_message_content.html('<div class="ac-game-admin-message-empty">网络错误</div>');
            }
        });
    }

    // 渲染私信消息
    render_admin_messages(messages) {
        this.$admin_message_content.empty();

        if (messages.length === 0) {
            this.$admin_message_content.html(`
                <div class="ac-game-admin-message-empty">
                    <div class="ac-game-admin-message-empty-icon">💬</div>
                    <div class="ac-game-admin-message-empty-text">暂无消息</div>
                </div>
            `);
            return;
        }

        for (let msg of messages) {
            // 渲染用户发送的消息
            let $userMsg = $(`
                <div class="ac-game-admin-message-item ac-game-admin-message-sent">
                    <div class="ac-game-admin-message-bubble">${this.escapeHtml(msg.message)}</div>
                    <div class="ac-game-admin-message-time">${this.formatLocalTime(msg.timestamp)}</div>
                </div>
            `);
            this.$admin_message_content.append($userMsg);

            // 如果有回复，渲染管理员的回复
            if (msg.reply) {
                let $adminReply = $(`
                    <div class="ac-game-admin-message-item ac-game-admin-message-received">
                        <div class="ac-game-admin-message-bubble">${this.escapeHtml(msg.reply)}</div>
                        <div class="ac-game-admin-message-time">${msg.reply_timestamp}</div>
                    </div>
                `);
                this.$admin_message_content.append($adminReply);
            }
        }

        // 滚动到底部
        this.$admin_message_content.scrollTop(this.$admin_message_content[0].scrollHeight);
    }

    // 发送私信给管理员
    send_admin_message() {
        let outer = this;
        let message = this.$admin_message_input.val().trim();

        if (!message) {
            return;
        }

        // 禁用发送按钮
        this.$admin_message_send.prop('disabled', true);

        $.ajax({
            url: AC_ORIGIN + "/settings/send_admin_message/",
            type: "POST",
            headers: {
                'X-CSRFToken': this.get_csrf_token()
            },
            data: JSON.stringify({
                message: message
            }),
            contentType: 'application/json',
            success: function (resp) {
                if (resp.result === "success") {
                    // 清空输入框
                    outer.$admin_message_input.val('');

                    // 添加消息到界面
                    let $newMsg = $(`
                        <div class="ac-game-admin-message-item ac-game-admin-message-sent">
                            <div class="ac-game-admin-message-bubble">${outer.escapeHtml(message)}</div>
                            <div class="ac-game-admin-message-time">${resp.timestamp}</div>
                        </div>
                    `);

                    // 如果是空消息状态，先清空
                    if (outer.$admin_message_content.find('.ac-game-admin-message-empty').length > 0) {
                        outer.$admin_message_content.empty();
                    }

                    outer.$admin_message_content.append($newMsg);
                    outer.$admin_message_content.scrollTop(outer.$admin_message_content[0].scrollHeight);
                } else {
                    alert(resp.message || '发送失败');
                }
            },
            error: function () {
                alert('网络错误，请重试');
            },
            complete: function () {
                outer.$admin_message_send.prop('disabled', false);
            }
        });
    }

    // 获取CSRF Token
    get_csrf_token() {
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

    // 检查未读消息数量
    check_unread_messages() {
        let outer = this;

        $.ajax({
            url: AC_ORIGIN + "/settings/get_unread_count/",
            type: "GET",
            success: function (resp) {
                if (resp.result === "success" && resp.count > 0) {
                    outer.$admin_badge.text(resp.count).show();
                } else {
                    outer.$admin_badge.hide();
                }
            }
        });
    }

    send_message() {
        let message = this.$input.val().trim();
        if (message && this.socket && this.socket.ws.readyState === WebSocket.OPEN) {
            this.socket.send_message(message);
            this.$input.val('');

            // 禁用发送按钮短暂时间，防止重复发送
            this.$send_btn.prop('disabled', true);
            setTimeout(() => {
                this.$send_btn.prop('disabled', false);
            }, 100);
        }
    }

    // 添加HTML转义方法，防止XSS攻击
    escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, m => map[m]);
    }

    add_message(username, message, is_system = false) {
        if (is_system) {
            // 系统消息 - 保持不变
            let $message = $(`
            <div class="ac-game-chatroom-message system-message">
                <div class="message-bubble">
                    ${message}
                </div>
            </div>
        `);
            this.$messages.append($message);
        } else {
            // 判断是否是自己发送的消息
            let is_self = (username === this.root.settings.username);
            let message_class = is_self ? 'message-self' : 'message-other';

            // 获取用户头像
            let user_photo = this.root.settings.photo;
            if (!is_self && this.socket && this.socket.online_users) {
                let user = this.socket.online_users[username];
                if (user) {
                    user_photo = user.photo;
                }
            }

            // 重要：根据 is_self 使用不同的类
            let $message = $(`
            <div class="ac-game-chatroom-message ${message_class}">
                <img class="message-avatar" src="${user_photo}" alt="${username}" title="${username}">
                <div class="message-bubble">
                    <div class="message-content">${this.escapeHtml(message)}</div>
                </div>
            </div>
        `);

            this.$messages.append($message);
        }

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

        if (!this.socket) {
            this.socket = new ChatRoomSocket(this);
        }

        // 检查未读消息数量
        this.check_unread_messages();
    }

    hide() {
        this.$chatroom.hide();
        this.hide_admin_message();


        if (this.socket) {
            this.socket.close();
            this.socket = null;
        }
    }
}