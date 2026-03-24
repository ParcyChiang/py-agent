/**
 * Liquid Glass Effect - WebGL Background
 * Dark theme with mouse-interactive waves
 */

class LiquidGlass {
    constructor(container) {
        this.container = container;
        this.canvas = document.createElement('canvas');
        this.ctx = this.canvas.getContext('webgl') || this.canvas.getContext('experimental-webgl');
        this.container.appendChild(this.canvas);

        this.time = 0;
        this.mouse = { x: 0.5, y: 0.5, targetX: 0.5, targetY: 0.5 };
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
            this.mouse.targetX = (e.clientX - rect.left) / this.width;
            this.mouse.targetY = 1.0 - (e.clientY - rect.top) / this.height;
        });

        this.container.addEventListener('mouseleave', () => {
            this.mouse.targetX = 0.5;
            this.mouse.targetY = 0.5;
        });

        this.container.addEventListener('touchmove', (e) => {
            const rect = this.container.getBoundingClientRect();
            const touch = e.touches[0];
            this.mouse.targetX = (touch.clientX - rect.left) / this.width;
            this.mouse.targetY = 1.0 - (touch.clientY - rect.top) / this.height;
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

        // Fragment shader - Dark liquid glass with mouse interaction
        const fragmentShaderSrc = `
            precision mediump float;
            uniform float u_time;
            uniform vec2 u_resolution;
            uniform vec2 u_mouse;

            void main() {
                vec2 uv = gl_FragCoord.xy / u_resolution;
                vec2 mouse = u_mouse;

                // Distance from mouse
                float dist = distance(uv, mouse);
                float mouseInfluence = smoothstep(0.5, 0.0, dist);

                // Base dark gradient - deep blue/purple
                vec3 baseColor1 = vec3(0.05, 0.05, 0.15);  // Deep dark blue
                vec3 baseColor2 = vec3(0.08, 0.05, 0.12);  // Deep purple
                vec3 baseColor3 = vec3(0.03, 0.08, 0.15);  // Dark teal

                // Mix base gradient
                float gradientMix = uv.y * 0.5 + sin(uv.x * 3.14159 + u_time * 0.2) * 0.2;
                vec3 baseColor = mix(baseColor1, baseColor2, gradientMix);
                baseColor = mix(baseColor, baseColor3, sin(uv.x * 6.28318 + u_time * 0.15) * 0.3 + 0.3);

                // Subtle wave distortion
                float wave = 0.0;
                float amp = 0.015;
                float freq = 2.5;

                // Waves emanate from mouse position
                vec2 toMouse = uv - mouse;
                float angle = atan(toMouse.y, toMouse.x);

                for (float i = 1.0; i < 4.0; i++) {
                    float distFromMouse = length(toMouse) * 3.0;
                    wave += amp / i * sin(distFromMouse * freq * i - u_time * 2.0 + angle * i);
                }

                // Add subtle background waves
                float bgWave = 0.0;
                for (float i = 1.0; i < 3.0; i++) {
                    bgWave += 0.008 / i * sin((uv.x + uv.y) * freq * i + u_time * 0.5);
                }

                // Glass-like highlight near mouse
                float highlight = mouseInfluence * 0.15 * (0.5 + 0.5 * sin(u_time * 3.0));
                float ring = smoothstep(0.3, 0.28, dist) * smoothstep(0.2, 0.25, dist) * mouseInfluence;

                // Chromatic accent at mouse position
                vec3 accentColor = vec3(0.2, 0.4, 0.8);  // Subtle blue accent
                vec3 color = baseColor;
                color += vec3(wave * 0.5);
                color += vec3(bgWave * 0.3);
                color += accentColor * highlight;
                color += accentColor * ring * 0.3;

                // Vignette effect
                float vignette = 1.0 - smoothstep(0.3, 1.5, length(uv - 0.5) * 1.5);
                color *= vignette * 0.3 + 0.7;

                // Ensure minimum brightness for text readability
                color = max(color, vec3(0.08));

                gl_FragColor = vec4(color, 1.0);
            }
        `;

        try {
            const vertexShader = this.compileShader(gl.VERTEX_SHADER, vertexShaderSrc);
            const fragmentShader = this.compileShader(gl.FRAGMENT_SHADER, fragmentShaderSrc);

            if (!vertexShader || !fragmentShader) {
                this.fallbackRender();
                return;
            }

            const program = gl.createProgram();
            gl.attachShader(program, vertexShader);
            gl.attachShader(program, fragmentShader);
            gl.linkProgram(program);

            if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
                console.error('Program link error:', gl.getProgramInfoLog(program));
                this.fallbackRender();
                return;
            }

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

                // Smooth mouse movement
                this.mouse.x += (this.mouse.targetX - this.mouse.x) * 0.05;
                this.mouse.y += (this.mouse.targetY - this.mouse.y) * 0.05;

                gl.viewport(0, 0, this.width, this.height);
                gl.clearColor(0.05, 0.05, 0.1, 1);
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
        // Canvas 2D fallback - dark theme
        this.ctx = this.canvas.getContext('2d');
        const draw = () => {
            this.time += 0.008;

            // Smooth mouse
            this.mouse.x += (this.mouse.targetX - this.mouse.x) * 0.03;
            this.mouse.y += (this.mouse.targetY - this.mouse.y) * 0.03;

            // Dark gradient background
            const gradient = this.ctx.createRadialGradient(
                this.width * this.mouse.x,
                this.height * (1 - this.mouse.y),
                0,
                this.width / 2,
                this.height / 2,
                Math.max(this.width, this.height)
            );
            gradient.addColorStop(0, 'rgba(30, 40, 80, 1)');
            gradient.addColorStop(0.5, 'rgba(15, 20, 40, 1)');
            gradient.addColorStop(1, 'rgba(8, 10, 20, 1)');

            this.ctx.fillStyle = gradient;
            this.ctx.fillRect(0, 0, this.width, this.height);

            // Subtle wave circles around mouse
            for (let i = 0; i < 3; i++) {
                const phase = this.time * 2 + i * 2;
                const radius = 50 + i * 40 + Math.sin(phase) * 20;
                const x = this.width * this.mouse.x;
                const y = this.height * (1 - this.mouse.y);

                const waveGradient = this.ctx.createRadialGradient(x, y, radius - 10, x, y, radius + 10);
                waveGradient.addColorStop(0, 'rgba(100, 150, 255, 0)');
                waveGradient.addColorStop(0.5, `rgba(100, 150, 255, ${0.1 - i * 0.03})`);
                waveGradient.addColorStop(1, 'rgba(100, 150, 255, 0)');

                this.ctx.fillStyle = waveGradient;
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
