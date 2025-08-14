class ChatRoomSocket {
    constructor(chatroom) {
        this.chatroom = chatroom;
        this.ws = new WebSocket("wss://app7562.acapp.acwing.com.cn/wss/chatroom/");

        this.username = this.chatroom.root.settings.username;
        this.photo = this.chatroom.root.settings.photo;
        this.online_users = {};

        this.start();
    }

    start() {
        this.add_listening_events();
    }

    add_listening_events() {
        let outer = this;

        this.ws.onopen = function () {
            outer.send_join();
        };

        this.ws.onmessage = function (e) {
            let data = JSON.parse(e.data);
            outer.receive(data);
        }

        this.ws.onclose = function () {
        };

        this.ws.onerror = function (e) {
            console.error("聊天室连接错误:", e);
        }
    }

    receive(data) {
        let event = data.event;

        switch (event) {
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
            'photo': this.photo,
        }));
    }

    // 发送聊天消息
    send_message(message) {
        this.ws.send(JSON.stringify({
            'event': 'message',
            'username': this.username,
            'message': message,
        }));
    }

    // 发送离开消息
    send_leave() {
        if (this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                'event': 'leave',
                'username': this.username,
            }));
        }
    }

    // 接受用户加入
    receive_join(data) {
        this.chatroom.add_message('系统', `${data.username} 加入了聊天室`, true);
    }

    // 接受用户离开
    receive_leave(data) {
        this.chatroom.add_message('系统', `${data.username} 离开了聊天室`, true);
    }

    // 接受聊天信息
    receive_message(data) {
        this.chatroom.add_message(data.username, data.message);
    }

    // 接受在线用户列表
    receive_users_list(data) {
        // 更新本地在线用户列表
        this.online_users = {};
        if (data.users && Array.isArray(data.users)) {
            data.users.forEach(user => {
                this.online_users[user.username] = user;
            });
        }
        this.chatroom.update_users_list(data.users);
    }

    // 关闭连携
    close() {
        this.send_leave();
        this.ws.close();
    }

}
