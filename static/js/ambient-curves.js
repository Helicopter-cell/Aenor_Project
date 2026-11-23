(() => {
    const svg = document.querySelector('.ambient-curves');
    if (!svg) return;

    const curves = Array.from(svg.querySelectorAll('.ambient-curve'));
    const glyphs = Array.from(svg.querySelectorAll('.ambient-glyph'));
    const dustLayer = document.querySelector('.ambient-ink-dust');
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
    const profiles = [
        { row: 0.13, phase: 0.3, amplitude: 0.018, drift: 0.075 },
        { row: 0.31, phase: 2.2, amplitude: 0.026, drift: -0.055 },
        { row: 0.52, phase: 4.1, amplitude: 0.021, drift: 0.06 },
        { row: 0.73, phase: 1.4, amplitude: 0.029, drift: -0.07 },
        { row: 0.9, phase: 3.2, amplitude: 0.017, drift: 0.05 },
    ];
    const glyphProfiles = [
        { x: 0.08, y: 0.18, depth: 0.09, direction: 1, rotation: -8, turn: 4, phase: 0.4 },
        { x: 0.88, y: 0.2, depth: 0.12, direction: -1, rotation: 7, turn: -5, phase: 2.1 },
        { x: 0.2, y: 0.39, depth: 0.055, direction: 1, rotation: 12, turn: 3, phase: 3.5 },
        { x: 0.76, y: 0.44, depth: 0.1, direction: -1, rotation: -12, turn: 4, phase: 1.5 },
        { x: 0.13, y: 0.68, depth: 0.11, direction: 1, rotation: 6, turn: -4, phase: 4.7 },
        { x: 0.9, y: 0.7, depth: 0.07, direction: -1, rotation: -6, turn: 5, phase: 2.8 },
        { x: 0.36, y: 0.87, depth: 0.065, direction: 1, rotation: 10, turn: -3, phase: 5.3 },
        { x: 0.67, y: 0.91, depth: 0.1, direction: -1, rotation: -10, turn: 4, phase: 0.9 },
    ];

    function createDust() {
        if (!dustLayer) return [];

        let seed = 0xA3E0F;
        const random = () => {
            seed = (seed * 1664525 + 1013904223) >>> 0;
            return seed / 0x100000000;
        };

        return Array.from({ length: 30 }, () => {
            const element = document.createElement('span');
            const particle = {
                element,
                x: random() * 100,
                y: random() * 100,
                size: 1 + random() * 2,
                opacity: 0.06 + random() * 0.06,
                phase: random() * Math.PI * 2,
                frequency: 0.00022 + random() * 0.0005,
                amplitudeX: 2 + random() * 5,
                amplitudeY: 3 + random() * 7,
                depth: 0.004 + random() * 0.018,
                direction: random() < 0.5 ? -1 : 1,
                stretch: 0.15 + random() * 0.45,
            };

            element.className = `ambient-dust-particle${random() < 0.38 ? ' ambient-dust-particle--leaf' : ''}`;
            element.style.setProperty('--particle-size', `${particle.size.toFixed(1)}px`);
            element.style.setProperty('--particle-opacity', particle.opacity.toFixed(3));
            element.style.left = `${particle.x.toFixed(2)}%`;
            element.style.top = `${particle.y.toFixed(2)}%`;
            dustLayer.appendChild(element);
            return particle;
        });
    }

    const particles = createDust();

    let width = 0;
    let height = 0;
    let progress = 0;
    let targetProgress = 0;
    let activity = 0;
    let velocity = 0;
    let lastVelocityAt = 0;
    let lastLenisAt = 0;
    let lastNativeScroll = window.scrollY;
    let lastNativeAt = performance.now();
    let lastFrame = 0;
    let frame = 0;
    let initialized = false;

    const clamp = value => Math.min(1, Math.max(0, value));
    const format = value => value.toFixed(1);

    function resize() {
        width = window.innerWidth;
        height = window.innerHeight;
        svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
    }

    function draw(time) {
        const motion = reducedMotion.matches ? 0 : 1;
        const visualTime = time * motion;
        const visualProgress = progress * motion;
        const visualActivity = activity * motion;
        const direction = Math.sign(velocity);
        const signedActivity = direction * visualActivity;
        const scrollPhase = visualProgress * 3.2;

        curves.forEach((curve, index) => {
            const profile = profiles[index];
            const centerY = (profile.row + (visualProgress - 0.5) * profile.drift) * height;
            const amplitude = height * (profile.amplitude + visualActivity * 0.026);
            const phase = visualTime * 0.00011 + scrollPhase + profile.phase;
            const leftY = centerY + Math.sin(phase) * amplitude;
            const middleY = centerY + Math.sin(phase + 2.15) * amplitude
                + signedActivity * height * 0.018;
            const rightY = centerY + Math.sin(phase + 4.3) * amplitude
                - signedActivity * height * 0.018;
            const endY = centerY + Math.sin(phase + 6.45) * amplitude;
            const bend = amplitude * 0.8;

            curve.setAttribute('d', [
                `M ${format(-width * 0.08)} ${format(leftY)}`,
                `C ${format(width * 0.08)} ${format(leftY - bend)}`,
                `${format(width * 0.31)} ${format(middleY + bend)}`,
                `${format(width * 0.5)} ${format(middleY)}`,
                `C ${format(width * 0.69)} ${format(middleY - bend)}`,
                `${format(width * 0.91)} ${format(rightY + bend)}`,
                `${format(width * 1.08)} ${format(endY)}`,
            ].join(' '));
        });

        glyphs.forEach((glyph, index) => {
            const profile = glyphProfiles[index];
            const y = profile.y * height
                - visualProgress * height * profile.depth * profile.direction
                + Math.sin(visualTime * 0.00016 + profile.phase) * 4
                + signedActivity * 3;
            const rotation = profile.rotation
                + visualProgress * profile.turn
                + Math.sin(visualTime * 0.00013 + profile.phase) * 1.5
                + signedActivity * 2;
            glyph.style.transform = `translate3d(${format(profile.x * width)}px, ${format(y)}px, 0) rotate(${format(rotation)}deg)`;
        });

        particles.forEach(particle => {
            const phase = visualTime * particle.frequency + particle.phase;
            const x = Math.sin(phase) * particle.amplitudeX
                + direction * visualActivity * (4 + particle.depth * 140);
            const y = Math.cos(phase * 0.82) * particle.amplitudeY
                - visualProgress * height * particle.depth * particle.direction
                - direction * visualActivity * (3 + particle.depth * 80);
            const opacity = Math.min(
                0.16,
                particle.opacity + Math.max(0, Math.sin(phase)) * 0.02 + visualActivity * 0.025,
            );
            const stretch = 1 + visualActivity * particle.stretch;

            particle.element.style.transform = `translate3d(${format(x)}px, ${format(y)}px, 0) scaleY(${format(stretch)})`;
            particle.element.style.opacity = opacity.toFixed(3);
        });
    }

    function normalizeVelocity(value) {
        const magnitude = Math.abs(value);
        const normalized = magnitude < 20 ? magnitude / 3.5 : magnitude / 1800;
        return Math.min(1, normalized);
    }

    function onLenisScroll({ scroll, limit, progress: lenisProgress, velocity: lenisVelocity }) {
        targetProgress = Number.isFinite(lenisProgress)
            ? clamp(lenisProgress)
            : limit > 0 ? clamp(scroll / limit) : 0;
        velocity = Number.isFinite(lenisVelocity) ? lenisVelocity : 0;
        lastVelocityAt = performance.now();
        lastLenisAt = lastVelocityAt;
    }

    function onNativeScroll() {
        const now = performance.now();
        if (now - lastLenisAt < 140) return;

        const scroll = window.scrollY;
        const elapsed = Math.max(16, now - lastNativeAt);
        const limit = Math.max(0, document.documentElement.scrollHeight - window.innerHeight);
        targetProgress = limit > 0 ? clamp(scroll / limit) : 0;
        velocity = ((scroll - lastNativeScroll) / elapsed) * 1000;
        lastNativeScroll = scroll;
        lastNativeAt = now;
        lastVelocityAt = now;

        if (reducedMotion.matches) {
            progress = targetProgress;
            activity = 0;
            draw(now);
        }
    }

    function refresh() {
        resize();
        const limit = Math.max(0, document.documentElement.scrollHeight - window.innerHeight);
        targetProgress = limit > 0 ? clamp(window.scrollY / limit) : 0;
        lastNativeScroll = window.scrollY;
        lastNativeAt = performance.now();
        lastLenisAt = 0;
        velocity = 0;

        if (!initialized) {
            progress = targetProgress;
            initialized = true;
        }
        draw(performance.now());
        start();
    }

    function animate(time) {
        frame = 0;
        if (document.hidden || reducedMotion.matches) return;

        const delta = lastFrame ? Math.min(64, time - lastFrame) : 16;
        lastFrame = time;
        const progressEase = 1 - Math.exp(-delta / 180);
        const activityEase = 1 - Math.exp(-delta / 120);
        const velocityAge = Math.max(0, time - lastVelocityAt);
        const targetActivity = normalizeVelocity(velocity) * Math.exp(-velocityAge / 260);

        progress += (targetProgress - progress) * progressEase;
        activity += (targetActivity - activity) * activityEase;
        draw(time);
        frame = window.requestAnimationFrame(animate);
    }

    function start() {
        if (frame || document.hidden || reducedMotion.matches) return;
        lastFrame = 0;
        frame = window.requestAnimationFrame(animate);
    }

    function stop() {
        if (!frame) return;
        window.cancelAnimationFrame(frame);
        frame = 0;
        lastFrame = 0;
    }

    function onMotionPreferenceChange() {
        if (reducedMotion.matches) {
            stop();
            progress = targetProgress;
            activity = 0;
            draw(performance.now());
        } else {
            start();
        }
    }

    function onVisibilityChange() {
        if (document.hidden) {
            stop();
        } else {
            refresh();
        }
    }

    window.addEventListener('scroll', onNativeScroll, { passive: true });
    window.addEventListener('resize', refresh, { passive: true });
    window.addEventListener('pagehide', stop);
    window.addEventListener('pageshow', refresh);
    document.addEventListener('visibilitychange', onVisibilityChange);
    reducedMotion.addEventListener('change', onMotionPreferenceChange);

    window.AenorAmbientCurves = {
        onLenisScroll,
        refresh,
    };

    refresh();
})();
