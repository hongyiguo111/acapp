class AcGameMenu{
    constructor(root){
        this.root = root;
        this.$menu = $(`
<div class="ac-game-menu">
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

        this.start();
    }

    start(){
        this.add_listening_events();
    }

    add_listening_events() {
        let outer = this;
        this.$single_mode.click(function(){
            outer.hide();
            outer.root.playground.show("single mode");
        });
        this.$multi_mode.click(function(){
            outer.hide();
            outer.root.playground.show("multi mode");
        });
        this.$settings.click(function(){
            console.log("click settings");
        });
        this.$exit.click(function(){
            console.log("exit");
            outer.root.settings.logout_on_remote();
        });
    }

    show(){//显示menu界面
        this.$menu.show();
    }

    hide(){// 关闭menu界面
        this.$menu.hide();
    }


}

let AC_GAME_OBJECTS = []; //用于记录当前画布中，需要渲染的对象有哪些

class AcGameObject{
    constructor() {
        AC_GAME_OBJECTS.push(this); //将当前新建的对象，加入到全局的画布中去，参与渲染

        this.has_called_start = false; //是否执行过start
        this.timedelta = 0 ; // 当前帧距离上一帧的时间间隔
        // 该数据记录是为了后续计算速度等参数的
        this.uuid = this.create_uuid();
    }

    create_uuid() {
        let res = "";
        for(let i = 0 ; i < 8 ; i ++){
            let x = parseInt(Math.floor(Math.random() * 10)); // 返回[0,1) 之间的数
            res += x;
        }
        return res;
    }

    start(){ // 只会在第一帧执行一次

    }

    update(){ // 每一帧均会执行一次

    }

    on_destroy(){ // 在销毁前执行一次

    }


    destroy(){ // 删掉该物体
        this.on_destroy(); // 删掉该物体前，执行删前的操作

        // 在全局渲染物体中，找到该物体，并将其删掉
        for(let i = 0 ; i < AC_GAME_OBJECTS.length ; i ++){
            if(AC_GAME_OBJECTS[i] === this){  // 三等号，在js里额外加了一层类型相等约束
                AC_GAME_OBJECTS.splice(i, 1);
                break;
            }
        }
    }
}

let last_timestamp;

let AC_GAME_ANIMATION = function (timestamp){ // 回调函数，实现：每一帧重绘时，都会执行一遍
    for(let i = 0 ; i < AC_GAME_OBJECTS.length ; i ++){
        let obj = AC_GAME_OBJECTS[i];
        if(!obj.has_called_start) { // 如果还未执行初始帧动作，就先执行
            obj.start();
            obj.has_called_start = true;
        }else { // 执行过初始帧，就执行每一帧的任务
            obj.timedelta = timestamp - last_timestamp;
            obj.update();
        }
    }

    last_timestamp = timestamp;
    requestAnimationFrame(AC_GAME_ANIMATION);
}


requestAnimationFrame(AC_GAME_ANIMATION); // js提供的api，其功能请见笔记
class GameMap extends AcGameObject { // 继承自游戏引擎基类
    constructor(playground) {
        super(); // 自函数功能：调用基类的构造函数
        this.playground = playground;
        this.$canvas = $(`<canvas></canvas>`)//创建一个canvas的jQuery对象，就是我们要实现的画布
        this.ctx = this.$canvas[0].getContext('2d'); //jQuery对象是一个数组，第一个索引是html对象
        //设置画布的宽高
        this.ctx.canvas.width = this.playground.width;
        this.ctx.canvas.height = this.playground.height;
        this.playground.$playground.append(this.$canvas);
    }

     start() {
     }

     resize() {
        this.ctx.canvas.width = this.playground.width;
        this.ctx.canvas.height = this.playground.height;
        this.ctx.fillStyle = "rgba(0, 0, 0, 1)";
        this.ctx.fillRect(0, 0, this.ctx.canvas.width, this.ctx.canvas.height);
     }

     update() {  // 游戏地图每帧都要渲染
        this.render()
     }

     render() {
        this.ctx.fillStyle = "rgba(0, 0, 0, 0.2)";
        this.ctx.fillRect(0, 0, this.ctx.canvas.width, this.ctx.canvas.height);
     }
}
class Particle extends AcGameObject {
    constructor(playground, x, y, radius, vx, vy, color, speed, move_length) {
        super();
        this.playground = playground;
        this.ctx = this.playground.game_map.ctx;
        this.x = x;
        this.y = y;
        this.radius = radius;
        this.vx = vx;
        this.vy = vy;
        this.color = color;
        this.speed = speed;
        this.friction = 0.9;
        this.eps = 0.01;
        this.move_length = move_length;
    }

    start(){

    }

    update(){
        if(this.move_length < this.eps || this.speed < this.eps){
            this.destroy();
            return false;
        }
        let moved = Math.min(this.move_length, this.speed * this.timedelta / 1000);
        this.x += this.vx * moved;
        this.y += this.vy * moved;
        this.speed *= this.friction;
        this.move_length -= moved;
        this.render();
    }

    render(){
        let scale = this.playground.scale;
        this.ctx.beginPath();
        this.ctx.arc(this.x * scale, this.y * scale, this.radius * scale, 0, Math.PI * 2, false);
        this.ctx.fillStyle = this.color;
        this.ctx.fill();
    }
}class Player extends AcGameObject{
    constructor(playground, x, y, radius, color, speed, character, username, photo) {
        console.log(character, username, photo);
        super();
        this.playground = playground;
        this.ctx = this.playground.game_map.ctx;
        this.x = x;
        this.y = y;
        this.vx = 0;
        this.vy = 0;
        this.move_length = 0;
        this.radius = radius;
        this.color = color;
        this.speed = speed;
        this.character = character;
        this.username = username;
        this.photo = photo;
        this.eps = 0.01;
        this.damage_vx = 0;
        this.damage_vy = 0;
        this.damage_speed = 0;
        this.friction = 0.9;
        this.spend_time = 0;

        this.cur_skill = null;

        if(this.character !== "robot") { // 只有不是机器人 才需要渲染图片
            this.img = new Image();
            this.img.src = this.photo;
        }
    }

    start() {
        if(this.character === "me"){
            this.add_listening_events();
        }else if(this.character === "robot") {
            let tx = Math.random() * this.playground.width / this.playground.scale;
            let ty = Math.random() * this.playground.height / this.playground.scale;
            this.move_to(tx, ty);
        }
    }

    add_listening_events() {
        let outer = this;
        this.playground.game_map.$canvas.on("contextmenu", function() {
            return false;
        });
        this.playground.game_map.$canvas.mousedown(function (e) {
            const rect = outer.ctx.canvas.getBoundingClientRect();

            if (e.which === 3){//移动功能
                outer.move_to((e.clientX - rect.left) / outer.playground.scale, (e.clientY - rect.top) / outer.playground.scale);
            }else if(e.which === 1){
                if(outer.cur_skill == "fireball"){
                    outer.shoot_fireball((e.clientX - rect.left) / outer.playground.scale,  (e.clientY - rect.top) / outer.playground.scale);
                }
                outer.cur_skill = null;
            }
        });
        $(window).keydown(function(e){
            if(e.which === 81){
                outer.cur_skill = "fireball";
                return false;
            }
        });
    }

    shoot_fireball(tx, ty){
        let x = this.x;;
        let y = this.y;
        let radius = 0.01;
        let angle = Math.atan2(ty - this.y, tx - this.x);
        let vx = Math.cos(angle), vy = Math.sin(angle);
        let color = "orange";
        let speed = 0.5;
        let move_length =  1.0;
        let damage =  0.01;
        new FireBall(this.playground, this, x, y, radius, vx, vy, color, speed, move_length, damage);
    }

    get_dist(x1, y1, x2, y2){
        let dx = x1 - x2;
        let dy = y1 - y2;
        return Math.sqrt(dx * dx + dy * dy);
    }

    move_to(tx, ty) {
        this.move_length = this.get_dist(this.x, this.y, tx, ty);
        let angle = Math.atan2(ty - this.y, tx - this.x);
        this.vx = Math.cos(angle);
        this.vy = Math.sin(angle);
    }

    is_attack(angle, damage){
        for(let i = 0 ; i < 10 + Math.random() * 5 ; i ++){
            let x = this.x;
            let y = this.y;
            let radius = this.radius * Math.random() * 0.1;
            let angle = Math.PI * 2 * Math.random();
            let vx = Math.cos(angle), vy = Math.sin(angle);
            let color = this.color;
            let speed = this.speed * 10;
            let move_length = this.radius * Math.random() * 5;
            new Particle(this.playground, x, y, radius, vx, vy, color, speed, move_length);
        }

        this.radius -= damage;
        if(this.radius < this.eps){
            this.destroy();
            return false;
        }

        this.damage_vx = Math.cos(angle);
        this.damage_vy = Math.sin(angle);
        this.damage_speed = damage * 100;
        this.speed *= 0.8;
    }

    update() {
            this.update_move();
            this.render();
        }

    update_move() {
        this.spend_time += this.timedelta / 1000;
        if(this.character === "robot" && this.spend_time > 5 && Math.random() < 1 / 360.0){
            let player = this.playground.players[Math.floor(Math.random() * this.playground.players.length)];
            let tx = player.x + player.speed * player.vx * this.timedelta / 1000 * 0.3;
            let ty = player.y + player.speed * player.vy * this.timedelta / 1000 * 0.3;
            this.shoot_fireball(tx, ty);
        }
        if (this.damage_speed > this.eps) {   //当前仍处于击退效果中
        this.vx = this.vy = 0;
        this.move_length = 0;
        this.x += this.damage_vx * this.damage_speed * this.timedelta / 1000;
        this.y += this.damage_vy * this.damage_speed * this.timedelta / 1000;
        this.damage_speed *= this.friction; // 击退速度乘以摩擦系数，已达到削减的目的
        } else {
                if (this.move_length < this.eps) {
                    this.move_length = 0;
                    this.vx = this.vy = 0;
                    if (this.character === "robot") {
                        let tx = Math.random() * this.playground.width / this.playground.scale;
                        let ty = Math.random() * this.playground.height / this.playground.scale;
                        this.move_to(tx, ty);
                    }

                } else {
                    let moved = Math.min(this.move_length, this.speed * this.timedelta / 1000);
                    this.x += this.vx * moved;
                    this.y += this.vy * moved;

                    this.move_length -= moved;
                }
            }
    }

    render() {
        let scale = this.playground.scale;
        if (this.character !== "robot") {
            this.ctx.save();
            this.ctx.beginPath();
            this.ctx.arc(this.x * scale, this.y * scale, this.radius * scale, 0, Math.PI * 2, false);
            this.ctx.stroke();
            this.ctx.clip();
            this.ctx.drawImage(this.img, (this.x - this.radius) * scale, (this.y - this.radius) * scale,
                               this.radius * 2 * scale, this.radius * 2 * scale);
            this.ctx.restore();
        } else {
            this.ctx.beginPath();
            this.ctx.arc(this.x * scale, this.y * scale, this.radius * scale, 0, Math.PI * 2, false);
            this.ctx.fillStyle = this.color;
            this.ctx.fill();
        }
    }

    on_destroy(){
        for(let i = 0 ; i < this.playground.players.length ; i ++){
            if(this.playground.players[i] === this){
                this.playground.players.splice(i, 1);
            }
        }
    }
}class FireBall extends AcGameObject {
    constructor(playground, player, x, y, raidus, vx, vy, color, speed, move_length, damage) {
        super();
        this.playground = playground;
        this.ctx = this.playground.game_map.ctx;
        this.player = player;
        this.x = x;
        this.y = y;
        this.vx = vx;
        this.vy = vy;
        this.radius = raidus;
        this.color = color;
        this.speed = speed;
        this.move_length = move_length;
        this.damage = damage;
        this.eps = 0.01;
    }

    start(){

    }

    update(){
        if(this.move_length < this.eps){
            this.destroy();
            return false;
        }else{
            let moved = Math.min(this.move_length, this.speed * this.timedelta / 1000);
            this.x += this.vx * moved;
            this.y += this.vy * moved;
            this.move_length -= moved;

            for(let i = 0 ; i < this.playground.players.length ; i ++){
                let player = this.playground.players[i];
                if(this.player !== player && this.is_collision(player)){
                    this.attack(player);
                }
            }
        }
        this.render();
    }

    get_dist(x1, y1, x2, y2){
        let dx = x1 - x2;
        let dy = y1 - y2;
        return Math.sqrt(dx * dx + dy * dy);
    }

    is_collision(player){
        let distance = this.get_dist(this.x, this.y, player.x, player.y);
        if(distance < (this.radius + player.radius))
            return true;
        return false;
    }

    attack(player){
        let angle = Math.atan2(player.y - this.y, player.x - this.x);
        player.is_attack(angle, this.damage);
        this.destroy();
    }

    render(){
        let scale = this.playground.scale;
        this.ctx.beginPath();
        this.ctx.arc(this.x * scale, this.y * scale, this.radius * scale, 0, 2 * Math.PI, false);
        this.ctx.fillStyle  = this.color;
        this.ctx.fill();
    }
}class MultiPlayerSocket {
    constructor(playground) {
        this.playground = playground;

        this.ws = new WebSocket("wss://app7549.acapp.acwing.com.cn/wss/multiplayer/");

        this.start();
    }

    start() {
        this.receive();
    }

    receive() {
        let outer = this;
        this.ws.onmessage = function(e) {
            let data = JSON.parse(e.data);
            let uuid = data.uuid;

            if (uuid === outer.uuid) return false;

            let event = data.event;
            if (event === "create_player") {
                outer.receive_create_player(uuid, data.username, data.photo);
            }
        };
    }

    send_create_player(username, photo) {
        let outer = this;
        this.ws.send(JSON.stringify({
            'event': "create_player",
            'uuid': outer.uuid,
            'username': username,
            'photo': photo,
        }));
    }

    receive_create_player(uuid, username, photo) {
        let player = new Player(
            this.playground,
            this.playground.width / 2 / this.playground.scale,
            0.5,
            0.05,
            "white",
            0.15,
            "enemy",
            username,
            photo,
        );
        player.uuid =  uuid;
        this.playground.players.push(player);
    }
}class AcGamePlayground{
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

    show(mode) { // 打开playground界面
        let outer = this;
        this.$playground.show();
        //存下来宽高
        this.width = this.$playground.width();
        this.height = this.$playground.height();
        this.game_map = new GameMap(this);

        this.resize();

        this.players = [];
        this.players.push(new Player(this, this.width / 2 / this.scale, 0.5, 0.05, "white", 0.15, "me", this.root.settings.username, this.root.settings.photo));
        if(mode === "single mode") {
            for (let i = 0; i < 5; i++) {
                this.players.push(new Player(this, this.width / 2 / this.scale, 0.5, 0.05, this.get_random_color(), 0.15, "robot"));
            }
        } else if (mode === "multi mode"){
            this.mps = new MultiPlayerSocket(this);
            this.mps.uuid = this.players[0].uuid;

            this.mps.ws.onopen = function () {
                outer.mps.send_create_player(outer.root.settings.username, outer.root.settings.photo);
            };
        }
        // 添加监听函数，为了实现退出游戏的功能
        // this.add_listening_events()
    }
    
    hide(){ // 关闭playground界面
        this.$playground.hide();
    }

}

class Settings {
    constructor(root) {
        this.root = root;
        this.platform = "WEB";
        if(this.root.AcWingOS) this.platform = "ACAPP";
        this.username = '';
        this.photo = '';

        this.$settings = $(`
<div class="ac-game-settings">
    <div class="ac-game-settings-login">
        <div class="ac-game-settings-title">
            登录
        </div>
        <div class="ac-game-settings-username">
            <div class="ac-game-settings-item">
                <input type="text" placeholder="用户名">
            </div>
        </div>
        <div class="ac-game-settings-password">
            <div class="ac-game-settings-item">
                <input type="password" placeholder="密码">
            </div>
        </div>
        <div class="ac-game-settings-submit">
            <div class="ac-game-settings-item">
                <button>登录</button>
            </div>
        </div>
        <div class="ac-game-settings-error-message">
        </div>
        <div class="ac-game-settings-option">
            注册
        </div>
        <br>
        <div class="ac-game-settings-acwing">
            <img width="30" src="https://app7549.acapp.acwing.com.cn/static/image/login/acwing.png"  alt="AcWing Login">
        </div>
        <div class="ac-game-settings-github">
            <img src="https://app7549.acapp.acwing.com.cn/static/image/login/github.png" alt="GitHub Login">
        </div>
            <div class="ac-game-settings-gitee">
            <img src="https://app7549.acapp.acwing.com.cn/static/image/login/gitee.png" alt="Gitee Login">
        </div>
    </div>
    <div class="ac-game-settings-register">
        <div class="ac-game-settings-title">
            注册
        </div>
        <div class="ac-game-settings-username">
            <div class="ac-game-settings-item">
                <input type="text" placeholder="用户名">
            </div>
        </div>
        <div class="ac-game-settings-password ac-game-settings-password-first">
            <div class="ac-game-settings-item">
                <input type="password" placeholder="密码">
            </div>
        </div>
        <div class="ac-game-settings-password ac-game-settings-password-second">
            <div class="ac-game-settings-item">
                <input type="password" placeholder="确认密码">
            </div>
        </div>
        <div class="ac-game-settings-submit">
            <div class="ac-game-settings-item">
                <button>注册</button>
            </div>
        </div>
        <div class="ac-game-settings-error-message">
        </div>
        <div class="ac-game-settings-option">
            登录
        </div>
        <br>
        <div class="ac-game-settings-acwing" title="AcWing 一键登录">
            <img width="30" src="https://app7549.acapp.acwing.com.cn/static/image/login/acwing.png"  alt="AcWing Login">
        </div>
        <div class="ac-game-settings-github" title="GitHub 一键登录">
            <img src="https://app7549.acapp.acwing.com.cn/static/image/login/github.png" alt="GitHub Login">
        </div>
            <div class="ac-game-settings-gitee" title="Gitee 一键登录">
            <img src="https://app7549.acapp.acwing.com.cn/static/image/login/gitee.png" alt="Gitee Login">
        </div>
    </div>
`);
        this.$login = this.$settings.find(".ac-game-settings-login");
        this.$login_username = this.$login.find(".ac-game-settings-username input");
        this.$login_password = this.$login.find(".ac-game-settings-password input");
        this.$login_submit = this.$login.find(".ac-game-settings-submit button");
        this.$login_error_message = this.$login.find(".ac-game-settings-error-message");
        this.$login_register = this.$login.find(".ac-game-settings-option");

        this.$login.hide();

        this.$register = this.$settings.find(".ac-game-settings-register");
        this.$register_username = this.$register.find(".ac-game-settings-username input");
        this.$register_password = this.$register.find(".ac-game-settings-password-first input");
        this.$register_password_confirm = this.$register.find(".ac-game-settings-password-second input");
        this.$register_submit = this.$register.find(".ac-game-settings-submit button");
        this.$register_error_message = this.$register.find(".ac-game-settings-error-message");
        this.$register_login = this.$register.find(".ac-game-settings-option");

        this.$register.hide();

        this.$acwing_login = this.$settings.find('.ac-game-settings-acwing img');
        this.$github_login = this.$settings.find('.ac-game-settings-github img');
        this.$gitee_login = this.$settings.find('.ac-game-settings-gitee img'); // 新增

        this.add_listening_events();

        this.root.$ac_game.append(this.$settings);

        this.start();
    }

    start() {
        if(this.platform === "ACAPP"){
            this.getinfo_acapp();
        }
        else {
            this.getinfo_web();
            this.add_listening_events();
        }
    }

    add_listening_events() {
        let outer = this;
        this.add_listening_events_login();
        this.add_listening_events_register();

        this.$acwing_login.click(function () {
            outer.acwing_login();
        })

        this.$github_login.click(function () {
            outer.github_login();
        })

        // Gitee 登录（新增）
        this.$gitee_login.click(function() {
            outer.gitee_login();
        });
    }

    acwing_login() {
        $.ajax({
            url: "https://app7549.acapp.acwing.com.cn/settings/acwing/web/apply_code/",
            type: "GET",
            success: function (resp) {
                console.log(resp);
                if(resp.result === "success") {
                    window.location.replace(resp.apply_code_url);
                }
            }
        })
    }

    github_login() {
        $.ajax({
            url: "https://app7549.acapp.acwing.com.cn/settings/github/web/apply_code/",
            type: "GET",
            success: function (resp) {
                console.log(resp);
                if (resp.result === "success") {
                    window.location.replace(resp.apply_code_url);
                }
            },
            error: function(xhr, status, error) {
                console.error("GitHub 登录失败:", error);
                alert("GitHub 登录暂时不可用，请稍后重试");
            }
        });
    }

    gitee_login() {
        $.ajax({
            url: "/settings/gitee/web/apply_code/",
            type: "GET",
            success: function(resp) {
                console.log(resp);
                if (resp.result === "success") {
                    window.location.replace(resp.apply_code_url);
                }
            },
            error: function(xhr, status, error) {
                console.error("Gitee 登录失败:", error);
                alert("Gitee 登录暂时不可用，请稍后重试");
            }
        });
    }

    add_listening_events_login() {
        let outer = this;
        this.$login_register.click(function (){
            outer.register();
        });
        this.$login_submit.click(function () {
            outer.login_on_remote();
        });

        this.$login_username.keydown(function(e) {
        if (e.which === 13) {  // 13 是回车键的键码
            outer.login_on_remote();
        }
        });

        this.$login_password.keydown(function(e) {
        if (e.which === 13) {  // 13 是回车键的键码
            outer.login_on_remote();
        }
        });

    }

    add_listening_events_register() {
        let outer = this;
        this.$register_login.click(function () {
            outer.login();
        });

        this.$register_submit.click(function () {
            outer.register_on_remote();
        });
        // 添加回车键监听
        this.$register_username.keydown(function(e) {
            if (e.which === 13) {  // 13 是回车键的键码
                outer.register_on_remote();
            }
        });

        this.$register_password.keydown(function(e) {
            if (e.which === 13) {  // 13 是回车键的键码
                outer.register_on_remote();
            }
        });

        this.$register_password_confirm.keydown(function(e) {
            if (e.which === 13) {  // 13 是回车键的键码
                outer.register_on_remote();
            }
        });
    }

    login_on_remote() { // 在远程服务器上登录
        let outer = this;
        let username = this.$login_username.val();
        let password = this.$login_password.val();
        this.$login_error_message.empty();
        $.ajax({
            url: "https://app7549.acapp.acwing.com.cn/settings/login/",
            type: "GET",
            data: {
                username: username,
                password: password,
            },
            success:function (resp) {
                console.log(resp);
                if(resp.result === "success") {
                    location.reload();
                } else {
                    outer.$login_error_message.html(resp.result);
                }
            }
        });
    }

    register_on_remote() { // 在远程服务器上注册
        let outer = this;
        let username = this.$register_username.val();
        let password = this.$register_password.val();
        let password_confirm = this.$register_password_confirm.val();
        this.$register_error_message.empty();

        $.ajax({
            url: "https://app7549.acapp.acwing.com.cn/settings/register/",
            type: "GET",
            data: {
                username: username,
                password: password,
                password_confirm: password_confirm,
            },
            success: function (resp) {
                console.log(resp);
                if(resp.result === "success"){
                    location.reload();
                } else {
                    outer.$register_error_message.html(resp.result);
                }
            }
        })
    }

    logout_on_remote() { // 在远程服务器上登出
        if(this.platform === "ACAPP") return false;

        $.ajax({
            url: "https://app7549.acapp.acwing.com.cn/settings/logout/",
            type: "GET",
            success: function (resp) {
                console.log(resp);
                if(resp.result === "success"){
                    location.reload()
                }
            }
        })
    }

    register(){ // 打开注册界面
        this.$login.hide();
        this.$register.show();
    }

    acapp_login(appid, redirect_uri, scope, state) {
        let outer = this;
         this.root.AcWingOS.api.oauth2.authorize(appid, redirect_uri, scope, state, function (resp) {
            console.log(resp);
            if(resp.result === "success") {
               outer.username= resp.username;
               outer.photo = resp.photo;
               outer.hide();
               outer.root.menu.show();
            }
         });
    }

    login() { // 打开登陆界面
        this.$login.show();
        this.$register.hide();
    }

    getinfo_acapp() {
        let outer = this;
        $.ajax({
            url: "https://app7549.acapp.acwing.com.cn/settings/acwing/acapp/apply_code/",
            type: "GET",
            success: function (resp) {
                if(resp.result === "success"){
                    outer.acapp_login(resp.appid, resp.redirect_uri, resp.scope, resp.state);
                }
            }
        })
    }

    getinfo_web() {
        let outer = this;

        $.ajax({
            url: "https://app7549.acapp.acwing.com.cn/settings/getinfo/",
            type: "GET",
            data: {
                platform: outer.platform,
            },
            success: function (resp) {
                console.log(resp);
                if(resp.result === "success") {
                    outer.username = resp.username;
                    outer.photo =  resp.photo;
                    outer.hide();
                    outer.root.menu.show();
                } else {
                    outer.login();
                }
            }
        })
    }

    hide() {
        this.$settings.hide();
    }

    show() {
        this.$settings.show();
    }

}
export class AcGame{
    constructor(id, AcWingOS){
        this.id = id;
        this.$ac_game = $('#' + id);
        this.AcWingOS = AcWingOS;

        this.settings = new Settings(this);
        this.menu = new AcGameMenu(this);
        this.playground = new AcGamePlayground(this);

        this.start();
    }

    start(){
    }
}

