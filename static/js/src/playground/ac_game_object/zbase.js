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
