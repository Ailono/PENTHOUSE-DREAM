const API = 'http://localhost:8000';
const WS_URL = 'ws://localhost:8000/ws';

let state = {
  userId: 1,
  balance: 0,
  roomLevel: 1,
  happiness: 50,
  inventory: [],
  shopItems: [],
};

let ws = null;

function $(id) { return document.getElementById(id); }

function setStatus(text) {
  $('statusText').textContent = text;
}

function showNotification(text, duration = 3000) {
  const area = $('notificationArea');
  const el = document.createElement('div');
  el.className = 'notification';
  el.textContent = text;
  area.appendChild(el);
  setTimeout(() => el.remove(), duration);
}

async function apiGet(path) {
  const res = await fetch(API + path);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

async function apiPost(path, body = {}) {
  const params = new URLSearchParams(body);
  const res = await fetch(API + path + '?' + params, { method: 'POST' });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

function connectWebSocket() {
  if (ws) ws.close();
  ws = new WebSocket(WS_URL + '/' + state.userId);

  ws.onopen = () => {
    $('connectionStatus').textContent = '● Подключено';
    $('connectionStatus').style.color = '#4ecca3';
    setStatus('WebSocket подключён');
  };

  ws.onclose = () => {
    $('connectionStatus').textContent = '○ Отключено';
    $('connectionStatus').style.color = '#e94560';
    setStatus('WebSocket отключён, переподключение...');
    setTimeout(connectWebSocket, 3000);
  };

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    handleWsEvent(data);
  };

  ws.onerror = () => {
    $('connectionStatus').textContent = '✕ Ошибка';
    $('connectionStatus').style.color = '#e94560';
  };
}

function handleWsEvent(data) {
  switch (data.type) {
    case 'balance_changed':
      state.balance = data.balance;
      updateUI();
      showNotification(`💰 Баланс: ${data.balance} монет`);
      break;
    case 'roulette_result':
      if (typeof window.showRouletteResult === 'function') {
        window.showRouletteResult(data);
      }
      if (data.win) {
        showNotification(`🎉 Выигрыш: +${data.payout} 🪙`);
      }
      state.balance = data.balance;
      updateUI();
      break;
    case 'room_update':
      setStatus('Комната обновлена');
      break;
  }
}

async function loadUserData() {
  try {
    const user = await apiGet('/api/users/' + state.userId);
    state.balance = user.balance || 0;
    state.roomLevel = user.room_level || 1;
    state.happiness = user.happiness || 50;
  } catch {
    await apiPost('/api/users/', { user_id: state.userId });
  }
}

async function loadInventory() {
  try {
    state.inventory = await apiGet('/api/users/' + state.userId + '/inventory');
  } catch {
    state.inventory = [];
  }
}

async function loadShop() {
  try {
    state.shopItems = await apiGet('/api/shop');
  } catch {
    state.shopItems = [];
  }
}

function updateUI() {
  $('balanceDisplay').textContent = state.balance.toLocaleString();
  $('roomLevelDisplay').textContent = state.roomLevel;
  $('happinessDisplay').textContent = state.happiness;
  renderInventory();
  renderShop();
}

function renderInventory() {
  const grid = $('inventoryGrid');
  if (!grid) return;

  if (!state.inventory.length) {
    grid.innerHTML = '<p style="color:#888;font-size:13px;">Инвентарь пуст</p>';
    return;
  }

  const emojiMap = {
    chair: '🪑', table: '🪑', lamp: '💡', carpet: '🟫', painting: '🖼️',
    aquarium: '🪸', fireplace: '🔥', sofa: '🛋️', bookshelf: '📚', plant: '🌿',
    floor_lamp: '💡', coffee_table: '🪑', mirror: '🪞', clock: '🕐', fountain: '⛲',
  };

  grid.innerHTML = state.inventory.map(item => {
    const emoji = emojiMap[item.item_id] || '📦';
    const rarityClass = item.rarity || 'common';
    const equipped = item.equipped ? 'equipped' : '';
    return `<div class="inv-slot ${equipped}" title="${item.name} (${item.rarity})">
      <span class="badge ${rarityClass}">${emoji}</span>
    </div>`;
  }).join('');
}

function renderShop() {
  const container = $('shopItems');
  if (!container) return;

  if (!state.shopItems.length) {
    container.innerHTML = '<p style="color:#888;font-size:13px;">Магазин пуст. Загляни в Telegram-бот!</p>';
    return;
  }

  const rarityColors = { common: '#4ecca3', uncommon: '#3498db', rare: '#9b59b6', legendary: '#e67e22' };

  container.innerHTML = state.shopItems.map(item => `
    <div style="display:flex;justify-content:space-between;align-items:center;padding:8px;background:#0f3460;border-radius:6px;margin-bottom:6px;">
      <span>
        <span style="color:${rarityColors[item.rarity] || '#aaa'};font-weight:bold;">${item.name}</span>
        <span class="badge ${item.rarity}">${item.rarity}</span>
        ${item.is_hot ? '<span style="color:#e94560;">🔥</span>' : ''}
      </span>
      <span>${item.price} 🪙 (ост. ${item.stock})</span>
    </div>
  `).join('');
}

document.querySelectorAll('.sidebar button[data-view]').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.sidebar button').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    const view = btn.dataset.view;
    document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
    const panel = $(view + 'Panel');
    if (panel) panel.classList.add('active');
    if (view === 'roulette' && typeof window.startRouletteUI === 'function') {
      window.startRouletteUI();
    }
  });
});

$('refreshBtn').addEventListener('click', async () => {
  setStatus('Загрузка...');
  await Promise.all([loadUserData(), loadInventory(), loadShop()]);
  updateUI();
  setStatus('Обновлено');
  showNotification('✅ Данные обновлены');
});

async function init() {
  setStatus('Загрузка данных...');
  await loadUserData();
  await loadInventory();
  await loadShop();
  updateUI();
  connectWebSocket();
  setStatus('Готово');
}

document.addEventListener('DOMContentLoaded', init);
