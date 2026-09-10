async function sendPrompt() {
    const prompt = (document.getElementById("prompt-fr") || document.getElementById("prompt-ae"))?.value || "";
    const responseDiv = document.getElementById("response");

    if (!prompt.trim()) {
        alert("Veuillez saisir une phrase.");
        return;
    }

    responseDiv.innerHTML = '<span class="loading">Traduction en cours :</span>';

    try {
        const direction = document.querySelector('input[name="direction"]:checked')?.value || 'fr2aenor';
        const response = await fetch('/traduire', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ texte: prompt, direction: direction })
        });

        const data = await response.json();

        if (!response.ok || !data.success) {
            throw new Error(data.erreur || 'Erreur inconnue');
        }

        responseDiv.textContent = data.traduction || 'Aucune réponse reçue.';
        responseDiv.classList.remove('result-aenor', 'result-fr');
        if (direction === 'aenor2fr') {
            responseDiv.classList.add('result-fr');
        } else {
            responseDiv.classList.add('result-aenor');
        }
    } catch (error) {
        console.error(error);
        responseDiv.textContent = 'Erreur lors de la traduction : ' + error.message;
        responseDiv.classList.remove('result-aenor', 'result-fr');
    }
}

document.addEventListener("DOMContentLoaded", () => {
    // 1. Récupérer tous les boutons radio de direction
    const directionRadios = document.querySelectorAll('input[name="direction"]');
    
    // 2. Récupérer le champ de saisie (on utilise une requête qui ne dépend pas de l'ID puisqu'il va changer)
    const textInput = document.querySelector('.form-wrapper input[type="text"]');

    // 3. Ajouter un écouteur d'événement sur chaque bouton radio
    directionRadios.forEach(radio => {
        radio.addEventListener('change', (event) => {
            if (event.target.value === 'fr2aenor') {
                // Si Français → Aënor
                textInput.id = 'prompt-fr';
                textInput.placeholder = "Écrivez votre phrase à traduire ici...";
                // Optionnel : tu peux même changer la classe si besoin
                textInput.classList.replace('result-aenor', 'result-fr'); 
            } else if (event.target.value === 'aenor2fr') {
                // Si Aënor → Français
                textInput.id = 'prompt-ae';
                textInput.placeholder = "Écrivez votre phrase à traduire ici...";
                // Optionnel : adapter la police/classe pour l'Aënor
                textInput.classList.replace('result-fr', 'result-aenor'); 
            }
        });
    });
});