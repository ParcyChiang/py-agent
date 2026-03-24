/**
 * Liquid Glass Effect - WebGL Background
 * Based on react-bits LiquidChrome effect
 */

class LiquidGlass {
    constructor(container) {
        this.container = container;
        this.canvas = document.createElement('canvas');
        this.ctx = this.canvas.getContext('webgl') || this.canvas.getContext('experimental-webgl');
        this.container.appendChild(this.canvas);

        this.time = 0;
        this.mouse = { x: 0, y: 0 };
        this.animationId = null;

        this.resize();
        this.initEvents();
        this.render();
    }

    resize() {
        this.width = this.canvas.width = this.container.offsetWidth;
        this.height = this.canvas.height = this.container.offsetHeight;
    }

    initEvents() {
        window.addEventListener('resize', () => this.resize());

        this.container.addEventListener('mousemove', (e) => {
            const rect = this.container.getBoundingClientRect();
            this.mouse.x = (e.clientX - rect.left) / this.width;
            this.mouse.y = 1.0 - (e.clientY - rect.top) / this.height;
        });

        this.container.addEventListener('touchmove', (e) => {
            const rect = this.container.getBoundingClientRect();
            const touch = e.touches[0];
            this.mouse.x = (touch.clientX - rect.left) / this.width;
            this.mouse.y = 1.0 - (touch.clientY - rect.top) / this.height;
        });
    }

    render() {
        const gl = this.ctx;
        if (!gl) {
            this.fallbackRender();
            return;
        }

        // Vertex shader
        const vertexShaderSrc = `
            attribute vec2 a_position;
            void main() {
                gl_Position = vec4(a_position, 0.0, 1.0);
            }
        `;

        // Fragment shader - Liquid Chrome effect
        const fragmentShaderSrc = `
            precision mediump float;
            uniform float u_time;
            uniform vec2 u_resolution;
            uniform vec2 u_mouse;

            void main() {
                vec2 uv = gl_FragCoord.xy / u_resolution;

                float amp = 0.03;
                float freq = 3.0;

                // Mouse influence
                vec2 mouse = u_mouse * 3.14159;

                // Distortion waves
                for (float i = 1.0; i < 8.0; i++) {
                    uv.x += amp / i * cos(i * freq * uv.y + u_time + mouse.x);
                    uv.y += amp / i * cos(i * freq * uv.x + u_time + mouse.y);
                }

                // Color calculation
                vec3 baseColor = vec3(0.1, 0.2, 0.4);
                vec3 color = baseColor / abs(sin(u_time - uv.y - uv.x));

                // Add chromatic aberration
                float r = color.r + 0.1 * sin(u_time * 0.5 + uv.x * 3.0);
                float g = color.g + 0.05 * sin(u_time * 0.7 + uv.y * 3.0);
                float b = color.b + 0.08 * sin(u_time * 0.3 + (uv.x + uv.y) * 2.0);

                // Add glass-like highlight
                float highlight = 0.3 + 0.2 * sin(uv.x * 10.0 + u_time);
                color += vec3(highlight * 0.1);

                gl_FragColor = vec4(color, 0.85);
            }
        `;

        try {
            const vertexShader = this.compileShader(gl.VERTEX_SHADER, vertexShaderSrc);
            const fragmentShader = this.compileShader(gl.FRAGMENT_SHADER, fragmentShaderSrc);

            const program = gl.createProgram();
            gl.attachShader(program, vertexShader);
            gl.attachShader(program, fragmentShader);
            gl.linkProgram(program);
            gl.useProgram(program);

            const positionBuffer = gl.createBuffer();
            gl.bindBuffer(gl.ARRAY_BUFFER, positionBuffer);
            gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([
                -1, -1, 1, -1, -1, 1,
                -1, 1, 1, -1, 1, 1
            ]), gl.STATIC_DRAW);

            const positionLocation = gl.getAttribLocation(program, 'a_position');
            gl.enableVertexAttribArray(positionLocation);
            gl.vertexAttribPointer(positionLocation, 2, gl.FLOAT, false, 0, 0);

            const timeLocation = gl.getUniformLocation(program, 'u_time');
            const resolutionLocation = gl.getUniformLocation(program, 'u_resolution');
            const mouseLocation = gl.getUniformLocation(program, 'u_mouse');

            const startTime = Date.now();

            const draw = () => {
                this.time = (Date.now() - startTime) * 0.001;

                gl.viewport(0, 0, this.width, this.height);
                gl.clearColor(0, 0, 0, 1);
                gl.clear(gl.COLOR_BUFFER_BIT);

                gl.uniform1f(timeLocation, this.time);
                gl.uniform2f(resolutionLocation, this.width, this.height);
                gl.uniform2f(mouseLocation, this.mouse.x, this.mouse.y);

                gl.drawArrays(gl.TRIANGLES, 0, 6);

                this.animationId = requestAnimationFrame(draw);
            };

            draw();
        } catch (e) {
            console.warn('WebGL failed, using fallback', e);
            this.fallbackRender();
        }
    }

    compileShader(type, source) {
        const gl = this.ctx;
        const shader = gl.createShader(type);
        gl.shaderSource(shader, source);
        gl.compileShader(shader);

        if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
            console.error('Shader compile error:', gl.getShaderInfoLog(shader));
            gl.deleteShader(shader);
            return null;
        }
        return shader;
    }

    fallbackRender() {
        // Canvas 2D fallback
        this.ctx = this.canvas.getContext('2d');
        const draw = () => {
            this.time += 0.016;

            const gradient = this.ctx.createLinearGradient(0, 0, this.width, this.height);
            const hue1 = (this.time * 20) % 360;
            const hue2 = (hue1 + 60) % 360;

            gradient.addColorStop(0, `hsla(${hue1}, 70%, 20%, 0.85)`);
            gradient.addColorStop(0.5, `hsla(${hue2}, 60%, 30%, 0.85)`);
            gradient.addColorStop(1, `hsla(${hue1}, 70%, 25%, 0.85)`);

            this.ctx.fillStyle = gradient;
            this.ctx.fillRect(0, 0, this.width, this.height);

            // Add noise pattern
            for (let i = 0; i < 50; i++) {
                const x = (Math.sin(this.time + i) * 0.5 + 0.5) * this.width;
                const y = (Math.cos(this.time * 0.7 + i * 2) * 0.5 + 0.5) * this.height;
                const radius = 20 + Math.sin(this.time + i) * 10;

                const radialGradient = this.ctx.createRadialGradient(x, y, 0, x, y, radius);
                radialGradient.addColorStop(0, 'rgba(255, 255, 255, 0.15)');
                radialGradient.addColorStop(1, 'rgba(255, 255, 255, 0)');

                this.ctx.fillStyle = radialGradient;
                this.ctx.beginPath();
                this.ctx.arc(x, y, radius, 0, Math.PI * 2);
                this.ctx.fill();
            }

            this.animationId = requestAnimationFrame(draw);
        };
        draw();
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

// Auto-initialize liquid glass backgrounds
document.addEventListener('DOMContentLoaded', () => {
    // Create liquid glass background for body
    const bgContainer = document.createElement('div');
    bgContainer.id = 'liquid-glass-bg';
    bgContainer.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        z-index: -1;
        overflow: hidden;
    `;
    document.body.insertBefore(bgContainer, document.body.firstChild);

    // Initialize liquid glass effect
    new LiquidGlass(bgContainer);

    // Add glass-morphism to existing cards
    document.querySelectorAll('.card, .stats-card, .report-card, .chart-card, .metric-card, .code-container').forEach(el => {
        el.classList.add('glass-effect');
    });

    // Add glass buttons to nav links
    document.querySelectorAll('.nav a, .btn').forEach(el => {
        el.classList.add('glass-button');
    });
});

// Export for manual initialization
window.LiquidGlass = LiquidGlass;
