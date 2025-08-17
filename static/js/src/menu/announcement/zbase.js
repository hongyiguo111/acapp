class AnnouncementBoard {
    constructor(menu) {
        this.menu = menu;
        this.root = menu.root;

        this.$board = $(`
            <div class="ac-game-menu-announcement">
            <div class="ac-game-menu-announcement-toggle">
                <span class="ac-game-menu-announcement-text">系统公告</span>
                <span class="ac-game-menu-announcement-arrow">▼</span>
            </div>
            <div class="ac-game-menu-announcement-content">
                
            </div>
        </div>
        `)

        this.menu.$menu.append(this.$board);
    }
}