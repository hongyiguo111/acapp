class AnnouncementBoard {
    constructor(menu) {
        this.menu = menu;
        this.root = menu.root;
        this.is_open = false;
        this.is_admin = false;
        this.current_edit_id = null; // 当前编辑的公告ID

        this.$board = $(`
            <div class="ac-game-menu-announcement">
                <div class="ac-game-menu-announcement-toggle">
                    <span class="ac-game-menu-announcement-text">系统公告</span>
                    <span class="ac-game-menu-announcement-arrow">▼</span>
                </div>
                <div class="ac-game-menu-announcement-content">
                    <div class="ac-game-menu-announcement-header">
                        <h3>🔔 系统公告</h3>
                        <button class="ac-game-menu-announcement-add-btn" style="display: none;" title="新增公告">➕</button>
                    </div>
                    <div class="ac-game-menu-announcement-loading">
                        <div class="spinner"></div>
                        <div>加载中...</div>
                    </div>
                    <div class="ac-game-menu-announcement-list"></div>
                    <div class="ac-game-menu-announcement-empty" style="display: none;">
                        <div class="announcement-empty-icon">📭</div>
                        <div>暂无公告</div>
                    </div>
                </div>
            </div>
        `);

        this.$edit_modal = $(`
            <div class="ac-game-menu-announcement-edit-modal">
                <div class="edit-modal-content">
                    <div class="edit-modal-header">
                        <h3 class="edit-modal-title">📝 编辑系统公告</h3>
                        <button class="edit-modal-close">×</button>
                    </div>
                    <form class="edit-form">
                        <div class="edit-form-group">
                            <label class="edit-form-label">公告标题</label>
                            <input type="text" class="edit-form-input edit-title" 
                                   placeholder="输入公告标题..." maxlength="100" required>
                            <div class="char-counter">
                                <span class="title-count">0</span>/100
                            </div>
                        </div>
                        <div class="edit-form-group">
                            <label class="edit-form-label">公告内容</label>
                            <textarea class="edit-form-textarea edit-content" 
                                      placeholder="输入公告内容..." maxlength="500" required></textarea>
                            <div class="char-counter">
                                <span class="content-count">0</span>/500
                            </div>
                        </div>
                        <div class="edit-form-group">
                            <div class="edit-form-checkbox-group">
                                <input type="checkbox" class="edit-form-checkbox edit-active" checked>
                                <label for="editActive" class="edit-form-label" style="margin: 0;">
                                    是否显示公告
                                </label>
                            </div>
                        </div>
                        <div class="edit-form-actions">
                            <button type="button" class="edit-form-btn edit-form-btn-cancel">取消</button>
                            <button type="submit" class="edit-form-btn edit-form-btn-save">保存公告</button>
                        </div>
                    </form>
                </div>
            </div>
        `);

        this.menu.$menu.append(this.$board);
        this.root.$ac_game.append(this.$edit_modal);

        this.$toggle = this.$board.find('.ac-game-menu-announcement-toggle');
        this.$arrow = this.$board.find('.ac-game-menu-announcement-arrow');
        this.$content = this.$board.find('.ac-game-menu-announcement-content');
        this.$loading = this.$board.find('.ac-game-menu-announcement-loading');
        this.$list = this.$board.find('.ac-game-menu-announcement-list');
        this.$empty = this.$board.find('.ac-game-menu-announcement-empty');
        this.$add_btn = this.$board.find('.ac-game-menu-announcement-add-btn');

        this.$modal_close = this.$edit_modal.find('.edit-modal-close');
        this.$modal_cancel = this.$edit_modal.find('.edit-form-btn-cancel');
        this.$modal_title = this.$edit_modal.find('.edit-modal-title');
        this.$edit_form = this.$edit_modal.find('.edit-form');
        this.$title_input = this.$edit_modal.find('.edit-title');
        this.$content_input = this.$edit_modal.find('.edit-content');
        this.$active_checkbox = this.$edit_modal.find('.edit-active');
        this.$title_count = this.$edit_modal.find('.title-count');
        this.$content_count = this.$edit_modal.find('.content-count');

        this.start();
    }

    start() {
        this.add_listening_events();
    }

    add_listening_events() {
        let outer = this;

        // 切换公告显示
        this.$toggle.click(function() {
            outer.toggle_announcement();
        });

        // 新增公告按钮
        this.$add_btn.click(function(e) {
            e.stopPropagation();
            outer.open_edit_modal(null); // null 表示新增
        });

        // 关闭编辑模态框
        this.$modal_close.click(function() {
            outer.close_edit_modal();
        });

        this.$modal_cancel.click(function() {
            outer.close_edit_modal();
        });

        // 保存公告
        this.$edit_form.submit(function(e) {
            e.preventDefault();
            outer.save_announcement();
        });

        // 字符计数
        this.$title_input.on('input', function() {
            outer.$title_count.text($(this).val().length);
        });

        this.$content_input.on('input', function() {
            outer.$content_count.text($(this).val().length);
        });

        // 点击外部关闭
        $(document).click(function(e) {
            if (!$(e.target).closest('.ac-game-menu-announcement').length && outer.is_open) {
                outer.close_announcement();
            }

            if ($(e.target).hasClass('ac-game-menu-announcement-edit-modal')) {
                outer.close_edit_modal();
            }
        });

        // 阻止冒泡
        this.$content.click(function(e) {
            e.stopPropagation();
        });

        this.$edit_modal.find('.edit-modal-content').click(function(e) {
            e.stopPropagation();
        });

        // ESC键关闭
        $(window).keydown(function(e) {
            if (e.which === 27 && outer.$edit_modal.hasClass('active')) {
                outer.close_edit_modal();
            }
        });
    }

    toggle_announcement() {
        if (this.is_open) {
            this.close_announcement();
        } else {
            this.open_announcement();
        }
    }

    open_announcement() {
        this.is_open = true;
        this.$content.addClass('active');
        this.$arrow.addClass('active');
        this.load_announcements();
    }

    close_announcement() {
        this.is_open = false;
        this.$content.removeClass('active');
        this.$arrow.removeClass('active');
    }

    load_announcements() {
        let outer = this;

        // 显示加载状态
        this.$loading.show();
        this.$list.hide();
        this.$empty.hide();

        $.ajax({
            url: "https://app7562.acapp.acwing.com.cn/settings/get_announcements/",
            type: "GET",
            success: function(resp) {
                if (resp.result === "success") {
                    outer.is_admin = resp.is_admin;

                    // 显示/隐藏新增按钮
                    if (outer.is_admin) {
                        outer.$add_btn.show();
                    }

                    outer.render_announcements(resp.announcements);
                }
            },
            error: function() {
                outer.$loading.hide();
                outer.$empty.show();
            }
        });
    }

    render_announcements(announcements) {
        let outer = this;
        this.$loading.hide();

        if (announcements.length === 0) {
            this.$empty.show();
            this.$list.hide();
        } else {
            this.$list.empty();
            this.$empty.hide();
            this.$list.show();

            for (let ann of announcements) {
                let $item = $(`
                    <div class="ac-game-menu-announcement-item" data-id="${ann.id}">
                        <div class="announcement-item-content">
                            <strong>${this.escape_html(ann.title)}</strong>
                            <div>${this.escape_html(ann.content).replace(/\n/g, '<br>')}</div>
                            <span class="ac-game-menu-announcement-time">${ann.updated_at}</span>
                        </div>
                    </div>
                `);

                // 如果是管理员，添加编辑和删除按钮
                if (this.is_admin) {
                    let $actions = $(`
                        <div class="announcement-item-actions">
                            <button class="announcement-action-btn edit-btn" title="编辑">✏️</button>
                            <button class="announcement-action-btn delete-btn" title="删除">🗑️</button>
                        </div>
                    `);

                    $item.append($actions);

                    // 编辑按钮事件
                    $actions.find('.edit-btn').click(function(e) {
                        e.stopPropagation();
                        outer.open_edit_modal(ann);
                    });

                    // 删除按钮事件
                    $actions.find('.delete-btn').click(function(e) {
                        e.stopPropagation();
                        outer.delete_announcement(ann.id);
                    });
                }

                this.$list.append($item);
            }
        }
    }

    open_edit_modal(announcement) {
        this.current_edit_id = announcement ? announcement.id : null;

        if (announcement) {
            // 编辑模式
            this.$modal_title.text('📝 编辑系统公告');
            this.$title_input.val(announcement.title);
            this.$content_input.val(announcement.content);
            this.$title_count.text(announcement.title.length);
            this.$content_count.text(announcement.content.length);
            this.$active_checkbox.prop('checked', true);
        } else {
            // 新增模式
            this.$modal_title.text('➕ 新增系统公告');
            this.$title_input.val('');
            this.$content_input.val('');
            this.$title_count.text('0');
            this.$content_count.text('0');
            this.$active_checkbox.prop('checked', true);
        }

        this.$edit_modal.addClass('active');
    }

    close_edit_modal() {
        this.$edit_modal.removeClass('active');
        this.current_edit_id = null;
    }

    save_announcement() {
        let outer = this;
        let title = this.$title_input.val().trim();
        let content = this.$content_input.val().trim();
        let is_active = this.$active_checkbox.prop('checked');

        if (!title || !content) {
            alert('请填写完整的公告信息');
            return;
        }

        let url, data;

        if (this.current_edit_id) {
            // 更新现有公告
            url = "https://app7562.acapp.acwing.com.cn/settings/update_announcement/";
            data = {
                id: this.current_edit_id,
                title: title,
                content: content,
                is_active: is_active
            };
        } else {
            // 创建新公告
            url = "https://app7562.acapp.acwing.com.cn/settings/create_announcement/";
            data = {
                title: title,
                content: content,
                is_active: is_active
            };
        }

        $.ajax({
            url: url,
            type: "POST",
            headers: {
                'X-CSRFToken': this.get_csrf_token()
            },
            data: JSON.stringify(data),
            contentType: 'application/json',
            success: function(resp) {
                if (resp.result === "success") {
                    alert(outer.current_edit_id ? '公告更新成功！' : '公告创建成功！');
                    outer.close_edit_modal();
                    outer.load_announcements();
                } else {
                    alert(resp.message || '操作失败');
                }
            },
            error: function() {
                alert('网络错误，请重试');
            }
        });
    }

    delete_announcement(announcement_id) {
        let outer = this;

        if (!confirm('确定要删除这条公告吗？')) {
            return;
        }

        $.ajax({
            url: "https://app7562.acapp.acwing.com.cn/settings/delete_announcement/",
            type: "POST",
            headers: {
                'X-CSRFToken': this.get_csrf_token()
            },
            data: JSON.stringify({
                id: announcement_id
            }),
            contentType: 'application/json',
            success: function(resp) {
                if (resp.result === "success") {
                    alert('公告删除成功！');
                    outer.load_announcements();
                } else {
                    alert(resp.message || '删除失败');
                }
            },
            error: function() {
                alert('网络错误，请重试');
            }
        });
    }

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

    escape_html(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, m => map[m]);
    }
}