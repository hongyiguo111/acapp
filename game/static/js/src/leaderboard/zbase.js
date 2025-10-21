class AcGameLeaderboard {
    constructor(root) {
        this.root = root;
        this.current_page = 1;
        this.total_pages = 1;
        this.current_player_rank = null;
        this.current_player_data = null;
        this.saved_player_info = null; // 保存玩家的完整信息

        // 段位系统配置
        this.tierSystem = {
            tiers: [
                { minScore: 0, maxScore: 299, name: '青铜', nameEN: 'Bronze', icon: '🥉', colorClass: 'tier-bronze' },
                { minScore: 300, maxScore: 599, name: '白银', nameEN: 'Silver', icon: '🥈', colorClass: 'tier-silver' },
                { minScore: 600, maxScore: 999, name: '黄金', nameEN: 'Gold', icon: '🥇', colorClass: 'tier-gold' },
                { minScore: 1000, maxScore: 1399, name: '铂金', nameEN: 'Platinum', icon: '💎', colorClass: 'tier-platinum' },
                { minScore: 1400, maxScore: 1799, name: '钻石', nameEN: 'Diamond', icon: '💠', colorClass: 'tier-diamond' },
                { minScore: 1800, maxScore: 2199, name: '大师', nameEN: 'Master', icon: '👑', colorClass: 'tier-master' },
                { minScore: 2200, maxScore: 2599, name: '宗师', nameEN: 'Grandmaster', icon: '⚔️', colorClass: 'tier-grandmaster' },
                { minScore: 2600, maxScore: 99999, name: '王者', nameEN: 'Champion', icon: '🏆', colorClass: 'tier-champion' }
            ]
        };

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
                    <div class="ac-game-leaderboard-player-card"></div>
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

        this.$player_card = this.$leaderboard.find('.ac-game-leaderboard-player-card');
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

    // 计算段位信息
    calculateTier(score) {
        for (let tier of this.tierSystem.tiers) {
            if (score >= tier.minScore && score <= tier.maxScore) {
                // 计算段内进度
                let tierRange = tier.maxScore - tier.minScore + 1;
                let scoreInTier = score - tier.minScore;
                let progress = (scoreInTier / tierRange) * 100;

                // 计算细分等级 (I-V)
                let subLevel = '';
                let levelProgress = scoreInTier / tierRange;
                if (levelProgress < 0.2) subLevel = 'V';
                else if (levelProgress < 0.4) subLevel = 'IV';
                else if (levelProgress < 0.6) subLevel = 'III';
                else if (levelProgress < 0.8) subLevel = 'II';
                else subLevel = 'I';

                // 计算到下一段位还需要的分数
                let nextTierScore = tier.maxScore + 1;
                let pointsToNext = nextTierScore - score;

                return {
                    ...tier,
                    subLevel: subLevel,
                    displayName: `${tier.name} ${subLevel}`,
                    progress: progress,
                    pointsToNext: pointsToNext > 0 ? pointsToNext : 0
                };
            }
        }
        return this.tierSystem.tiers[this.tierSystem.tiers.length - 1];
    }

    show() {
        this.$leaderboard.show();
        this.saved_player_info = null; // 重置保存的玩家信息
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
            url: "https://app7562.acapp.acwing.com.cn/settings/ranklist/",
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

    // 查找当前玩家数据
    findCurrentPlayer(ranklist) {
        let currentUsername = this.root.settings.username;

        for (let player of ranklist) {
            if (player.username === currentUsername) {
                return player;
            }
        }
        return null;
    }

    // 渲染当前玩家卡片
    renderPlayerCard(playerData) {
        // 如果找到了玩家数据，保存它
        if (playerData) {
            this.saved_player_info = playerData;
        }

        // 优先使用传入的数据，如果没有则使用保存的数据
        let displayData = playerData || this.saved_player_info;

        if (!displayData) {
            // 如果都没有，显示默认信息
            displayData = {
                rank: '未上榜',
                username: this.root.settings.username,
                photo: this.root.settings.photo,
                score: 1500 // 默认分数
            };
        }

        let tierInfo = this.calculateTier(displayData.score);

        let playerCardHTML = `
            <div class="ac-game-leaderboard-player-info">
                <div class="ac-game-leaderboard-player-rank">
                    <div class="ac-game-leaderboard-player-rank-number">#${displayData.rank}</div>
                    <div class="ac-game-leaderboard-player-rank-label">你的排名</div>
                </div>
                <img class="ac-game-leaderboard-player-avatar" 
                     src="${displayData.photo}" 
                     alt="${displayData.username}"
                     onerror="this.src='https://app7562.acapp.acwing.com.cn/static/image/favicon/favicon.png'">
                <div class="ac-game-leaderboard-player-details">
                    <div class="ac-game-leaderboard-player-name">${displayData.username}</div>
                    <div class="ac-game-leaderboard-player-tier">
                        <span class="ac-game-leaderboard-tier-badge ${tierInfo.colorClass}">
                            <span class="ac-game-leaderboard-tier-icon">${tierInfo.icon}</span>
                            ${tierInfo.displayName}
                        </span>
                        <div class="ac-game-leaderboard-tier-progress">
                            <div class="ac-game-leaderboard-progress-bar">
                                <div class="ac-game-leaderboard-progress-fill" style="width: ${tierInfo.progress}%"></div>
                            </div>
                            <span>还需 ${tierInfo.pointsToNext} 分升级</span>
                        </div>
                    </div>
                </div>
                <div class="ac-game-leaderboard-player-score">
                    <div class="ac-game-leaderboard-player-score-value">${displayData.score}</div>
                    <div class="ac-game-leaderboard-player-score-label">积分</div>
                </div>
            </div>
        `;

        this.$player_card.html(playerCardHTML);
    }

    render_ranklist(data) {
    let outer = this;

    // 优先使用后端返回的当前用户信息
    let currentPlayer = data.current_user || this.findCurrentPlayer(data.ranklist);
    this.renderPlayerCard(currentPlayer);

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

        let tierInfo = outer.calculateTier(player.score);

        let $row = $(`
            <div class="ac-game-leaderboard-row ${rank_class}">
                <div class="ac-game-leaderboard-rank">
                    ${player.rank <= 3 ? player.rank + '👑' : player.rank}
                </div>
                <div class="ac-game-leaderboard-user">
                    <img class="ac-game-leaderboard-avatar" 
                         src="${player.photo}" 
                         alt="${player.username}"
                         onerror="this.src='https://app7562.acapp.acwing.com.cn/static/image/favicon/favicon.png'">
                    <span class="ac-game-leaderboard-username">${player.username}</span>
                </div>
                <div class="ac-game-leaderboard-tier">
                    <span class="ac-game-leaderboard-tier-mini ${tierInfo.colorClass}">
                        <span class="ac-game-leaderboard-tier-mini-icon">${tierInfo.icon}</span>
                        ${tierInfo.displayName}
                    </span>
                </div>
                <div class="ac-game-leaderboard-score">${player.score}</div>
            </div>
        `);

        // 如果是当前玩家，添加特殊高亮
        if (player.username === outer.root.settings.username) {
            $row.css({
                'background': 'rgba(102, 126, 234, 0.15)',
                'border-color': 'rgba(102, 126, 234, 0.5)'
            });
        }

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