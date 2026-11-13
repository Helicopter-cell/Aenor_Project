(() => {
    const canvas = document.getElementById("home-voice-orb");
    const intro = canvas?.closest(".home-intro");
    if (!canvas || !intro) return;

    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
    const connection = navigator.connection;
    const isLowPower =
        (navigator.hardwareConcurrency && navigator.hardwareConcurrency < 4) ||
        (navigator.deviceMemory && navigator.deviceMemory <= 4) ||
        connection?.saveData ||
        ["slow-2g", "2g"].includes(connection?.effectiveType);
    const canRender =
        window.innerWidth >= 768 &&
        !reducedMotion.matches &&
        !isLowPower &&
        typeof window.WebGLRenderingContext !== "undefined";

    if (!canRender) return;

    let renderer;
    let animationFrame = 0;
    let observer;
    let lastFrameTime = 0;
    let destroyed = false;
    const pointer = { x: 0, y: 0 };
    const targetPointer = { x: 0, y: 0 };

    const initialize = (THREE) => {
        if (destroyed || reducedMotion.matches || window.innerWidth < 768 || !canvas.isConnected) return;
        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(34, 1, 0.1, 20);
        camera.position.z = 4.2;

        try {
            renderer = new THREE.WebGLRenderer({
                canvas,
                alpha: true,
                antialias: false,
                powerPreference: "low-power"
            });
        } catch (error) {
            console.warn("The Aënor 3D ornament could not initialize.", error);
            return;
        }

        const pixelRatio = Math.min(window.devicePixelRatio || 1, 1.5);
        renderer.setPixelRatio(pixelRatio);
        renderer.setClearColor(0x000000, 0);

        const orb = new THREE.Group();
        scene.add(orb);

        const coreMaterial = new THREE.MeshStandardMaterial({
            color: 0x2e5a44,
            emissive: 0x123524,
            emissiveIntensity: 0.85,
            metalness: 0.72,
            roughness: 0.28
        });
        const core = new THREE.Mesh(new THREE.IcosahedronGeometry(0.55, 2), coreMaterial);
        orb.add(core);

        const ringMaterial = new THREE.MeshStandardMaterial({
            color: 0xb3894e,
            emissive: 0x4a3319,
            emissiveIntensity: 0.6,
            metalness: 0.8,
            roughness: 0.34
        });
        const ring = new THREE.Mesh(new THREE.TorusGeometry(0.88, 0.012, 6, 96), ringMaterial);
        ring.rotation.set(0.85, 0.2, -0.3);
        orb.add(ring);

        const innerRing = new THREE.Mesh(
            new THREE.TorusGeometry(0.72, 0.006, 5, 80),
            new THREE.MeshBasicMaterial({ color: 0xe5c58b, transparent: true, opacity: 0.72 })
        );
        innerRing.rotation.set(-0.45, 0.7, 0.38);
        orb.add(innerRing);

        scene.add(new THREE.AmbientLight(0xfcfcfc, 1.1));
        const copperLight = new THREE.PointLight(0xb3894e, 3.2, 8);
        copperLight.position.set(1.6, 1.3, 2.2);
        scene.add(copperLight);
        const forestLight = new THREE.PointLight(0x2e5a44, 2.1, 7);
        forestLight.position.set(-1.5, -0.8, 1.4);
        scene.add(forestLight);

        const resize = () => {
            if (window.innerWidth < 768) {
                destroy();
                return;
            }
            const bounds = canvas.getBoundingClientRect();
            if (!bounds.width || !bounds.height) return;
            renderer.setSize(bounds.width, bounds.height, false);
            camera.aspect = bounds.width / bounds.height;
            camera.updateProjectionMatrix();
        };

        const onPointerMove = (event) => {
            const bounds = intro.getBoundingClientRect();
            targetPointer.x = ((event.clientX - bounds.left) / bounds.width - 0.5) * 0.45;
            targetPointer.y = ((event.clientY - bounds.top) / bounds.height - 0.5) * 0.3;
        };

        const render = (time) => {
            animationFrame = 0;
            if (destroyed || document.hidden || !renderer) return;
            if (time - lastFrameTime < 1000 / 60) {
                animationFrame = window.requestAnimationFrame(render);
                return;
            }

            const delta = Math.min((time - (lastFrameTime || time)) / 1000, 0.05);
            lastFrameTime = time;
            pointer.x += (targetPointer.x - pointer.x) * 0.035;
            pointer.y += (targetPointer.y - pointer.y) * 0.035;
            orb.rotation.y += delta * 0.16 + pointer.x * 0.003;
            orb.rotation.x += (pointer.y - orb.rotation.x) * 0.025;
            ring.rotation.z += delta * 0.035;
            renderer.render(scene, camera);
            animationFrame = window.requestAnimationFrame(render);
        };

        const start = () => {
            if (!animationFrame && !document.hidden && !destroyed) {
                lastFrameTime = 0;
                animationFrame = window.requestAnimationFrame(render);
            }
        };
        const pause = () => {
            if (animationFrame) window.cancelAnimationFrame(animationFrame);
            animationFrame = 0;
        };
        const destroy = () => {
            destroyed = true;
            pause();
            window.removeEventListener("resize", resize);
            intro.removeEventListener("pointermove", onPointerMove);
            document.removeEventListener("visibilitychange", onVisibilityChange);
            reducedMotion.removeEventListener("change", onMotionPreferenceChange);
            window.removeEventListener("pagehide", onPageHide);
            observer?.disconnect();
            scene.traverse((object) => {
                if (object.geometry) object.geometry.dispose();
                if (object.material) {
                    const materials = Array.isArray(object.material) ? object.material : [object.material];
                    materials.forEach((material) => material.dispose());
                }
            });
            renderer.dispose();
            renderer.forceContextLoss();
            renderer = undefined;
            canvas.hidden = true;
            canvas.classList.remove("is-ready");
        };
        const onVisibilityChange = () => (document.hidden ? pause() : start());
        const onMotionPreferenceChange = (event) => {
            if (event.matches) destroy();
        };
        const onPageHide = (event) => {
            if (event.persisted) {
                pause();
                return;
            }
            destroy();
        };

        canvas.hidden = false;
        resize();
        canvas.classList.add("is-ready");
        window.addEventListener("resize", resize, { passive: true });
        intro.addEventListener("pointermove", onPointerMove, { passive: true });
        document.addEventListener("visibilitychange", onVisibilityChange);
        reducedMotion.addEventListener("change", onMotionPreferenceChange);
        window.addEventListener("pagehide", onPageHide);

        observer = new IntersectionObserver(([entry]) => {
            if (entry.isIntersecting) start();
            else pause();
        });
        observer.observe(canvas);
    };

    import("https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js")
        .then(initialize)
        .catch((error) => console.warn("Three.js could not load; the page remains fully usable.", error));
})();
