const AENOR_SPEECH_LANGUAGE = 'fr-FR';
const AENOR_SPEECH_VOICE_NAME = '';
const AENOR_SPEECH_RATE = 0.85;
const AENOR_SPEECH_PITCH = 1.0;

let activeUtterance = null;
let activeButton = null;

function speechSynthesisAvailable() {
    return 'speechSynthesis' in window && 'SpeechSynthesisUtterance' in window;
}

function setButtonSpeaking(button, isSpeaking) {
    if (!button) return;

    button.classList.toggle('is-speaking', isSpeaking);
    button.setAttribute('aria-pressed', String(isSpeaking));
    button.setAttribute(
        'aria-label',
        isSpeaking ? 'Arrêter la lecture' : 'Écouter la prononciation'
    );
    button.title = isSpeaking ? 'Arrêter la lecture' : 'Écouter la prononciation';
}

function resetActiveSpeech(utterance) {
    if (utterance && activeUtterance !== utterance) return;

    setButtonSpeaking(activeButton, false);
    activeUtterance = null;
    activeButton = null;
}

function selectSpeechVoice() {
    const voices = window.speechSynthesis.getVoices();
    if (AENOR_SPEECH_VOICE_NAME) {
        const preferredVoice = voices.find(voice => voice.name === AENOR_SPEECH_VOICE_NAME);
        if (preferredVoice) return preferredVoice;
    }

    return voices.find(voice => voice.lang.toLowerCase().startsWith('fr')) || voices[0] || null;
}

function speakAenor(text, ipaText, button = null) {
    if (!speechSynthesisAvailable()) {
        if (button) {
            button.disabled = true;
            button.title = 'La synthèse vocale n’est pas prise en charge par ce navigateur';
        }
        return;
    }

    if (activeButton === button && activeUtterance) {
        resetActiveSpeech(activeUtterance);
        window.speechSynthesis.cancel();
        return;
    }

    if (activeUtterance) {
        resetActiveSpeech(activeUtterance);
        window.speechSynthesis.cancel();
    }

    const pronunciation = String(ipaText || text || '').replace(/[\[\]]/g, '').trim();
    if (!pronunciation) return;

    const utterance = new SpeechSynthesisUtterance(pronunciation);
    utterance.lang = AENOR_SPEECH_LANGUAGE;
    utterance.rate = AENOR_SPEECH_RATE;
    utterance.pitch = AENOR_SPEECH_PITCH;

    const voice = selectSpeechVoice();
    if (voice) utterance.voice = voice;

    activeUtterance = utterance;
    activeButton = button;
    setButtonSpeaking(button, true);

    utterance.onend = () => resetActiveSpeech(utterance);
    utterance.onerror = event => {
        resetActiveSpeech(utterance);
        if (event.error !== 'canceled' && event.error !== 'interrupted') {
            console.error('Erreur de synthèse vocale Aënor :', event.error);
        }
    };

    try {
        window.speechSynthesis.speak(utterance);
    } catch (error) {
        resetActiveSpeech(utterance);
        console.error('Impossible de démarrer la synthèse vocale Aënor :', error);
    }
}

window.speakAenor = speakAenor;

document.addEventListener('DOMContentLoaded', () => {
    if (!speechSynthesisAvailable()) {
        document.querySelectorAll('.btn-tts').forEach(button => {
            button.disabled = true;
            button.title = 'La synthèse vocale n’est pas prise en charge par ce navigateur';
        });
    }

    document.addEventListener('click', event => {
        if (!(event.target instanceof Element)) return;
        const button = event.target.closest('.btn-tts');
        if (!button || button.disabled) return;

        speakAenor(button.dataset.text, button.dataset.ipa, button);
    });
});
