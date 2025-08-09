class AcGameMenu {
    constructor(root) {
        this.root = root;
        this.$menu = $(`
<div class="ac-game-menu">
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
            </div>
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
        this.$single_mode = this.$menu.find('.ac-game-menu-field-item-single-mode');
        this.$multi_mode = this.$menu.find('.ac-game-menu-field-item-multi-mode');
        this.$settings = this.$menu.find('.ac-game-menu-field-item-settings');
        this.$exit = this.$menu.find('.ac-game-menu-field-item-exit');

        this.$guide_toggle = this.$menu.find('.ac-game-menu-guide-toggle');
        this.$guide_content = this.$menu.find('.ac-game-menu-guide-content');
        this.$guide_arrow = this.$menu.find('.ac-game-menu-guide-arrow');

        this.start();
    }

    start() {
        this.add_listening_events();
    }

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
        this.$settings.click(function () {

        });
        this.$exit.click(function () {
            outer.root.settings.logout_on_remote();
        });
        
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

    show() {//显示menu界面
        this.$menu.show();
    }

    hide() {// 关闭menu界面
        this.$menu.hide();
    }


}

