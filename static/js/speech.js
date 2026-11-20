(() => {
    const players = new Set();
    const playerByButton = new WeakMap();
    let activePlayer = null;

    function setButtonState(button, state, message = '') {
        button.classList.remove('is-loading', 'is-playing', 'is-paused', 'is-error');
        if (state !== 'idle' && state !== 'ready') {
            button.classList.add(`is-${state}`);
        }

        const labels = {
            idle: 'Écouter la prononciation',
            ready: 'Écouter la prononciation',
            loading: 'Annuler le chargement audio',
            playing: 'Mettre en pause la lecture',
            paused: 'Reprendre la lecture',
            error: 'Réessayer la lecture audio',
        };
        button.setAttribute('aria-label', labels[state]);
        button.setAttribute('aria-pressed', String(state === 'playing'));
        const title = state === 'error'
            ? message
            : state === 'loading'
                ? message || 'Chargement audio…'
                : state === 'ready' && message
                    ? message
                    : labels[state];
        button.title = title;
    }

    function setPlayerState(player, state, message = '') {
        player.status = state;
        player.wrapper.classList.remove(
            'is-loading',
            'is-playing',
            'is-paused',
            'is-ready',
            'is-error'
        );
        if (state !== 'idle') player.wrapper.classList.add(`is-${state}`);
        player.wrapper.setAttribute('aria-busy', String(state === 'loading'));
        setButtonState(player.button, state, message);
    }

    function destroyPlayer(player) {
        if (player.destroyed) return;
        player.destroyed = true;
        player.pendingPlay = false;
        player.controller.abort();
        player.unsubscribers.forEach(unsubscribe => unsubscribe());

        if (activePlayer === player) activePlayer = null;
        if (player.instance) {
            player.instance.destroy();
            player.instance = null;
        }

        player.wrapper.classList.remove(
            'has-waveform',
            'is-loading',
            'is-playing',
            'is-paused',
            'is-ready',
            'is-error'
        );
        player.wrapper.setAttribute('aria-busy', 'false');
        player.waveform.replaceChildren();
        setButtonState(player.button, 'idle');
        playerByButton.delete(player.button);
        players.delete(player);
    }

    async function diagnoseAudioFailure(player, error) {
        const detail = error instanceof Error ? error.message : String(error);

        try {
            const response = await fetch(player.sourceUrl, {
                method: 'GET',
                credentials: 'same-origin',
                cache: 'no-store',
                signal: player.controller.signal,
            });
            if (player.destroyed) return null;

            if (!response.ok) {
                if ((response.headers.get('Content-Type') || '').toLowerCase().includes('application/json')) {
                    try {
                        const errorBody = await response.json();
                        if (typeof errorBody.error === 'string' && errorBody.error) {
                            return errorBody.error;
                        }
                    } catch (parseError) {
                        console.error('Réponse JSON invalide de la route TTS :', parseError);
                    }
                }
                return `Le serveur TTS a répondu HTTP ${response.status}.`;
            }

            const contentType = response.headers.get('Content-Type') || '';
            if (!contentType.toLowerCase().startsWith('audio/mpeg')) {
                return `Type MIME audio inattendu : ${contentType || 'absent'}.`;
            }
            return `L’audio reçu n’a pas pu être lu : ${detail || 'format ou codec non pris en charge'}.`;
        } catch (diagnosticError) {
            if (player.destroyed || diagnosticError.name === 'AbortError') return null;
            return `Impossible de contacter la route TTS : ${diagnosticError.message || detail}.`;
        }
    }

    async function handleAudioError(player, error) {
        if (player.destroyed || player.handlingError) return;
        player.handlingError = true;

        const message = await diagnoseAudioFailure(player, error);
        if (player.destroyed || !message) return;

        console.error('Erreur de synthèse ou de lecture audio Aënor:', error);
        const { button, wrapper } = player;
        destroyPlayer(player);
        wrapper.classList.add('is-error');
        setButtonState(button, 'error', message);
    }

    function handlePlaybackError(player, error) {
        if (error && error.name === 'NotAllowedError' && !player.destroyed) {
            player.pendingPlay = false;
            setPlayerState(player, 'ready', 'Audio chargé. Cliquez pour commencer la lecture.');
            console.warn('Lecture audio bloquée par le navigateur : une nouvelle activation est nécessaire.');
            return;
        }
        void handleAudioError(player, error);
    }

    function pauseOtherPlayers(currentPlayer) {
        players.forEach(player => {
            if (player === currentPlayer) return;
            player.pendingPlay = false;
            if (player.instance && player.instance.isPlaying()) {
                player.instance.pause();
            }
        });
    }

    function startPlayback(player) {
        if (player.destroyed || !player.instance) return;
        pauseOtherPlayers(player);
        player.pendingPlay = false;

        try {
            const playPromise = player.instance.play();
            if (playPromise && typeof playPromise.catch === 'function') {
                playPromise.catch(error => handlePlaybackError(player, error));
            }
        } catch (error) {
            handlePlaybackError(player, error);
        }
    }

    function createPlayer(button) {
        if (!window.WaveSurfer || typeof window.WaveSurfer.create !== 'function') {
            const message = 'Le lecteur audio WaveSurfer n’a pas pu être chargé.';
            setButtonState(button, 'error', message);
            console.error(message);
            return null;
        }

        const wrapper = button.closest('.tts-player');
        const waveform = wrapper && wrapper.querySelector('.tts-waveform');
        if (!wrapper || !waveform) {
            const message = 'Le conteneur du lecteur audio est introuvable.';
            setButtonState(button, 'error', message);
            console.error(message);
            return null;
        }
        if (!button.dataset.text) {
            const message = 'Aucun texte n’est disponible pour la synthèse vocale.';
            setButtonState(button, 'error', message);
            console.error(message);
            return null;
        }

        const source = new URL('/api/tts', window.location.origin);
        source.search = new URLSearchParams({
            text: button.dataset.text,
            ipa: String(button.dataset.ipa || '').replace(/^\[|\]$/g, '').trim(),
        }).toString();

        const player = {
            button,
            wrapper,
            waveform,
            sourceUrl: source.toString(),
            controller: new AbortController(),
            instance: null,
            unsubscribers: [],
            pendingPlay: true,
            handlingError: false,
            destroyed: false,
            status: 'loading',
        };
        players.add(player);
        playerByButton.set(button, player);
        wrapper.classList.add('has-waveform');
        setPlayerState(player, 'loading');

        requestAnimationFrame(() => {
            if (player.destroyed) return;
            try {
                const instance = window.WaveSurfer.create({
                    container: waveform,
                    waveColor: '#2E5A44',
                    progressColor: '#B3894E',
                    cursorColor: '#B3894E',
                    cursorWidth: 1,
                    height: 24,
                    barWidth: 2,
                    barGap: 2,
                    barRadius: 2,
                    normalize: true,
                    dragToSeek: true,
                    hideScrollbar: true,
                });
                player.instance = instance;
                player.unsubscribers.push(
                    instance.on('loading', percent => {
                        if (!player.destroyed) {
                            setPlayerState(player, 'loading', `Chargement audio : ${percent} %`);
                        }
                    }),
                    instance.on('ready', () => {
                        if (player.destroyed) return;
                        setPlayerState(player, 'ready');
                        if (player.pendingPlay) startPlayback(player);
                    }),
                    instance.on('play', () => {
                        if (player.destroyed) return;
                        pauseOtherPlayers(player);
                        activePlayer = player;
                        setPlayerState(player, 'playing');
                    }),
                    instance.on('pause', () => {
                        if (player.destroyed) return;
                        if (activePlayer === player) activePlayer = null;
                        setPlayerState(player, 'paused');
                    }),
                    instance.on('finish', () => {
                        if (player.destroyed) return;
                        if (activePlayer === player) activePlayer = null;
                        player.instance.setTime(0);
                        setPlayerState(player, 'ready');
                    }),
                    instance.on('error', error => void handleAudioError(player, error))
                );

                const loadPromise = instance.load(player.sourceUrl);
                if (loadPromise && typeof loadPromise.catch === 'function') {
                    loadPromise.catch(error => void handleAudioError(player, error));
                }
            } catch (error) {
                void handleAudioError(player, error);
            }
        });

        return player;
    }

    function togglePlayback(button) {
        const player = playerByButton.get(button);
        if (!player) {
            createPlayer(button);
            return;
        }

        if (player.status === 'loading') {
            destroyPlayer(player);
            setButtonState(button, 'idle');
            return;
        }
        if (player.status === 'playing') {
            player.instance.pause();
            return;
        }

        startPlayback(player);
    }

    function destroyAllPlayers() {
        Array.from(players).forEach(destroyPlayer);
    }

    window.destroyAenorAudioPlayers = destroyAllPlayers;
    document.addEventListener('click', event => {
        if (!(event.target instanceof Element)) return;
        const button = event.target.closest('.btn-tts');
        if (button && !button.disabled) togglePlayback(button);
    });
    document.addEventListener('visibilitychange', () => {
        if (document.hidden && activePlayer && activePlayer.instance) {
            activePlayer.instance.pause();
        }
    });
    window.addEventListener('pagehide', destroyAllPlayers);
})();
