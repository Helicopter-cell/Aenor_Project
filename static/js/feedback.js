(() => {
  const modal = document.getElementById('feedback-modal');
  const modalContent = document.getElementById('feedback-modal-content');
  const modalTag = document.getElementById('feedback-modal-tag');
  const modalDate = document.getElementById('feedback-modal-date');

  document.querySelectorAll('.feedback-card').forEach((card) => {
    const openCard = () => {
      const tag = card.querySelector('.feedback-tag');
      const date = card.querySelector('time');
      modalTag.textContent = tag.textContent;
      modalContent.textContent = card.dataset.content;
      modalDate.textContent = date.textContent;
      modalDate.dateTime = date.dateTime;
      card.setAttribute('aria-expanded', 'true');
      modal.showModal();
    };
    card.addEventListener('click', (event) => {
      if (!event.target.closest('.feedback-like')) openCard();
    });
    card.addEventListener('keydown', (event) => {
      if ((event.key === 'Enter' || event.key === ' ') && !event.target.closest('.feedback-like')) {
        event.preventDefault();
        openCard();
      }
    });
  });

  document.querySelector('.feedback-modal-close').addEventListener('click', () => modal.close());
  modal.addEventListener('click', (event) => {
    if (event.target === modal) modal.close();
  });

  document.querySelectorAll('.feedback-like').forEach((button) => {
    button.addEventListener('click', async (event) => {
      event.stopPropagation();
      if (button.disabled) return;
      button.disabled = true;
      try {
        const response = await fetch(`/api/like_comment/${button.dataset.likeId}`, { method: 'POST' });
        const result = await response.json();
        if (!response.ok || !result.success) throw new Error('Like impossible');
        button.querySelector('b').textContent = result.likes_count;
        button.querySelector('span').textContent = '♥';
      } catch (error) {
        button.disabled = false;
      }
    });
  });
})();