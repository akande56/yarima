document.addEventListener('DOMContentLoaded', function () {
  const mineralImages = [
    '/static/images/minerals/tin.png',
    '/static/images/minerals/columbite.png',
    '/static/images/minerals/monazite.png'
  ];

  const container = document.getElementById('mineralFallContainer');
  if (!container) return;

  const stackHeight = {};  // Track stack height at positions
  const maxMinerals = 3;  // Limit total minerals in DOM
  let activeMinerals = [];

  function spawnMineral() {
    if (activeMinerals.length >= maxMinerals) {
      const oldest = activeMinerals.shift();
      container.removeChild(oldest);
    }

    const img = document.createElement('img');
    img.src = mineralImages[Math.floor(Math.random() * mineralImages.length)];
    img.classList.add('mineral-fall');

    const containerWidth = container.clientWidth;
    const leftPos = Math.floor(Math.random() * (containerWidth - 40));  // avoid overflow
    img.style.left = `${leftPos}px`;

    container.appendChild(img);
    activeMinerals.push(img);

    // After fall completes (6s), fix its bottom position for stacking
    setTimeout(() => {
      img.style.animation = 'none';
      img.style.top = 'auto';
      img.style.bottom = `${stackHeight[leftPos] || 0}px`;
      img.style.transform = `rotate(${Math.random() * 360}deg)`;

      stackHeight[leftPos] = (stackHeight[leftPos] || 0) + 40;
    }, 6000);
  }

  // Spawn new mineral every 1.5 seconds
  setInterval(spawnMineral, 1500);
});
