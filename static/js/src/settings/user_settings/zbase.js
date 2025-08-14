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
                                <label class="ac-game-user-settings-label">得分</label>
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
            url: "https://app7562.acapp.acwing.com.cn/settings/get_user_settings/",
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
                url: "https://app7562.acapp.acwing.com.cn/settings/check_username/",
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
            url: "https://app7562.acapp.acwing.com.cn/settings/update_username/",
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
            url: "https://app7562.acapp.acwing.com.cn/settings/update_password/",
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
            url: "https://app7562.acapp.acwing.com.cn/settings/upload_avatar/",
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