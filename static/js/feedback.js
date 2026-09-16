(() => {
  const cardsContainer = document.getElementById('feedback-cards');
  const emptyState = document.getElementById('feedback-empty');
  const filter = document.getElementById('feedback-filter');
  const sort = document.getElementById('feedback-sort');
  const modal = document.getElementById('feedback-modal');
  const deleteModal = document.getElementById('feedback-delete-modal');
  const deleteForm = document.getElementById('feedback-delete-form');
  const deleteError = document.getElementById('feedback-delete-error');
  let cardToDelete = null;

  const updateCount = (visibleCount) => {
    const count = document.querySelector('.feedback-count');
    count.textContent = `${visibleCount} retour${visibleCount === 1 ? '' : 's'}`;
  };

  const refreshCards = () => {
    const cards = [...cardsContainer.querySelectorAll('.feedback-card')];
    const target = filter.value;
    const sortMode = sort.value;
    const visibleCards = cards.filter((card) => target === 'all' || card.dataset.target === target);
    visibleCards.sort((left, right) => {
      if (sortMode === 'oldest') return left.dataset.createdAt.localeCompare(right.dataset.createdAt);
      if (sortMode === 'popular') return Number(right.dataset.likes) - Number(left.dataset.likes);
      if (sortMode === 'longest') return right.dataset.content.length - left.dataset.content.length;
      return right.dataset.createdAt.localeCompare(left.dataset.createdAt);
    });
    cards.forEach((card) => { card.hidden = !visibleCards.includes(card); });
    visibleCards.forEach((card) => cardsContainer.appendChild(card));
    emptyState.hidden = visibleCards.length > 0;
    updateCount(visibleCards.length);
  };

  const openCard = (card) => {
    const tag = card.querySelector('.feedback-tag');
    const date = card.querySelector('time');
    document.getElementById('feedback-modal-tag').textContent = tag.textContent;
    document.getElementById('feedback-modal-content').textContent = card.dataset.content;
    document.getElementById('feedback-modal-date').textContent = date.textContent;
    document.getElementById('feedback-modal-date').dateTime = date.dateTime;
    modal.showModal();
  };

  const bindCard = (card) => {
    card.addEventListener('click', (event) => {
      if (!event.target.closest('button')) openCard(card);
    });
    card.addEventListener('keydown', (event) => {
      if ((event.key === 'Enter' || event.key === ' ') && !event.target.closest('button')) {
        event.preventDefault();
        openCard(card);
      }
    });
    card.querySelector('.feedback-like').addEventListener('click', async (event) => {
      event.stopPropagation();
      const button = event.currentTarget;
      if (button.disabled) return;
      button.disabled = true;
      try {
        const response = await fetch(`/api/like_comment/${button.dataset.likeId}`, { method: 'POST' });
        const result = await response.json();
        if (!response.ok || !result.success) throw new Error('Like impossible');
        button.querySelector('b').textContent = result.likes_count;
        button.querySelector('span').textContent = '♥';
        card.dataset.likes = result.likes_count;
        refreshCards();
      } catch (error) {
        button.disabled = false;
      }
    });
    card.querySelector('.feedback-delete').addEventListener('click', (event) => {
      event.stopPropagation();
      cardToDelete = card;
      deleteError.hidden = true;
      deleteForm.reset();
      deleteModal.showModal();
      document.getElementById('admin-password').focus();
    });
  };

  cardsContainer.querySelectorAll('.feedback-card').forEach(bindCard);
  filter.addEventListener('change', refreshCards);
  sort.addEventListener('change', refreshCards);

  document.querySelector('.feedback-modal-close').addEventListener('click', () => modal.close());
  modal.addEventListener('click', (event) => { if (event.target === modal) modal.close(); });
  document.querySelector('[data-close-delete]').addEventListener('click', () => deleteModal.close());
  deleteModal.addEventListener('click', (event) => { if (event.target === deleteModal) deleteModal.close(); });

  deleteForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    const button = deleteForm.querySelector('button[type="submit"]');
    button.disabled = true;
    deleteError.hidden = true;
    try {
      const response = await fetch(`/api/delete_comment/${cardToDelete.dataset.commentId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password: new FormData(deleteForm).get('password') }),
      });
      const result = await response.json();
      if (!response.ok || !result.success) throw new Error(result.error || 'Suppression impossible');
      cardToDelete.remove();
      cardToDelete = null;
      deleteModal.close();
      refreshCards();
    } catch (error) {
      deleteError.textContent = error.message;
      deleteError.hidden = false;
    } finally {
      button.disabled = false;
    }
  });
})();
