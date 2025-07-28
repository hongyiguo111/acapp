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
    </div>
</div>
`);
        this.root.$ac_game.append(this.$menu);
        this.$single_mode = this.$menu.find('.ac-game-menu-field-item-single-mode');
        this.$multi_mode = this.$menu.find('.ac-game-menu-field-item-multi-mode');
        this.$settings = this.$menu.find('.ac-game-menu-field-item-settings');

        this.start();
    }

    start(){
        this.add_listening_events();
    }

    add_listening_events() {
        let outer = this;
        this.$single_mode.click(function(){
            outer.hide();
            outer.root.playground.show();
        });
        this.$multi_mode.click(function(){
            console.log("click multi mode");
        });
        this.$settings.click(function(){
            console.log("click settings");
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

     start(){

     }

     update(){  // 游戏地图每帧都要渲染
        this.render()
     }

     render(){
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
        this.eps = 1;
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
        this.ctx.beginPath();
        this.ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2, false);
        this.ctx.fillStyle = this.color;
        this.ctx.fill();
    }
}class Player extends AcGameObject{
    constructor(playground, x, y, radius, color, speed, is_me) {
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
        this.is_me = is_me;
        this.eps = 0.1;
        this.damage_vx = 0;
        this.damage_vy = 0;
        this.damage_speed = 0;
        this.friction = 0.9;
        this.spend_time = 0;

        this.cur_skill = null;
    }

    start() {
        if(this.is_me){
            this.add_listening_events();
        }else {
            let tx = Math.random() * this.playground.width;
            let ty = Math.random() * this.playground.height;
            this.move_to(tx, ty);
        }
    }

    add_listening_events() {
        let outer = this;
        this.playground.game_map.$canvas.on("contextmenu", function() {
            return false;
        });
        this.playground.game_map.$canvas.mousedown(function (e) {
            const rect = outer.ctx.canvas.getBoundingClientRect(); // <-----修复bug

            if (e.which === 3){//移动功能
                outer.move_to(e.clientX - rect.left, e.clientY - rect.top);// <-----修复bug
            }else if(e.which === 1){
                if(outer.cur_skill == "fireball"){
                    outer.shoot_fireball(e.clientX - rect.left, e.clientY - rect.top);
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
        let radius = this.playground.height * 0.01;
        let angle = Math.atan2(ty - this.y, tx - this.x);
        let vx = Math.cos(angle), vy = Math.sin(angle);
        let color = "orange";
        let speed = this.playground.height * 0.5;
        let move_length = this.playground.height * 1.0;
        let damage = this.playground.height * 0.01;
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
        if(this.radius < 10){
            this.destroy();
            return false;
        }

        this.damage_vx = Math.cos(angle);
        this.damage_vy = Math.sin(angle);
        this.damage_speed = damage * 100;
        this.speed *= 0.8;
    }

    update() {
        this.spend_time += this.timedelta / 1000;
        if(!this.is_me && this.spend_time > 5 && Math.random() < 1 / 360.0){
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
                    if (!this.is_me) {
                        let tx = Math.random() * this.playground.width;
                        let ty = Math.random() * this.playground.height;
                        this.move_to(tx, ty);
                    }

                } else {
                    let moved = Math.min(this.move_length, this.speed * this.timedelta / 1000);
                    this.x += this.vx * moved;
                    this.y += this.vy * moved;

                    this.move_length -= moved;
                }
            }
            this.render();
        }

    render() {
        this.ctx.beginPath();
        this.ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2, false);
        this.ctx.fillStyle = this.color;
        this.ctx.fill();
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
        this.damage = damage;;
        this.eps = 0.1;
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
        this.ctx.beginPath();
        this.ctx.arc(this.x, this.y, this.radius, 0, 2 * Math.PI, false);
        this.ctx.fillStyle  = this.color;
        this.ctx.fill();
    }
}class AcGamePlayground{
    constructor(root){
        this.root = root;
        this.$playground =$(`<div class="ac-game-playground"></div>`);
        
        this.hide();

        this.start();
    }

    get_random_color(){
        let colors = ["blue", "red", "pink", "grey", "green"];
        return colors[Math.floor(Math.random() * 5)];
    }

    start(){
    
    }


    show(){ // 打开playground界面
        this.$playground.show();
        this.root.$ac_game.append(this.$playground);
        //存下来宽高
        this.width = this.$playground.width();
        this.height = this.$playground.height();
        this.game_map = new GameMap(this);
        this.players = [];
        this.players.push(new Player(this, this.width / 2, this.height / 2, this.height * 0.05, "white", this.height * 0.15, true));

        for(let i = 0 ; i < 5 ; i ++){
            this.players.push(new Player(this, this.width / 2, this.height / 2, this.height * 0.05, this.get_random_color(), this.height * 0.15, false));
        }
    }
    
    hide(){ // 关闭playground界面
        this.$playground.hide();
    }

}

export class AcGame{
    constructor(id){
        this.id = id;
        this.$ac_game = $('#' + id);
        this.menu = new AcGameMenu(this);
        this.playground = new AcGamePlayground(this);

        this.start();
    }

    start(){
    }
}

