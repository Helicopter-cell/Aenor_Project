(() => {
    let root;
    let entries = [];
    let deck = [];
    let roundIndex = 0;
    let score = 0;
    let currentEntry;
    let breathTimeout;

    const normalize = value => value
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '')
        .trim()
        .toLocaleLowerCase('fr');

    function shuffle(items) {
        const shuffled = [...items];
        for (let index = shuffled.length - 1; index > 0; index -= 1) {
            const swapIndex = Math.floor(Math.random() * (index + 1));
            [shuffled[index], shuffled[swapIndex]] = [shuffled[swapIndex], shuffled[index]];
        }
        return shuffled;
    }

    function setStatus(message, state = '') {
        const status = root.querySelector('[data-game-feedback]');
        status.textContent = message;
        status.classList.toggle('is-correct', state === 'correct');
        status.classList.toggle('is-incorrect', state === 'incorrect');
    }

    function updateScore() {
        root.querySelector('[data-game-score]').textContent = String(score);
    }

    function buildOptions(entry) {
        const answer = normalize(entry.french);
        const alternatives = [];
        const seen = new Set([answer]);

        for (const candidate of shuffle(entries)) {
            const key = normalize(candidate.french);
            if (!key || seen.has(key)) continue;
            seen.add(key);
            alternatives.push(candidate.french);
            if (alternatives.length === 2) break;
        }

        if (alternatives.length < 2) {
            throw new Error('Le lexique ne contient pas trois traductions distinctes pour le jeu.');
        }
        return shuffle([entry.french, ...alternatives]);
    }

    function showQuestion() {
        currentEntry = deck[roundIndex];
        root.querySelector('[data-game-round]').textContent = `Manche ${roundIndex + 1} / ${deck.length}`;
        root.querySelector('[data-game-progress]').value = roundIndex;
        root.querySelector('[data-game-total]').textContent = String(deck.length);
        root.querySelector('[data-game-glyph]').textContent = currentEntry.aenor;
        root.querySelector('[data-game-phonetic]').textContent = currentEntry.phonetic;

        const hintOutput = root.querySelector('[data-game-hint-output]');
        hintOutput.hidden = true;
        hintOutput.textContent = '';
        root.querySelectorAll('[data-game-hint]').forEach(button => {
            button.disabled = false;
            button.setAttribute('aria-expanded', 'false');
        });

        const choices = root.querySelector('[data-game-choices]');
        choices.replaceChildren();
        buildOptions(currentEntry).forEach(option => {
            const button = document.createElement('button');
            button.className = 'lexicographer-choice';
            button.type = 'button';
            button.dataset.answer = normalize(option);
            button.textContent = option;
            choices.appendChild(button);
        });

        root.querySelector('[data-game-next]').hidden = true;
        setStatus('');
    }

    function startGame() {
        const distinctAnswers = new Set(entries.map(entry => normalize(entry.french)).filter(Boolean));
        if (distinctAnswers.size < 3 || entries.length === 0) {
            setStatus('Le lexique ne contient pas assez de réponses distinctes pour ouvrir le jeu.');
            console.error('The lexicographer game requires at least three distinct lexicon translations.');
            return;
        }

        deck = shuffle(entries).slice(0, Math.min(10, entries.length));
        roundIndex = 0;
        score = 0;
        updateScore();
        root.querySelector('[data-game-question]').hidden = false;
        root.querySelector('[data-game-result]').hidden = true;
        showQuestion();
        window.AenorLenis?.resize?.();
    }

    function revealHint(button) {
        const output = root.querySelector('[data-game-hint-output]');
        const type = button.dataset.gameHint;
        const hint = type === 'category'
            ? `Cette entrée appartient à la catégorie « ${currentEntry.category} ».`
            : `Le mot français commence par « ${Array.from(currentEntry.french)[0]} ».`;

        output.textContent = hint;
        output.hidden = false;
        button.disabled = true;
        button.setAttribute('aria-expanded', 'true');
    }

    function answerQuestion(button) {
        const correct = button.dataset.answer === normalize(currentEntry.french);
        const choices = Array.from(root.querySelectorAll('.lexicographer-choice'));
        choices.forEach(choice => {
            choice.disabled = true;
            if (choice.dataset.answer === normalize(currentEntry.french)) {
                choice.classList.add('is-correct');
            }
        });

        if (correct) {
            score += 1;
            updateScore();
            setStatus('La voix est retrouvée. Le glyphe révèle son sens.', 'correct');
            const card = root.querySelector('[data-game-card]');
            card.classList.remove('ink-breath');
            window.requestAnimationFrame(() => card.classList.add('ink-breath'));
            window.clearTimeout(breathTimeout);
            breathTimeout = window.setTimeout(() => card.classList.remove('ink-breath'), 760);
        } else {
            button.classList.add('is-incorrect');
            setStatus(`Le mot était « ${currentEntry.french} ». Garde son écho pour la suite.`, 'incorrect');
        }

        root.querySelectorAll('[data-game-hint]').forEach(hint => {
            hint.disabled = true;
        });
        root.querySelector('[data-game-progress]').value = roundIndex + 1;
        const nextButton = root.querySelector('[data-game-next]');
        nextButton.innerHTML = roundIndex + 1 === deck.length
            ? 'Sceller la manche <span aria-hidden="true">→</span>'
            : 'Continuer <span aria-hidden="true">→</span>';
        nextButton.hidden = false;
        nextButton.focus();
    }

    function finishGame() {
        root.querySelector('[data-game-question]').hidden = true;
        const result = root.querySelector('[data-game-result]');
        const rank = root.querySelector('[data-game-rank]');
        const message = root.querySelector('[data-game-result-message]');

        if (score === deck.length) {
            rank.textContent = 'Maître des Voix';
            message.textContent = 'Aucune racine ne vous échappe. Le Cabinet garde désormais l’empreinte de votre écoute.';
        } else if (score >= Math.ceil(deck.length * 0.7)) {
            rank.textContent = 'Scribe des Racines';
            message.textContent = 'Les signes vous sont familiers. Quelques pages encore, et leurs voix deviendront les vôtres.';
        } else if (score >= Math.ceil(deck.length * 0.4)) {
            rank.textContent = 'Apprenti Scribe';
            message.textContent = 'Votre encre prend forme. Chaque détour dans le lexique affinera votre regard.';
        } else {
            rank.textContent = 'Gardien du Silence';
            message.textContent = 'Les mots se dérobent encore, mais leurs traces vous attendent dans les salles du lexique.';
        }

        root.querySelector('[data-game-result-score]').textContent = `${score} voix retrouvée${score === 1 ? '' : 's'} sur ${deck.length}`;
        result.hidden = false;
        rank.focus();
        window.AenorLenis?.resize?.();
    }

    function onClick(event) {
        const target = event.target instanceof Element ? event.target : null;
        if (!target) return;

        const choice = target.closest('.lexicographer-choice');
        if (choice && !choice.disabled) {
            answerQuestion(choice);
            return;
        }

        const hint = target.closest('[data-game-hint]');
        if (hint && !hint.disabled) {
            revealHint(hint);
            return;
        }

        if (target.closest('[data-game-next]')) {
            roundIndex += 1;
            if (roundIndex < deck.length) showQuestion();
            else finishGame();
            return;
        }

        if (target.closest('[data-game-restart]')) startGame();
    }

    function init() {
        const nextRoot = document.querySelector('[data-lexicographer-game]');
        if (!nextRoot || root === nextRoot) return;
        destroy();
        root = nextRoot;

        const data = document.getElementById('lexicographer-entries');
        try {
            entries = JSON.parse(data?.textContent || '[]').filter(entry => (
                typeof entry.french === 'string'
                && typeof entry.aenor === 'string'
                && typeof entry.phonetic === 'string'
                && typeof entry.category === 'string'
                && entry.french.trim()
                && entry.aenor.trim()
            ));
        } catch (error) {
            entries = [];
            setStatus('Le registre du lexique n’a pas pu être lu. Recharge la page pour réessayer.');
            console.error('Unable to parse lexicon entries for the game.', error);
            return;
        }

        root.addEventListener('click', onClick);
        try {
            startGame();
        } catch (error) {
            setStatus('La manche ne peut pas commencer avec les entrées actuelles du lexique.');
            console.error('Unable to start the lexicographer game.', error);
        }
    }

    function destroy() {
        if (root) root.removeEventListener('click', onClick);
        window.clearTimeout(breathTimeout);
        breathTimeout = undefined;
        root = undefined;
        entries = [];
        deck = [];
        currentEntry = undefined;
    }

    window.AenorLexicographerGame = { init, destroy };
    init();
})();
