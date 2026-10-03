let activeAudio = null;
let activeButton = null;
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

function resetActiveAudio(audio) {
    if (activeAudio !== audio) return;

    setButtonState(activeButton, 'idle');
    activeAudio = null;
    activeButton = null;
}

function showAudioError(button) {
    if (!button) return;

    button.classList.add('is-error');
    button.setAttribute('aria-label', 'Erreur de lecture audio');
    button.title = 'Audio indisponible. Vérifiez la configuration du service vocal.';
    const timer = window.setTimeout(() => {
        button.classList.remove('is-error');
        button.setAttribute('aria-label', 'Écouter la prononciation');
        button.title = 'Écouter la prononciation';
        buttonErrorTimers.delete(button);
    }, 4000);
    buttonErrorTimers.set(button, timer);
}

function speakAenor(text, ipaText, button = null) {
    if (activeAudio && activeButton === button) {
        const audioToStop = activeAudio;
        resetActiveAudio(audioToStop);
        audioToStop.pause();
        audioToStop.currentTime = 0;
        return;
    }

    if (activeAudio) {
        const previousAudio = activeAudio;
        resetActiveAudio(previousAudio);
        previousAudio.pause();
        previousAudio.currentTime = 0;
    }

    const parameters = new URLSearchParams({
        text: String(text || ''),
        ipa: String(ipaText || '').replace(/^\[|\]$/g, '').trim(),
    });
    const audio = new Audio(`/api/tts?${parameters.toString()}`);
    audio.preload = 'auto';
    activeAudio = audio;
    activeButton = button;
    setButtonState(button, 'loading');

    audio.onplaying = () => {
        if (activeAudio === audio) setButtonState(button, 'playing');
    };
    audio.onended = () => resetActiveAudio(audio);
    audio.onerror = () => {
        if (activeAudio !== audio) return;
        resetActiveAudio(audio);
        showAudioError(button);
        console.error('Erreur lors du chargement ou de la lecture de l’audio Aënor.');
    };

    try {
        const playPromise = audio.play();
        if (playPromise) {
            playPromise.catch(error => {
                if (activeAudio !== audio) return;
                resetActiveAudio(audio);
                showAudioError(button);
                if (error.name !== 'AbortError') {
                    console.error('Impossible de démarrer la lecture audio Aënor :', error);
                }
            });
        }
    } catch (error) {
        resetActiveAudio(audio);
        showAudioError(button);
        console.error('Impossible de démarrer la lecture audio Aënor :', error);
    }
}

window.speakAenor = speakAenor;

document.addEventListener('DOMContentLoaded', () => {
    document.addEventListener('click', event => {
        if (!(event.target instanceof Element)) return;
        const button = event.target.closest('.btn-tts');
        if (!button || button.disabled) return;

        speakAenor(button.dataset.text, button.dataset.ipa, button);
    });
});
