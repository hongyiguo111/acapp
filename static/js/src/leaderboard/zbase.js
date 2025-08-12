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