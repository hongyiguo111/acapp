// Florr-style co-op mode. The server owns the world (see game/consumers/florr/world.py);
// this class only sends input and draws what the server reports. It has its own canvas and
// render loop and does not touch the original playground modes.
class AcGameFlorr {
    constructor(root) {
        this.root = root;
        this.$florr = $(`
<div class="ac-game-florr">
    <canvas class="ac-game-florr-canvas" tabindex="0"></canvas>
    <button class="ac-game-florr-exit">退出 (ESC)</button>
    <div class="ac-game-florr-status"></div>
    <div class="ac-game-florr-help">鼠标/WASD 移动 · 左键或空格：展开花瓣攻击 · 右键或 Shift：收拢花瓣防御</div>
</div>
`);
        this.$florr.hide();
        this.root.$ac_game.append(this.$florr);

        this.$canvas = this.$florr.find('.ac-game-florr-canvas');
        this.canvas = this.$canvas[0];
        this.ctx = this.canvas.getContext('2d');
        this.$status = this.$florr.find('.ac-game-florr-status');
        this.$exit = this.$florr.find('.ac-game-florr-exit');

        this.VIEW_HEIGHT = 900;       // world units visible vertically, on every screen size
        this.running = false;
        this.reset_state();

        let outer = this;
        this.$exit.click(function () {
            outer.exit();
        });
    }

    reset_state() {
        this.ws = null;
        this.cfg = null;
        this.me_id = null;
        this.players = new Map();
        this.mobs = new Map();
        this.snap_time = 0;
        this.keys = new Set();
        this.mouse = {x: 0, y: 0, active: false};
        this.buttons = {left: false, right: false};
        this.last_sent = {dx: 0, dy: 0, m: 0, time: 0};
        this.raf = null;
        this.send_timer = null;
        this.last_frame = 0;
    }

    show() {
        if (this.running) return;
        this.running = true;
        this.reset_state();
        this.$florr.show();
        this.set_status("连接中…");
        this.resize();
        this.add_listening_events();
        this.connect();
        this.send_timer = setInterval(() => this.send_input(false), 50);
        this.last_frame = performance.now();
        this.raf = requestAnimationFrame((t) => this.frame(t));
        this.canvas.focus();
    }

    hide() {
        if (!this.running) return;
        this.running = false;
        $(window).off('.florr');
        if (this.send_timer) clearInterval(this.send_timer);
        if (this.raf) cancelAnimationFrame(this.raf);
        if (this.ws) {
            this.ws.onclose = null;
            this.ws.close();
        }
        this.reset_state();
        this.$florr.hide();
    }

    exit() {
        this.hide();
        this.root.menu.show();
    }

    set_status(text) {
        this.$status.text(text).toggle(!!text);
    }

    // ---- networking -----------------------------------------------------------
    connect() {
        let outer = this;
        let ws = new WebSocket(AC_WS_ORIGIN + "/wss/florr/");
        this.ws = ws;
        ws.onopen = function () {
            outer.set_status("");
        };
        ws.onmessage = function (e) {
            let data = JSON.parse(e.data);
            if (data.t === "welcome") {
                outer.cfg = data;
                outer.me_id = data.id;
            } else if (data.t === "s") {
                outer.apply_snapshot(data);
            }
        };
        ws.onclose = function (e) {
            if (!outer.running) return;
            if (e.code === 4401) outer.set_status("请先登录");
            else if (e.code === 4409) outer.set_status("该账号已在其他窗口进入，本窗口已断开");
            else outer.set_status("连接已断开，请退出后重新进入");
        };
    }

    apply_snapshot(s) {
        this.snap_time = performance.now();
        this.me_id = s.me;
        this.sync(this.players, s.ps);
        this.sync(this.mobs, s.ms);
    }

    // Keep a render-side copy per entity: `tx/ty` is the latest server position, `x/y` is what we draw
    sync(map, list) {
        let seen = new Set();
        for (let e of list) {
            seen.add(e.i);
            let cur = map.get(e.i);
            if (!cur) {
                cur = {x: e.x, y: e.y, r: e.r};
                map.set(e.i, cur);
            }
            cur.tx = e.x;
            cur.ty = e.y;
            cur.tr = e.r;
            cur.a = e.a;
            cur.mask = e.p;
            cur.hp = e.h;
            cur.max_hp = e.H;
            cur.name = e.n;
            cur.kind = e.t;
            cur.kills = e.k;
            cur.dead = e.d === 1;
        }
        for (let id of map.keys()) {
            if (!seen.has(id)) map.delete(id);
        }
    }

    compute_input() {
        let dx = 0, dy = 0;
        let k = this.keys;
        if (k.has('KeyW') || k.has('ArrowUp')) dy -= 1;
        if (k.has('KeyS') || k.has('ArrowDown')) dy += 1;
        if (k.has('KeyA') || k.has('ArrowLeft')) dx -= 1;
        if (k.has('KeyD') || k.has('ArrowRight')) dx += 1;
        if (dx !== 0 || dy !== 0) {
            let n = Math.hypot(dx, dy);
            dx /= n;
            dy /= n;
        } else if (this.mouse.active) {
            let vx = this.mouse.x - this.css_w / 2, vy = this.mouse.y - this.css_h / 2;
            let d = Math.hypot(vx, vy), dead_zone = 24;
            if (d > dead_zone) {
                let mag = Math.min(1, (d - dead_zone) / (0.2 * this.css_h));
                dx = vx / d * mag;
                dy = vy / d * mag;
            }
        }
        let m = 0;
        if (this.buttons.left || k.has('Space')) m = 1;
        else if (this.buttons.right || k.has('ShiftLeft') || k.has('ShiftRight')) m = -1;
        return {dx: Math.round(dx * 100) / 100, dy: Math.round(dy * 100) / 100, m: m};
    }

    send_input(force) {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return;
        let inp = this.compute_input(), last = this.last_sent, now = performance.now();
        let changed = inp.dx !== last.dx || inp.dy !== last.dy || inp.m !== last.m;
        if (!changed && !force && now - last.time < 500) return;
        this.ws.send(JSON.stringify({t: "in", dx: inp.dx, dy: inp.dy, m: inp.m}));
        this.last_sent = {dx: inp.dx, dy: inp.dy, m: inp.m, time: now};
    }

    request_respawn() {
        let me = this.players.get(this.me_id);
        if (me && me.dead && this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({t: "respawn"}));
        }
    }

    // ---- input events -----------------------------------------------------------
    add_listening_events() {
        let outer = this;
        this.$canvas.on('contextmenu', () => false);
        this.$canvas.on('mousemove', function (e) {
            let rect = outer.canvas.getBoundingClientRect();
            outer.mouse = {x: e.clientX - rect.left, y: e.clientY - rect.top, active: true};
        });
        this.$canvas.on('mousedown', function (e) {
            if (e.which === 1) outer.buttons.left = true;
            else if (e.which === 3) outer.buttons.right = true;
            outer.request_respawn();
            outer.canvas.focus();
            return false;
        });
        $(window).on('mouseup.florr', function (e) {
            if (e.which === 1) outer.buttons.left = false;
            else if (e.which === 3) outer.buttons.right = false;
        });
        $(window).on('keydown.florr', function (e) {
            let code = e.originalEvent.code;
            if (code === 'Escape') {
                outer.exit();
                return false;
            }
            outer.keys.add(code);
            if (code === 'Space') outer.request_respawn();
            if (['Space', 'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(code)) return false;
        });
        $(window).on('keyup.florr', function (e) {
            outer.keys.delete(e.originalEvent.code);
        });
        $(window).on('blur.florr', function () {
            outer.keys.clear();
            outer.buttons = {left: false, right: false};
        });
        $(window).on('resize.florr', function () {
            outer.resize();
        });
    }

    resize() {
        let dpr = window.devicePixelRatio || 1;
        this.css_w = this.$florr.width();
        this.css_h = this.$florr.height();
        this.canvas.width = Math.floor(this.css_w * dpr);
        this.canvas.height = Math.floor(this.css_h * dpr);
        this.dpr = dpr;
    }

    // ---- rendering ------------------------------------------------------------------
    frame(now) {
        if (!this.running) return;
        let dt = Math.min(0.1, (now - this.last_frame) / 1000);
        this.last_frame = now;
        this.smooth(dt);
        this.render(now);
        this.raf = requestAnimationFrame((t) => this.frame(t));
    }

    smooth(dt) {
        let k = 1 - Math.exp(-dt * 20);
        for (let p of this.players.values()) {
            p.x += (p.tx - p.x) * k;
            p.y += (p.ty - p.y) * k;
            p.r += (p.tr - p.r) * k;
        }
        for (let m of this.mobs.values()) {
            m.x += (m.tx - m.x) * k;
            m.y += (m.ty - m.y) * k;
        }
    }

    render(now) {
        let ctx = this.ctx, W = this.css_w, H = this.css_h;
        ctx.setTransform(this.dpr, 0, 0, this.dpr, 0, 0);
        ctx.fillStyle = '#15613a';
        ctx.fillRect(0, 0, W, H);

        let cfg = this.cfg, me = this.players.get(this.me_id);
        if (!cfg || !me) return;

        let scale = H / this.VIEW_HEIGHT;
        ctx.save();
        ctx.translate(W / 2, H / 2);
        ctx.scale(scale, scale);
        ctx.translate(-me.x, -me.y);

        this.draw_world(cfg, me, W / scale, H / scale);
        for (let m of this.mobs.values()) this.draw_mob(m);
        for (let p of this.players.values()) {
            if (p !== me && !p.dead) this.draw_player(p, now, false);
        }
        if (!me.dead) this.draw_player(me, now, true);
        ctx.restore();

        this.draw_hud(me);
    }

    draw_world(cfg, me, view_w, view_h) {
        let ctx = this.ctx;
        ctx.fillStyle = '#1ea761';
        ctx.fillRect(0, 0, cfg.w, cfg.h);

        ctx.strokeStyle = 'rgba(0, 0, 0, 0.10)';
        ctx.lineWidth = 2;
        let step = 100;
        let x0 = Math.max(0, Math.floor((me.x - view_w / 2) / step) * step);
        let x1 = Math.min(cfg.w, me.x + view_w / 2);
        let y0 = Math.max(0, Math.floor((me.y - view_h / 2) / step) * step);
        let y1 = Math.min(cfg.h, me.y + view_h / 2);
        ctx.beginPath();
        for (let x = x0; x <= x1; x += step) {
            ctx.moveTo(x, y0);
            ctx.lineTo(x, y1);
        }
        for (let y = y0; y <= y1; y += step) {
            ctx.moveTo(x0, y);
            ctx.lineTo(x1, y);
        }
        ctx.stroke();
    }

    draw_hp_bar(x, y, width, hp, max_hp) {
        if (hp >= max_hp) return;
        let ctx = this.ctx, h = 7;
        ctx.fillStyle = 'rgba(0, 0, 0, 0.45)';
        ctx.fillRect(x - width / 2, y, width, h);
        ctx.fillStyle = '#8be25a';
        ctx.fillRect(x - width / 2, y, width * Math.max(0, hp) / max_hp, h);
    }

    draw_eyes(x, y, radius) {
        let ctx = this.ctx;
        ctx.fillStyle = '#1a1a1a';
        for (let s of [-1, 1]) {
            ctx.beginPath();
            ctx.ellipse(x + s * radius * 0.34, y - radius * 0.12, radius * 0.12, radius * 0.2, 0, 0, Math.PI * 2);
            ctx.fill();
        }
    }

    draw_player(p, now, is_me) {
        let ctx = this.ctx, cfg = this.cfg, R = cfg.player_r;
        // petals first so the body sits on top of them
        let a0 = p.a + cfg.omega * (now - this.snap_time) / 1000;
        for (let i = 0; i < cfg.petal_n; i++) {
            if (!(p.mask & (1 << i))) continue;
            let a = a0 + i * 2 * Math.PI / cfg.petal_n;
            ctx.beginPath();
            ctx.arc(p.x + p.r * Math.cos(a), p.y + p.r * Math.sin(a), cfg.petal_r, 0, Math.PI * 2);
            ctx.fillStyle = '#ffffff';
            ctx.fill();
            ctx.lineWidth = 3;
            ctx.strokeStyle = '#cfcfcf';
            ctx.stroke();
        }
        ctx.beginPath();
        ctx.arc(p.x, p.y, R, 0, Math.PI * 2);
        ctx.fillStyle = is_me ? '#ffe763' : '#9bd3ff';
        ctx.fill();
        ctx.lineWidth = 4;
        ctx.strokeStyle = is_me ? '#cfbb50' : '#6fa3cc';
        ctx.stroke();
        this.draw_eyes(p.x, p.y, R);

        ctx.fillStyle = '#ffffff';
        ctx.strokeStyle = 'rgba(0, 0, 0, 0.6)';
        ctx.lineWidth = 4;
        ctx.font = 'bold 18px sans-serif';
        ctx.textAlign = 'center';
        ctx.strokeText(p.name, p.x, p.y - R - 14);
        ctx.fillText(p.name, p.x, p.y - R - 14);
        this.draw_hp_bar(p.x, p.y + R + 8, R * 2, p.hp, cfg.player_hp);
    }

    draw_mob(m) {
        let ctx = this.ctx, spec = this.cfg.mobs[m.kind];
        if (!spec) return;
        let R = spec.radius;
        ctx.beginPath();
        ctx.arc(m.x, m.y, R, 0, Math.PI * 2);
        ctx.fillStyle = '#8e5fb3';
        ctx.fill();
        ctx.lineWidth = 4;
        ctx.strokeStyle = '#6b3f8a';
        ctx.stroke();
        this.draw_eyes(m.x, m.y, R);
        this.draw_hp_bar(m.x, m.y + R + 8, R * 2, m.hp, m.max_hp);
    }

    draw_hud(me) {
        let ctx = this.ctx, W = this.css_w, H = this.css_h;
        ctx.textAlign = 'left';
        ctx.font = 'bold 20px sans-serif';
        ctx.fillStyle = '#ffffff';
        ctx.strokeStyle = 'rgba(0, 0, 0, 0.6)';
        ctx.lineWidth = 4;
        let text = "击杀 " + me.kills;
        ctx.strokeText(text, 16, 34);
        ctx.fillText(text, 16, 34);

        let bw = Math.min(360, W * 0.5), bh = 18, bx = (W - bw) / 2, by = H - 46;
        ctx.fillStyle = 'rgba(0, 0, 0, 0.45)';
        ctx.fillRect(bx, by, bw, bh);
        ctx.fillStyle = '#8be25a';
        ctx.fillRect(bx, by, bw * Math.max(0, me.hp) / this.cfg.player_hp, bh);

        if (me.dead) {
            ctx.fillStyle = 'rgba(0, 0, 0, 0.55)';
            ctx.fillRect(0, 0, W, H);
            ctx.textAlign = 'center';
            ctx.fillStyle = '#ffffff';
            ctx.font = 'bold 44px sans-serif';
            ctx.fillText("你被击败了", W / 2, H / 2 - 10);
            ctx.font = '22px sans-serif';
            ctx.fillText("点击或按空格重生", W / 2, H / 2 + 34);
        }
    }
}
