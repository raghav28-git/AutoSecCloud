/* --------------------------------------------------------------------------
   AutoSec Cloud - Landing Page Interactive Script & Canvas
   -------------------------------------------------------------------------- */

document.addEventListener("DOMContentLoaded", () => {
    // 1. Floating Header on Scroll
    const navbarWrapper = document.getElementById("navbarWrapper");
    if (navbarWrapper) {
        window.addEventListener("scroll", () => {
            if (window.scrollY > 40) {
                navbarWrapper.classList.add("scrolled");
            } else {
                navbarWrapper.classList.remove("scrolled");
            }
        });
    }

    // 2. Mobile Menu Toggle
    const mobileMenuBtn = document.getElementById("mobileMenuBtn");
    const mobileOverlay = document.getElementById("mobileOverlay");
    const closeMobileBtn = document.getElementById("closeMobileBtn");

    if (mobileMenuBtn && mobileOverlay) {
        mobileMenuBtn.addEventListener("click", () => {
            mobileOverlay.classList.add("active");
            document.body.style.overflow = "hidden";
        });
    }

    if (closeMobileBtn && mobileOverlay) {
        closeMobileBtn.addEventListener("click", () => {
            mobileOverlay.classList.remove("active");
            document.body.style.overflow = "auto";
        });
    }

    // 3. Rotating Keyword Reveal ("deploy", "secure", "comply", "scale")
    const rotatingWordEl = document.getElementById("rotatingWord");
    if (rotatingWordEl) {
        const keywords = ["deploy", "secure", "comply", "scale"];
        let currentIndex = 0;

        setInterval(() => {
            rotatingWordEl.classList.add("changing");

            setTimeout(() => {
                currentIndex = (currentIndex + 1) % keywords.length;
                rotatingWordEl.textContent = keywords[currentIndex];
                rotatingWordEl.classList.remove("changing");
            }, 400);
        }, 3000);
    }

    // 4. Metric Counter Reveal
    const metricValues = document.querySelectorAll(".metric-value[data-count]");
    if (metricValues.length > 0) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const el = entry.target;
                    const targetCount = parseInt(el.getAttribute("data-count"), 10);
                    const suffix = el.getAttribute("data-suffix") || "";
                    let currentCount = 0;
                    const duration = 1500;
                    const step = Math.max(1, Math.floor(targetCount / (duration / 16)));

                    const timer = setInterval(() => {
                        currentCount += step;
                        if (currentCount >= targetCount) {
                            currentCount = targetCount;
                            clearInterval(timer);
                        }
                        el.textContent = currentCount + suffix;
                    }, 16);

                    observer.unobserve(el);
                }
            });
        }, { threshold: 0.5 });

        metricValues.forEach(el => observer.observe(el));
    }
});

/* --------------------------------------------------------------------------
   Interactive Wireframe Canvas Visualizer (3D Rotating Geometric Mesh)
   -------------------------------------------------------------------------- */
(function initWireframeCanvas() {
    const canvas = document.getElementById("bgWireframeCanvas");
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    let width = canvas.width = window.innerWidth;
    let height = canvas.height = window.innerHeight;

    window.addEventListener("resize", () => {
        width = canvas.width = window.innerWidth;
        height = canvas.height = window.innerHeight;
    });

    // 3D Sphere Wireframe Vertices
    const nodes = [];
    const numNodes = 70;
    const radius = Math.min(width, height) * 0.35;

    for (let i = 0; i < numNodes; i++) {
        const theta = Math.acos(2 * Math.random() - 1);
        const phi = 2 * Math.PI * Math.random();

        nodes.push({
            x: radius * Math.sin(theta) * Math.cos(phi),
            y: radius * Math.sin(theta) * Math.sin(phi),
            z: radius * Math.cos(theta)
        });
    }

    let angleX = 0.002;
    let angleY = 0.003;

    function render3DFrame() {
        ctx.clearRect(0, 0, width, height);

        const centerX = width * 0.75;
        const centerY = height * 0.5;

        // Rotate nodes in 3D
        nodes.forEach(node => {
            // Rotate around Y
            const x1 = node.x * Math.cos(angleY) - node.z * Math.sin(angleY);
            const z1 = node.z * Math.cos(angleY) + node.x * Math.sin(angleY);
            
            // Rotate around X
            const y2 = node.y * Math.cos(angleX) - z1 * Math.sin(angleX);
            const z2 = z1 * Math.cos(angleX) + node.y * Math.sin(angleX);

            node.x = x1;
            node.y = y2;
            node.z = z2;
        });

        // Draw connecting wireframe lines
        for (let i = 0; i < nodes.length; i++) {
            for (let j = i + 1; j < nodes.length; j++) {
                const dx = nodes[i].x - nodes[j].x;
                const dy = nodes[i].y - nodes[j].y;
                const dz = nodes[i].z - nodes[j].z;
                const dist = Math.sqrt(dx * dx + dy * dy + dz * dz);

                if (dist < radius * 0.55) {
                    const alpha = (1 - dist / (radius * 0.55)) * 0.25;
                    ctx.beginPath();
                    ctx.strokeStyle = `rgba(240, 244, 248, ${alpha})`;
                    ctx.lineWidth = 0.6;
                    ctx.moveTo(centerX + nodes[i].x, centerY + nodes[i].y);
                    ctx.lineTo(centerX + nodes[j].x, centerY + nodes[j].y);
                    ctx.stroke();
                }
            }
        }

        // Draw nodes
        nodes.forEach(node => {
            const scale = (node.z + radius) / (2 * radius);
            const alpha = 0.2 + scale * 0.6;
            ctx.beginPath();
            ctx.arc(centerX + node.x, centerY + node.y, 1.5, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(240, 244, 248, ${alpha})`;
            ctx.fill();
        });

        requestAnimationFrame(render3DFrame);
    }

    render3DFrame();
})();
