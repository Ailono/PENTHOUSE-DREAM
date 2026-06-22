const API = window.location.origin;
const WS_URL = API.replace(/^http/, 'ws') + '/ws';

let state = {
  userId: null,
  balance: 0,
  roomLevel: 1,
  happiness: 50,
  level: 1,
  xp: 0,
  inventory: [],
  shopItems: [],
  profile: null,
  isLoggedIn: false,
};

let ws = null;

function $(id) { return document.getElementById(id); }

function setStatus(text) {
  const el = $('statusText');
  if (el) el.textContent = text;
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

async function apiPut(path, body = {}) {
  const params = new URLSearchParams(body);
  const res = await fetch(API + path + '?' + params, { method: 'PUT' });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

function connectWebSocket() {
  if (!state.userId) return;
  if (ws) ws.close();
  ws = new WebSocket(WS_URL + '/' + state.userId);

  ws.onopen = () => {
    const el = $('connectionStatus');
    if (el) {
      el.textContent = '● Подключено';
      el.style.color = '#4ecca3';
    }
    setStatus('WebSocket подключён');
  };

  ws.onclose = () => {
    const el = $('connectionStatus');
    if (el) {
      el.textContent = '○ Отключено';
      el.style.color = '#e94560';
    }
    setStatus('WebSocket отключён, переподключение...');
    setTimeout(connectWebSocket, 3000);
  };

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    handleWsEvent(data);
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
    case 'profile_updated':
      loadProfile();
      break;
    case 'pong':
      break;
  }
}

// --- Login ---

function showLogin() {
  $('loginOverlay').style.display = 'flex';
}

function hideLogin() {
  $('loginOverlay').style.display = 'none';
  state.isLoggedIn = true;
}

async function loginWithCode(code) {
  const errorEl = $('loginError');
  try {
    const result = await apiPost('/api/link/validate', { code });
    if (result.success) {
      state.userId = result.user_id;
      state.profile = result.profile;
      localStorage.setItem('pd_userId', result.user_id);
      localStorage.setItem('pd_linked', 'true');
      hideLogin();
      await afterLogin();
      showNotification('✅ Аккаунт связан с Telegram!');
    }
  } catch (e) {
    errorEl.textContent = '❌ Неверный или просроченный код';
    setTimeout(() => errorEl.textContent = '', 3000);
  }
}

async function loginAsGuest() {
  let guestId = localStorage.getItem('pd_userId');
  if (!guestId) {
    guestId = Math.floor(Math.random() * 900000) + 100000;
    try {
      await apiPost('/api/users/', { user_id: guestId, username: 'Гость' });
    } catch {}
    localStorage.setItem('pd_userId', guestId);
  }
  state.userId = parseInt(guestId);
  localStorage.setItem('pd_linked', 'false');
  hideLogin();
  await afterLogin();
}

async function afterLogin() {
  await apiPost('/api/users/' + state.userId + '/login');
  await loadProfile();
  await loadInventory();
  await loadShop();
  updateUI();
  connectWebSocket();
  setStatus('Готово');
}

// --- Profile ---

async function loadProfile() {
  try {
    state.profile = await apiGet('/api/users/' + state.userId + '/profile');
    state.balance = state.profile.balance;
    state.roomLevel = state.profile.room_level;
    state.happiness = state.profile.happiness;
    state.level = state.profile.level;
    state.xp = state.profile.xp;
    updateUI();
    renderProfile();
  } catch {}
}

function renderProfile() {
  const p = state.profile;
  if (!p) return;

  $('profileUsernameDisplay').textContent = p.username || 'Без имени';
  $('profileBioDisplay').textContent = p.bio || '';
  $('profileBioDisplay').style.display = p.bio ? 'block' : 'none';

  $('pLevel').textContent = p.level;
  $('pBalance').textContent = p.balance.toLocaleString();
  $('pRoom').textContent = p.room_level;
  $('pHappiness').textContent = p.happiness + '%';
  $('pInventory').textContent = p.inventory_count;
  $('pAchievements').textContent = p.achievements_count;
  $('pGamesWon').textContent = p.games_won;
  $('pXp').textContent = p.xp;

  const xpForCurrent = ((p.level - 1) ** 2) * 100;
  const xpForNext = (p.level ** 2) * 100;
  const xpInLevel = p.xp - xpForCurrent;
  const xpNeeded = xpForNext - xpForCurrent;
  const pct = Math.min(100, Math.round((xpInLevel / Math.max(xpNeeded, 1)) * 100));
  $('pXpFill').style.width = pct + '%';
  $('pXpInfo').textContent = `${xpInLevel} / ${xpNeeded} XP`;

  $('pCreatedAt').textContent = p.created_at ? p.created_at.slice(0, 10) : '—';
  $('pLastLogin').textContent = p.last_login ? p.last_login.slice(0, 10) : '—';

  $('profileAvatar').textContent = p.avatar_url || (p.username ? p.username[0].toUpperCase() : '👤');

  if (p.is_telegram_linked) {
    $('profileLinkSection').style.display = 'none';
    $('profileLinkedSection').style.display = 'block';
    $('profileTelegramUser').textContent = p.telegram_username || 'Telegram';
  } else {
    $('profileLinkSection').style.display = 'block';
    $('profileLinkedSection').style.display = 'none';
  }
}

function updateUI() {
  const bd = $('balanceDisplay');
  const rd = $('roomLevelDisplay');
  const hd = $('happinessDisplay');
  const ld = $('levelDisplay');
  if (bd) bd.textContent = state.balance.toLocaleString();
  if (rd) rd.textContent = state.roomLevel;
  if (hd) hd.textContent = state.happiness;
  if (ld) ld.textContent = state.level;
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

// --- Sidebar navigation ---

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
    if (view === 'profile') {
      loadProfile();
    }
  });
});

$('refreshBtn').addEventListener('click', async () => {
  setStatus('Загрузка...');
  await Promise.all([loadProfile(), loadInventory(), loadShop()]);
  updateUI();
  setStatus('Обновлено');
  showNotification('✅ Данные обновлены');
});

// --- Login UI ---

$('loginCodeBtn').addEventListener('click', () => {
  const code = $('loginCodeInput').value.trim().toUpperCase();
  if (code) loginWithCode(code);
});

$('loginCodeInput').addEventListener('keydown', (e) => {
  if (e.key === 'Enter') $('loginCodeBtn').click();
});

$('loginGuestBtn').addEventListener('click', loginAsGuest);

// --- Profile Edit ---

$('profileEditBtn').addEventListener('click', () => {
  const form = $('profileEditForm');
  if (form.style.display === 'none' || !form.style.display) {
    const p = state.profile;
    $('editUsername').value = p.username || '';
    $('editBio').value = p.bio || '';
    form.style.display = 'block';
  } else {
    form.style.display = 'none';
  }
});

$('profileCancelBtn').addEventListener('click', () => {
  $('profileEditForm').style.display = 'none';
});

$('profileSaveBtn').addEventListener('click', async () => {
  const username = $('editUsername').value.trim();
  const bio = $('editBio').value.trim();
  try {
    await apiPut('/api/users/' + state.userId + '/profile', { username, bio });
    $('profileEditForm').style.display = 'none';
    await loadProfile();
    showNotification('✅ Профиль обновлён');
  } catch {
    showNotification('❌ Ошибка сохранения');
  }
});

// --- Profile Link ---

$('profileLinkBtn').addEventListener('click', async () => {
  const code = $('profileLinkInput').value.trim().toUpperCase();
  const statusEl = $('profileLinkStatus');
  if (!code) {
    statusEl.textContent = '❌ Введи код';
    return;
  }
  try {
    const result = await apiPost('/api/link/validate', { code });
    if (result.success) {
      state.userId = result.user_id;
      state.profile = result.profile;
      localStorage.setItem('pd_userId', result.user_id);
      localStorage.setItem('pd_linked', 'true');
      showNotification('✅ Telegram подключён!');
      await loadProfile();
    }
  } catch {
    statusEl.textContent = '❌ Неверный или просроченный код';
    setTimeout(() => statusEl.textContent = '', 3000);
  }
});

// --- Init ---

async function init() {
  const savedId = localStorage.getItem('pd_userId');
  const linked = localStorage.getItem('pd_linked');

  if (savedId && linked === 'true') {
    state.userId = parseInt(savedId);
    hideLogin();
    await afterLogin();
  } else if (savedId && linked === 'false') {
    state.userId = parseInt(savedId);
    hideLogin();
    await afterLogin();
  } else {
    showLogin();
  }
}

document.addEventListener('DOMContentLoaded', init);