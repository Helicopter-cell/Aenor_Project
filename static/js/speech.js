let activePlayback = null;
const buttonErrorTimers = new WeakMap();

function setButtonState(button, state) {
    if (!button) return;

    const existingTimer = buttonErrorTimers.get(button);
    if (existingTimer) {
        window.clearTimeout(existingTimer);
        buttonErrorTimers.delete(button);
    }

    button.classList.remove('is-loading', 'is-playing', 'is-error');
    if (state !== 'idle') button.classList.add(`is-${state}`);
    button.setAttribute('aria-pressed', String(state !== 'idle'));
    button.setAttribute(
        'aria-label',
        state === 'idle'
            ? 'Écouter la prononciation'
            : state === 'loading'
                ? 'Annuler le chargement audio'
                : 'Arrêter la lecture'
    );
    button.title = state === 'loading'
        ? 'Chargement audio…'
        : state === 'playing'
            ? 'Arrêter la lecture'
            : 'Écouter la prononciation';
}

function showAudioError(button, message) {
    if (!button) return;

    button.classList.add('is-error');
    button.setAttribute('aria-label', 'Erreur de lecture audio');
    button.title = message || 'Audio indisponible. Vérifiez la configuration du service vocal.';
    const timer = window.setTimeout(() => {
        button.classList.remove('is-error');
        button.setAttribute('aria-label', 'Écouter la prononciation');
        button.title = 'Écouter la prononciation';
        buttonErrorTimers.delete(button);
    }, 5000);
    buttonErrorTimers.set(button, timer);
}

function releasePlayback(playback) {
    if (playback.audio) {
        playback.audio.onplaying = null;
        playback.audio.onended = null;
        playback.audio.onerror = null;
        playback.audio.pause();
        playback.audio.removeAttribute('src');
        playback.audio.load();
    }
}

function stopPlayback(playback) {
    if (activePlayback !== playback) return;

    activePlayback = null;
    setButtonState(playback.button, 'idle');
    playback.controller.abort();
    releasePlayback(playback);
}

function finishPlayback(playback, error = null) {
    if (activePlayback !== playback) return;

    activePlayback = null;
    setButtonState(playback.button, 'idle');
    releasePlayback(playback);

    if (error) {
        showAudioError(playback.button, error.message);
        console.error('Erreur de synthèse ou de lecture audio Aënor:', error);
    }
}

async function diagnoseAudioFailure(playback, sourceUrl, mediaError) {
    if (playback.diagnosing) return;
    playback.diagnosing = true;

    let message = mediaError
        ? `Le navigateur n’a pas pu lire l’audio (code ${mediaError.code}).`
        : 'Le navigateur n’a pas pu lire l’audio renvoyé.';

    try {
        const response = await fetch(sourceUrl, {
            method: 'GET',
            credentials: 'same-origin',
            cache: 'no-store',
            signal: playback.controller.signal,
        });
        if (activePlayback !== playback) return;

        const contentType = response.headers.get('Content-Type') || '';
        if (!response.ok) {
            let detail = '';
            try {
                const errorBody = await response.json();
                detail = errorBody.error || '';
            } catch {
                detail = '';
            }
            message = detail || `Le serveur TTS a répondu HTTP ${response.status}.`;
        } else if (!contentType.toLowerCase().startsWith('audio/mpeg')) {
            message = `Type MIME audio inattendu : ${contentType || 'absent'}.`;
        } else {
            message = `L’audio reçu n’a pas pu être décodé (code ${mediaError ? mediaError.code : 'inconnu'}).`;
        }
    } catch (error) {
        if (error.name === 'AbortError' || activePlayback !== playback) return;
        message = `Impossible de contacter la route TTS : ${error.message}`;
    }

    finishPlayback(playback, new Error(message));
}

function speakAenor(text, ipaText, button = null) {
    if (activePlayback && activePlayback.button === button) {
        stopPlayback(activePlayback);
        return;
    }
    if (activePlayback) stopPlayback(activePlayback);

    const parameters = new URLSearchParams({
        text: String(text || ''),
        ipa: String(ipaText || '').replace(/^\[|\]$/g, '').trim(),
    });
    const sourceUrl = `/api/tts?${parameters.toString()}`;
    const playback = {
        button,
        controller: new AbortController(),
        audio: null,
        diagnosing: false,
    };
    playback.audio = new Audio(sourceUrl);
    playback.audio.preload = 'auto';
    activePlayback = playback;
    setButtonState(button, 'loading');

    playback.audio.onplaying = () => {
        if (activePlayback === playback) setButtonState(button, 'playing');
    };
    playback.audio.onended = () => finishPlayback(playback);
    playback.audio.onerror = () => {
        if (activePlayback !== playback) return;
        void diagnoseAudioFailure(playback, sourceUrl, playback.audio.error);
    };

    try {
        const playPromise = playback.audio.play();
        if (playPromise) {
            playPromise.catch(error => {
                if (activePlayback !== playback) return;
                if (error.name === 'NotSupportedError') {
                    void diagnoseAudioFailure(playback, sourceUrl, playback.audio.error);
                    return;
                }
                finishPlayback(playback, error);
            });
        }
    } catch (error) {
        finishPlayback(playback, error);
    }
}

window.speakAenor = speakAenor;

document.addEventListener('DOMContentLoaded', () => {
    document.addEventListener('click', event => {
        if (!(event.target instanceof Element)) return;
        const button = event.target.closest('.btn-tts');
        if (!button || button.disabled) return;

        void speakAenor(button.dataset.text, button.dataset.ipa, button);
    });
});
