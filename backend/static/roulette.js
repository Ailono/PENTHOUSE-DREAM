const rouletteCanvas = document.getElementById('rouletteCanvas');
const rCtx = rouletteCanvas.getContext('2d');

const ROULETTE_NUMBERS = [0, 32, 15, 19, 4, 21, 2, 25, 17, 34, 6, 27, 13, 36, 11, 30, 8, 23, 10, 5, 24, 16, 33, 1, 20, 14, 31, 9, 22, 18, 29, 7, 28, 12, 35, 3, 26];

const REDS = new Set([1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]);

function getColor(num) {
  if (num === 0) return 'green';
  return REDS.has(num) ? 'red' : 'black';
}

const SECTOR = (2 * Math.PI) / 37;
const CX = 150, CY = 150, R = 130, INNER_R = 35;

let currentAngle = 0;
let spinning = false;
let spinStartAngle = 0;
let spinTargetAngle = 0;
let spinStartTime = 0;
const SPIN_DURATION = 5000;
let targetNumber = -1;
let onSpinComplete = null;

function drawRoulette(angle) {
  rCtx.clearRect(0, 0, 300, 300);

  rCtx.save();
  rCtx.beginPath();
  rCtx.arc(CX, CY, R + 5, 0, Math.PI * 2);
  rCtx.fillStyle = '#2c3e50';
  rCtx.fill();
  rCtx.closePath();

  for (let i = 0; i < 37; i++) {
    const a0 = i * SECTOR + angle;
    const a1 = (i + 1) * SECTOR + angle;

    rCtx.beginPath();
    rCtx.moveTo(CX, CY);
    rCtx.arc(CX, CY, R, a0, a1);
    rCtx.closePath();

    const num = ROULETTE_NUMBERS[i];
    rCtx.fillStyle = getColor(num);
    rCtx.fill();

    rCtx.strokeStyle = 'rgba(255,255,255,0.2)';
    rCtx.lineWidth = 0.5;
    rCtx.stroke();

    rCtx.save();
    rCtx.translate(CX, CY);
    rCtx.rotate(a0 + SECTOR / 2);
    rCtx.fillStyle = '#fff';
    rCtx.font = num === 0 ? 'bold 10px Arial' : '9px Arial';
    rCtx.textAlign = 'right';
    rCtx.fillText(num, R - 8, 3);
    rCtx.restore();
  }

  rCtx.beginPath();
  rCtx.arc(CX, CY, INNER_R, 0, Math.PI * 2);
  rCtx.fillStyle = '#1a1a2e';
  rCtx.fill();
  rCtx.strokeStyle = '#e94560';
  rCtx.lineWidth = 2;
  rCtx.stroke();
  rCtx.fillStyle = '#e94560';
  rCtx.font = 'bold 10px Arial';
  rCtx.textAlign = 'center';
  rCtx.textBaseline = 'middle';
  rCtx.fillText('PD', CX, CY);

  rCtx.fillStyle = '#ffd700';
  rCtx.beginPath();
  rCtx.moveTo(CX + R + 8, CY - 10);
  rCtx.lineTo(CX + R + 8, CY + 10);
  rCtx.lineTo(CX + R + 20, CY);
  rCtx.closePath();
  rCtx.fill();

  rCtx.restore();
}

function easeOutCubic(t) {
  return 1 - Math.pow(1 - t, 3);
}

function startSpin(targetNum, callback) {
  if (spinning) return;

  targetNumber = targetNum;
  onSpinComplete = callback;
  spinning = true;
  spinStartAngle = currentAngle;
  spinStartTime = performance.now();

  const numIndex = ROULETTE_NUMBERS.indexOf(targetNum);
  const targetSector = numIndex * SECTOR;
  const fullSpins = 5 + Math.floor(Math.random() * 3);
  const offset = (Math.random() - 0.5) * SECTOR * 0.6;
  spinTargetAngle = spinStartAngle + fullSpins * 2 * Math.PI + (2 * Math.PI - targetSector + offset);

  document.getElementById('rouletteResult').textContent = '🎰 Вращение...';
}

function updateSpin() {
  if (!spinning) return;

  const elapsed = performance.now() - spinStartTime;
  const t = Math.min(elapsed / SPIN_DURATION, 1);
  const eased = easeOutCubic(t);

  currentAngle = spinStartAngle + (spinTargetAngle - spinStartAngle) * eased;

  if (t >= 1) {
    spinning = false;
    currentAngle = spinTargetAngle % (2 * Math.PI);
    if (currentAngle < 0) currentAngle += 2 * Math.PI;

    const color = getColor(targetNumber);
    const colorEmoji = { red: '🔴', black: '⚫', green: '🟢' }[color] || '⚪';

    document.getElementById('rouletteResult').innerHTML =
      `🎰 ${targetNumber} ${colorEmoji}`;

    if (onSpinComplete) onSpinComplete(targetNumber, color);
    onSpinComplete = null;
  }
}

let rouletteInitialized = false;
let rouletteAnimId = null;
let rouletteLastTime = 0;

function rouletteLoop(timestamp) {
  if (!rouletteInitialized) return;
  const dt = Math.min((timestamp - rouletteLastTime) / 1000, 0.05);
  rouletteLastTime = timestamp;

  updateSpin();
  drawRoulette(currentAngle);

  rouletteAnimId = requestAnimationFrame(rouletteLoop);
}

function startRouletteUI() {
  if (rouletteInitialized) return;
  rouletteInitialized = true;

  drawRoulette(0);

  const controls = document.getElementById('rouletteControls');
  controls.innerHTML = '';

  const betTypes = [
    { label: 'Прямая (x36)', type: 'straight' },
    { label: 'Сплит (x18)', type: 'split' },
    { label: 'Стрит (x12)', type: 'street' },
    { label: 'Корнер (x9)', type: 'corner' },
    { label: 'Сикслайн (x6)', type: 'sixline' },
    { label: 'Соседи (x7)', type: 'neighbors' },
    { label: 'Красное (x2)', type: 'red', value: 'red' },
    { label: 'Чёрное (x2)', type: 'black', value: 'black' },
    { label: 'Чёт (x2)', type: 'even', value: 'even' },
    { label: 'Нечет (x2)', type: 'odd', value: 'odd' },
    { label: '1-18 (x2)', type: 'low', value: 'low' },
    { label: '19-36 (x2)', type: 'high', value: 'high' },
  ];

  betTypes.forEach(bt => {
    const btn = document.createElement('button');
    btn.className = 'bet';
    btn.textContent = bt.label;
    btn.addEventListener('click', () => {
      if (spinning) return;
      if (bt.type === 'straight') {
        const num = prompt('Введи число от 0 до 36:', '17');
        if (num === null) return;
        const n = parseInt(num);
        if (isNaN(n) || n < 0 || n > 36) { alert('Неверное число!'); return; }
        startSpin(n, (result) => { if (result === n) showNotification('🎉 Прямая ставка! x36'); });
      } else if (bt.type === 'split') {
        const input = prompt('Введи 2 числа через запятую (напр. 14,17):', '14,17');
        if (!input) return;
        const nums = input.split(',').map(s => parseInt(s.trim()));
        if (nums.length !== 2 || nums.some(n => isNaN(n) || n < 0 || n > 36)) { alert('Неверно!'); return; }
        const randomNum = ROULETTE_NUMBERS[Math.floor(Math.random() * 37)];
        startSpin(randomNum, (result) => { if (nums.includes(result)) showNotification('🎉 Сплит! x18'); });
      } else if (bt.type === 'street') {
        const start = parseInt(prompt('Введи начало ряда (1,4,7,10,13,16,19,22,25,28,31,34):', '1'));
        if (isNaN(start) || start < 1 || start > 34) { alert('Неверно!'); return; }
        const streetNums = [start, start + 1, start + 2];
        const randomNum = ROULETTE_NUMBERS[Math.floor(Math.random() * 37)];
        startSpin(randomNum, (result) => { if (streetNums.includes(result)) showNotification('🎉 Стрит! x12'); });
      } else if (bt.type === 'corner') {
        const input = prompt('Введи 4 числа (напр. 1,2,4,5):', '1,2,4,5');
        if (!input) return;
        const nums = input.split(',').map(s => parseInt(s.trim()));
        if (nums.length !== 4 || nums.some(n => isNaN(n) || n < 0 || n > 36)) { alert('Неверно!'); return; }
        const randomNum = ROULETTE_NUMBERS[Math.floor(Math.random() * 37)];
        startSpin(randomNum, (result) => { if (nums.includes(result)) showNotification('🎉 Корнер! x9'); });
      } else if (bt.type === 'sixline') {
        const start = parseInt(prompt('Введи начало (1,7,13,19,25,31):', '1'));
        if (isNaN(start) || ![1,7,13,19,25,31].includes(start)) { alert('Неверно!'); return; }
        const sixNums = [start, start+1, start+2, start+3, start+4, start+5];
        const randomNum = ROULETTE_NUMBERS[Math.floor(Math.random() * 37)];
        startSpin(randomNum, (result) => { if (sixNums.includes(result)) showNotification('🎉 Сикслайн! x6'); });
      } else if (bt.type === 'neighbors') {
        const center = parseInt(prompt('Введи центр (0-36):', '17'));
        if (isNaN(center) || center < 0 || center > 36) { alert('Неверно!'); return; }
        const idx = ROULETTE_NUMBERS.indexOf(center);
        const neighbors = [-2,-1,0,1,2].map(offset => ROULETTE_NUMBERS[(idx + offset + 37) % 37]);
        const randomNum = ROULETTE_NUMBERS[Math.floor(Math.random() * 37)];
        startSpin(randomNum, (result) => { if (neighbors.includes(result)) showNotification('🎉 Соседи! x7'); });
      } else {
        const randomNum = ROULETTE_NUMBERS[Math.floor(Math.random() * 37)];
        startSpin(randomNum, (result, color) => {
          let win = false;
          if (bt.type === 'red' && color === 'red') win = true;
          else if (bt.type === 'black' && color === 'black') win = true;
          else if (bt.type === 'even' && result !== 0 && result % 2 === 0) win = true;
          else if (bt.type === 'odd' && result % 2 === 1) win = true;
          else if (bt.type === 'low' && result >= 1 && result <= 18) win = true;
          else if (bt.type === 'high' && result >= 19 && result <= 36) win = true;
          if (win) showNotification('🎉 Выигрыш! x2');
        });
      }
    });
    controls.appendChild(btn);
  });

  const clearBtn = document.createElement('button');
  clearBtn.textContent = '🗑️ Очистить';
  clearBtn.addEventListener('click', () => {
    document.getElementById('rouletteResult').textContent = '';
  });
  controls.appendChild(clearBtn);

  rouletteLastTime = performance.now();
  rouletteAnimId = requestAnimationFrame(rouletteLoop);
}

window.startRouletteUI = startRouletteUI;
window.showRouletteResult = function(data) {
  if (data.number !== undefined) {
    startSpin(data.number, () => {});
  }
};
