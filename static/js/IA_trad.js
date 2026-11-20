(() => {
window.AenorTranslator?.destroy();

let activeTranslationRequest;
window.AenorTranslator = {
    destroy() {
        activeTranslationRequest?.abort();
        activeTranslationRequest = undefined;
    },
};

async function sendPrompt() {
    const prompt = (document.getElementById("prompt-fr") || document.getElementById("prompt-ae"))?.value || "";
    const responseDiv = document.getElementById("response");

    if (!prompt.trim()) {
        alert("Veuillez saisir une phrase.");
        return;
    }

    responseDiv.innerHTML = '<span class="loading">Traduction en cours :</span>';
    activeTranslationRequest?.abort();
    const requestController = new AbortController();
    activeTranslationRequest = requestController;

    try {
        const direction = document.querySelector('input[name="direction"]:checked')?.value || 'fr2aenor';
        const autoriserApprentissage = document.getElementById('autoriser-apprentissage')?.checked || false;
        const traductionFiable = document.getElementById('traduction-fiable')?.checked || false;
        const csrfToken = document.querySelector('#swup')?.dataset.csrfToken
            || document.querySelector('meta[name="csrf-token"]')?.content;
        const response = await fetch('/traduire', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            signal: requestController.signal,
            body: JSON.stringify({
                texte: prompt,
                direction: direction,
                autoriser_apprentissage: autoriserApprentissage,
                traduction_fiable: traductionFiable
            })
        });

        const data = await response.json();

        if (!response.ok || !data.success) {
            throw new Error(data.erreur || 'Erreur inconnue');
        }

        const translationText = data.traduction || 'Aucune réponse reçue.';
        const resultContent = document.createElement('div');
        resultContent.className = 'translation-result';
        const translatedText = document.createElement('span');
        translatedText.className = 'translation-text';
        translatedText.textContent = translationText;
        resultContent.appendChild(translatedText);

        if (direction === 'fr2aenor' && data.traduction) {
            const speakPlayer = document.getElementById('tts-button-template').content.firstElementChild.cloneNode(true);
            const speakButton = speakPlayer.querySelector('.btn-tts');
            speakButton.dataset.ipa = data.phonetic || '';
            speakButton.dataset.text = data.traduction;
            resultContent.appendChild(speakPlayer);
        }
        responseDiv.replaceChildren(resultContent);
        if (autoriserApprentissage && data.commentaire) {
            const commentaire = document.createElement('div');
            commentaire.className = 'learning-comment';
            commentaire.textContent = data.commentaire;
            responseDiv.appendChild(commentaire);
        }
        responseDiv.classList.remove('result-aenor', 'result-fr');
        if (direction === 'aenor2fr') {
            responseDiv.classList.add('result-fr');
        } else {
            responseDiv.classList.add('result-aenor');
        }
    } catch (error) {
        if (error.name === 'AbortError') return;
        console.error(error);
        responseDiv.textContent = 'Erreur lors de la traduction : ' + error.message;
        responseDiv.classList.remove('result-aenor', 'result-fr');
    } finally {
        if (activeTranslationRequest === requestController) {
            activeTranslationRequest = undefined;
        }
    }
}
window.sendPrompt = sendPrompt;

(() => {
    const directionRadios = document.querySelectorAll('input[name="direction"]');
    const textInput = document.querySelector('.form-wrapper input[type="text"]');
    const textInputLabel = document.querySelector('.translator-form label[for="prompt-fr"]');
    if (!textInput || !textInputLabel) return;

    directionRadios.forEach(radio => {
        radio.addEventListener('change', (event) => {
            if (event.target.value === 'fr2aenor') {
                textInput.id = 'prompt-fr';
                textInputLabel.htmlFor = 'prompt-fr';
                textInput.placeholder = "Écrivez votre phrase à traduire ici...";
                textInput.classList.replace('result-aenor', 'result-fr');
            } else if (event.target.value === 'aenor2fr') {
                textInput.id = 'prompt-ae';
                textInputLabel.htmlFor = 'prompt-ae';
                textInput.placeholder = "Écrivez votre phrase à traduire ici...";
                textInput.classList.replace('result-fr', 'result-aenor');
            }
        });
    });
})();
})();