class ParticleEffect {
    constructor() {
        this.canvas = null;
        this.ctx = null;
        this.particles = [];
        this.mouse = { x: null, y: null, radius: 150 };
        this.init();
    }

    init() {
        // 创建canvas
        this.canvas = document.createElement('canvas');
        this.canvas.id = 'particles-canvas';
        this.ctx = this.canvas.getContext('2d');

        // 设置canvas尺寸
        this.resizeCanvas();

        // 创建粒子
        this.createParticles();

        // 绑定事件
        this.bindEvents();

        // 开始动画
        this.animate();
    }

    resizeCanvas() {
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
    }

    createParticles() {
        const numberOfParticles = 100;
        this.particles = [];

        for (let i = 0; i < numberOfParticles; i++) {
            const x = Math.random() * this.canvas.width;
            const y = Math.random() * this.canvas.height;
            const size = Math.random() * 3 + 1;
            const speedX = (Math.random() - 0.5) * 0.5;
            const speedY = (Math.random() - 0.5) * 0.5;

            this.particles.push({
                x, y, size, speedX, speedY,
                originalX: x,
                originalY: y
            });
        }
    }

    bindEvents() {
        window.addEventListener('resize', () => {
            this.resizeCanvas();
            this.createParticles();
        });

        window.addEventListener('mousemove', (e) => {
            this.mouse.x = e.x;
            this.mouse.y = e.y;
        });

        window.addEventListener('mouseout', () => {
            this.mouse.x = null;
            this.mouse.y = null;
        });
    }

    drawParticles() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        for (let i = 0; i < this.particles.length; i++) {
            const particle = this.particles[i];

            // 绘制粒子
            this.ctx.fillStyle = 'rgba(100, 200, 255, 0.8)';
            this.ctx.beginPath();
            this.ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
            this.ctx.fill();

            // 绘制连线
            for (let j = i + 1; j < this.particles.length; j++) {
                const particle2 = this.particles[j];
                const dx = particle.x - particle2.x;
                const dy = particle.y - particle2.y;
                const distance = Math.sqrt(dx * dx + dy * dy);

                if (distance < 120) {
                    this.ctx.strokeStyle = `rgba(100, 200, 255, ${1 - distance / 120})`;
                    this.ctx.lineWidth = 0.5;
                    this.ctx.beginPath();
                    this.ctx.moveTo(particle.x, particle.y);
                    this.ctx.lineTo(particle2.x, particle2.y);
                    this.ctx.stroke();
                }
            }
        }
    }

    updateParticles() {
        for (let particle of this.particles) {
            // 基础移动
            particle.x += particle.speedX;
            particle.y += particle.speedY;

            // 边界检测
            if (particle.x < 0 || particle.x > this.canvas.width) {
                particle.speedX *= -1;
            }
            if (particle.y < 0 || particle.y > this.canvas.height) {
                particle.speedY *= -1;
            }

            // 鼠标交互
            if (this.mouse.x !== null && this.mouse.y !== null) {
                const dx = this.mouse.x - particle.x;
                const dy = this.mouse.y - particle.y;
                const distance = Math.sqrt(dx * dx + dy * dy);

                if (distance < this.mouse.radius) {
                    const force = (this.mouse.radius - distance) / this.mouse.radius;
                    const forceDirectionX = dx / distance;
                    const forceDirectionY = dy / distance;

                    particle.x -= forceDirectionX * force * 5;
                    particle.y -= forceDirectionY * force * 5;
                }
            }
        }
    }

    animate() {
        this.drawParticles();
        this.updateParticles();
        requestAnimationFrame(() => this.animate());
    }

    getCanvas() {
        return this.canvas;
    }
}
