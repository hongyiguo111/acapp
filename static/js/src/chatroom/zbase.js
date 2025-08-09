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

        this.$messages = this.$chatroom.find('.ac-game-chatroom-messages');
        this.$input = this.$chatroom.find('.ac-game-chatroom-input');
        this.$send_btn = this.$chatroom.find('.ac-game-chatroom-send');
        this.$close_btn = this.$chatroom.find('.ac-game-chatroom-close');
        this.$users_list = this.$chatroom.find('.ac-game-chatroom-users-list');

        this.socket = null;
        this.start();
    }

    start() {
        this.add_listening_events();
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

        // ESC退出
        $(window).keydown(function (e) {
            if (e.which === 27 && outer.$chatroom.is(':visible')) {
                outer.hide();
                outer.root.menu.show();
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
    }

    hide() {
        this.$chatroom.hide();

        if (this.socket) {
            this.socket.close();
            this.socket = null;
        }
    }
}