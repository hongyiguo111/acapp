
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