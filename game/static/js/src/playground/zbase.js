class AcGamePlayground{
    constructor(root){
        this.root = root;
        this.$playground =$(`<div class="ac-game-playground"></div>`);

        this.create_confirm_dialog();

        this.hide();
        this.root.$ac_game.append(this.$playground);
        this.start();
    }

    get_random_color(){
        let colors = ["blue", "red", "pink", "grey", "green"];
        return colors[Math.floor(Math.random() * 5)];
    }

    // 退出游戏的提示框
    // 退出游戏的提示框
    create_confirm_dialog() {
        // 先创建一个简单的对话框结构
        this.$confirm_dialog = $(`
            <div class="ballblitz-confirm-dialog">
                <div class="ballblitz-confirm-box">
                    <h2>BallBlitz</h2>
                    <p>确定要退出游戏返回主菜单吗？当前游戏进度将会丢失。</p>
                    <button class="confirm-yes">确定</button>
                    <button class="confirm-no">取消</button>
                </div>
            </div>
        `);

        // 先隐藏对话框
        this.$confirm_dialog.hide();

        // 添加到游戏容器中
        this.root.$ac_game.append(this.$confirm_dialog);

        // 绑定按钮事件
        let outer = this;

        // 确定按钮 - 点击后返回菜单
        this.$confirm_dialog.find('.confirm-yes').click(function() {
            outer.$confirm_dialog.hide();  // 先隐藏对话框
            outer.hide();  // 隐藏游戏界面
            outer.root.menu.show();  // 显示菜单
        });

        // 取消按钮 - 点击后隐藏对话框
        this.$confirm_dialog.find('.confirm-no').click(function() {
            outer.$confirm_dialog.hide();
        });
    }

    start(){
        let outer = this;
        $(window).resize(function () {
            outer.resize();
        }); // 当用户改变窗口大小的时候，事件就会触发
    }

    resize() {
        this.width = this.$playground.width();
        this.height = this.$playground.height();
        let unit = Math.min(this.width / 16, this.height / 9);
        this.width = unit * 16;
        this.height = unit * 9;
        this.scale = this.height;

        if(this.game_map) this.game_map.resize();
    }

    // 摁下'esc'键退出游戏界面
    add_listening_events() {
        let outer = this;

        $(window).keydown(function(e) {
            if (e.which === 27) {
                // 显示我们自己的对话框，而不是用 confirm()
                outer.$confirm_dialog.show();
            }
        });
    }

    show() { // 打开playground界面
        this.$playground.show();

        this.resize();

        //存下来宽高
        this.width = this.$playground.width();
        this.height = this.$playground.height();
        this.game_map = new GameMap(this);
        this.players = [];
        this.players.push(new Player(this, this.width / 2 / this.scale, 0.5, 0.05, "white", 0.15, true));

        for(let i = 0 ; i < 5 ; i ++){
            this.players.push(new Player(this, this.width / 2 / this.scale, 0.5, 0.05, this.get_random_color(), 0.15, false));
        }

        // 添加监听函数，为了实现退出游戏的功能
        // this.add_listening_events()
    }
    
    hide(){ // 关闭playground界面
        this.$playground.hide();
    }

}

