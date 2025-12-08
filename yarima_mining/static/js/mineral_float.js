document.addEventListener('DOMContentLoaded', function () {
  const minerals = [
    '/static/images/minerals/tin.png',
    '/static/images/minerals/columbite.png',
    '/static/images/minerals/gold.png',
  ];

  const container = document.querySelector('.background-minerals');

  if (!container) return;

  const numberOfMinerals = 3;  // Adjust as needed

  for (let i = 0; i < numberOfMinerals; i++) {
    const img = document.createElement('img');
    img.src = minerals[Math.floor(Math.random() * minerals.length)];
    img.classList.add('mineral');

    // Random starting position
    img.style.top = `${Math.random() * 100}vh`;
    img.style.left = `${Math.random() * 100}vw`;

    // Random animation duration and delay
    const duration = 10 + Math.random() * 10; // 10s to 20s
    const delay = Math.random() * 10; // 0s to 10s
    img.style.animationDuration = `${duration}s`;
    img.style.animationDelay = `${delay}s`;

    container.appendChild(img);
  }
});