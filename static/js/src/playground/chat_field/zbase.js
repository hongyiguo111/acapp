class ChatField {
    constructor(playground) {
        this.playground = playground;

        this.$history = $(`<div class="ac-game-chat-field-history">历史记录</div>`);
        this.$input = $(`<input type="text" class="ac-game-chat-field-input">`);

        this.$history.hide();
        this.$input.hide();

        // 阻止聊天区域的右键菜单
        this.$history.on('contextmenu', function (e) {
            e.preventDefault();
            return false;
        });

        this.$input.on('contextmenu', function (e) {
            e.preventDefault();
            return false;
        });

        this.func_id = null;
        this.is_input_active = false;

        this.playground.$playground.append(this.$history);
        this.playground.$playground.append(this.$input);

        this.start();
    }

    start() {
        this.add_listening_events();
    }

    add_listening_events() {
        let outer = this;

        this.$input.keydown(function (e) {
            if (e.which === 27) { // esc
                outer.hide_input();
                outer.hide_history();
                return false;
            } else if (e.which === 13) { // enter
                let username = outer.playground.root.settings.username;
                let text = outer.$input.val();
                if (text) {
                    outer.$input.val("");
                    outer.add_message(username, text);
                    outer.playground.mps.send_message(username, text);
                }
                return false;
            }
        });

        this.playground.$playground.mousedown(function (e) {
            let $target = $(e.target);

            // 判断点击是否在聊天区域外
            if (!$target.is(outer.$input) && !$target.is(outer.$history) &&
                !$target.closest('.ac-game-chat-field-history').length) {

                // 如果输入框显示，关闭它
                if (outer.$input.is(':visible')) {
                    outer.hide_input();
                }
                // 如果历史记录显示，关闭它
                if (outer.$history.is(':visible')) {
                    outer.hide_history();
                }
            }
        });

        // 防止点击输入框和历史记录时触发外部点击
        this.$input.mousedown(function (e) {
            e.stopPropagation();
        });

        this.$history.mousedown(function (e) {
            e.stopPropagation();
        });
    }

    render_message(message) {
        return $(`<div>${message}</div>`);
    }

    add_message(username, text) {
        this.show_history();
        let message = `${username}: ${text}`;
        this.$history.append(this.render_message(message));
        this.$history.scrollTop(this.$history[0].scrollHeight);
    }

    show_history() {
        let outer = this;
        this.$history.fadeIn();

        // 如果输入框激活，就不启动倒计时
        if (this.func_id) {
            return;
        }

        if (!this.$input.is(":visible")) {
            this.func_id = setTimeout(function () {
                outer.$history.fadeOut();
                outer.func_id = null;
            }, 3000);
        }
    }

    show_input() {
        this.$input.show();
        this.$input.focus();
        this.show_history();
    }

    hide_input() {
        this.$input.hide();
        this.playground.game_map.$canvas.focus();
        this.show_history();
    }

    hide_history() {
        this.$history.hide();

        if (this.func_id) {
            clearTimeout(this.func_id);
            this.func_id = null;
        }

        this.playground.game_map.$canvas.focus();
    }
}