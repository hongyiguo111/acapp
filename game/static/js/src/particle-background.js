// 粒子背景系统
class ParticleBackground {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.canvas = document.createElement('canvas');
        this.ctx = this.canvas.getContext('2d');

        // 设置canvas样式
        this.canvas.style.position = 'fixed';
        this.canvas.style.top = '0';
        this.canvas.style.left = '0';
        this.canvas.style.width = '100%';
        this.canvas.style.height = '100%';
        this.canvas.style.zIndex = '-1';
        this.canvas.style.pointerEvents = 'none';

        // 插入到容器开头
        this.container.insertBefore(this.canvas, this.container.firstChild);

        // 粒子配置
        this.config = {
            particleCount: 100,        // 粒子数量
            particleSize: 2,          // 粒子大小
            particleColor: 'rgba(59, 130, 246, 0.8)', // 粒子颜色 - 更深的蓝色
            lineColor: 'rgba(59, 130, 246, 0.3)',     // 连线颜色 - 更深的蓝色
            maxDistance: 150,         // 最大连线距离
            mouseRadius: 200,         // 鼠标影响半径
            mouseForce: 0.3,          // 鼠标作用力
            baseSpeed: 0.5,           // 基础速度
        };

        this.particles = [];
        this.mouse = { x: null, y: null };
        this.animationId = null;

        this.init();
    }

    init() {
        this.resize();
        this.createParticles();
        this.addEventListeners();
        this.animate();
    }

    resize() {
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
    }

    createParticles() {
        this.particles = [];
        for (let i = 0; i < this.config.particleCount; i++) {
            this.particles.push({
                x: Math.random() * this.canvas.width,
                y: Math.random() * this.canvas.height,
                vx: (Math.random() - 0.5) * this.config.baseSpeed,
                vy: (Math.random() - 0.5) * this.config.baseSpeed,
                originalVx: (Math.random() - 0.5) * this.config.baseSpeed,
                originalVy: (Math.random() - 0.5) * this.config.baseSpeed,
            });
        }
    }

    addEventListeners() {
        window.addEventListener('resize', () => {
            this.resize();
            this.createParticles();
        });

        window.addEventListener('mousemove', (e) => {
            this.mouse.x = e.clientX;
            this.mouse.y = e.clientY;
        });

        window.addEventListener('mouseleave', () => {
            this.mouse.x = null;
            this.mouse.y = null;
        });
    }

    updateParticles() {
        for (let particle of this.particles) {
            // 鼠标交互效果
            if (this.mouse.x !== null && this.mouse.y !== null) {
                const dx = particle.x - this.mouse.x;
                const dy = particle.y - this.mouse.y;
                const distance = Math.sqrt(dx * dx + dy * dy);

                if (distance < this.config.mouseRadius) {
                    const force = (this.config.mouseRadius - distance) / this.config.mouseRadius;
                    const directionX = dx / distance;
                    const directionY = dy / distance;

                    particle.vx += directionX * force * this.config.mouseForce;
                    particle.vy += directionY * force * this.config.mouseForce;
                }
            }

            // 速度衰减,回归原始速度
            particle.vx += (particle.originalVx - particle.vx) * 0.05;
            particle.vy += (particle.originalVy - particle.vy) * 0.05;

            // 更新位置
            particle.x += particle.vx;
            particle.y += particle.vy;

            // 边界检测
            if (particle.x < 0 || particle.x > this.canvas.width) {
                particle.vx *= -1;
                particle.originalVx *= -1;
                particle.x = Math.max(0, Math.min(this.canvas.width, particle.x));
            }
            if (particle.y < 0 || particle.y > this.canvas.height) {
                particle.vy *= -1;
                particle.originalVy *= -1;
                particle.y = Math.max(0, Math.min(this.canvas.height, particle.y));
            }
        }
    }

    drawParticles() {
        // 清空画布
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        // 绘制背景渐变 - 明亮白色到浅灰
        const gradient = this.ctx.createLinearGradient(0, 0, 0, this.canvas.height);
        gradient.addColorStop(0, 'rgba(248, 250, 252, 0.98)');   // 接近白色
        gradient.addColorStop(0.5, 'rgba(241, 245, 249, 0.98)'); // 浅灰白
        gradient.addColorStop(1, 'rgba(226, 232, 240, 0.98)');   // 浅灰
        this.ctx.fillStyle = gradient;
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

        // 绘制连线
        this.ctx.strokeStyle = this.config.lineColor;
        this.ctx.lineWidth = 1;

        for (let i = 0; i < this.particles.length; i++) {
            for (let j = i + 1; j < this.particles.length; j++) {
                const dx = this.particles[i].x - this.particles[j].x;
                const dy = this.particles[i].y - this.particles[j].y;
                const distance = Math.sqrt(dx * dx + dy * dy);

                if (distance < this.config.maxDistance) {
                    const opacity = (1 - distance / this.config.maxDistance) * 0.35; // 增加不透明度
                    this.ctx.strokeStyle = `rgba(59, 130, 246, ${opacity})`; // 使用深蓝色
                    this.ctx.beginPath();
                    this.ctx.moveTo(this.particles[i].x, this.particles[i].y);
                    this.ctx.lineTo(this.particles[j].x, this.particles[j].y);
                    this.ctx.stroke();
                }
            }
        }

        // 绘制粒子
        this.ctx.fillStyle = this.config.particleColor;
        for (let particle of this.particles) {
            this.ctx.beginPath();
            this.ctx.arc(particle.x, particle.y, this.config.particleSize, 0, Math.PI * 2);
            this.ctx.fill();

            // 添加发光效果
            const gradient = this.ctx.createRadialGradient(
                particle.x, particle.y, 0,
                particle.x, particle.y, this.config.particleSize * 3
            );
            gradient.addColorStop(0, 'rgba(59, 130, 246, 0.5)'); // 深蓝色发光
            gradient.addColorStop(1, 'rgba(59, 130, 246, 0)');
            this.ctx.fillStyle = gradient;
            this.ctx.beginPath();
            this.ctx.arc(particle.x, particle.y, this.config.particleSize * 3, 0, Math.PI * 2);
            this.ctx.fill();
        }
    }

    animate() {
        this.updateParticles();
        this.drawParticles();
        this.animationId = requestAnimationFrame(() => this.animate());
    }

    destroy() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
        }
        if (this.canvas && this.canvas.parentNode) {
            this.canvas.parentNode.removeChild(this.canvas);
        }
    }
}

// 导出
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ParticleBackground;
}