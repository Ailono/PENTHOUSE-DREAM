const canvas = document.getElementById('roomCanvas');
const ctx = canvas.getContext('2d');

function resizeRoomCanvas() {
  const rect = canvas.getBoundingClientRect();
  const w = Math.round(rect.width);
  const h = Math.round(rect.height);
  if (w > 0 && h > 0 && (canvas.width !== w || canvas.height !== h)) {
    canvas.width = w;
    canvas.height = h;
  }
}

window.addEventListener('resize', resizeRoomCanvas);
window.addEventListener('orientationchange', resizeRoomCanvas);

const ITEM_EMOJI = {
  chair: '🪑', table: '🪑', lamp: '💡', carpet: '🟫', painting: '🖼️',
  aquarium: '🪸', fireplace: '🔥', sofa: '🛋️', bookshelf: '📚', plant: '🌿',
  floor_lamp: '💡', coffee_table: '🪑', mirror: '🪞', clock: '🕐', fountain: '⛲',
};

const RARITY_COLORS = {
  common: ['#4ecca3', '#3db88b'],
  uncommon: ['#3498db', '#2980b9'],
  rare: ['#9b59b6', '#8e44ad'],
  legendary: ['#e67e22', '#d35400'],
};

class Room {
  constructor() {
    this.wallColor = '#3d3d5c';
    this.floorColor = '#2d2d44';
    this.time = 0;
    this.dayPhase = 'day';
    this.character = new Character(380, 390);
    this.furniture = [];
    this.windowX = 200;
    this.windowY = 70;
    this.windowW = 300;
    this.windowH = 120;
    this.doorX = 650;
    this.doorY = 250;
    this.doorW = 60;
    this.doorH = 150;
  }

  addItem(item) {
    this.furniture.push(item);
  }

  removeItem(type) {
    this.furniture = this.furniture.filter(f => f.type !== type);
  }

  update(dt) {
    this.time += dt;
    this.character.update(dt);
    this.furniture.forEach(f => f.update(dt));
  }

  draw() {
    const s = Math.min(canvas.width / 800, canvas.height / 500);
    ctx.save();
    ctx.scale(s, s);

    ctx.fillStyle = '#1a1a2e';
    ctx.fillRect(0, 0, 800, 500);

    this.drawBackWall();
    this.drawWindow();
    this.drawDoor();
    this.drawFloor();

    this.character.draw(ctx);
    this.furniture.forEach(f => f.draw(ctx));
    this.drawBaseboard();

    ctx.restore();
  }

  drawBackWall() {
    ctx.fillStyle = this.wallColor;
    ctx.fillRect(50, 50, 700, 330);

    for (let i = 0; i < 6; i++) {
      const x = 80 + i * 120;
      ctx.fillStyle = 'rgba(255,255,255,0.03)';
      ctx.fillRect(x, 55, 80, 320);
    }
  }

  drawWindow() {
    const skyGrad = ctx.createLinearGradient(this.windowX, this.windowY, this.windowX, this.windowY + this.windowH);
    skyGrad.addColorStop(0, '#1a1a4e');
    skyGrad.addColorStop(0.5, '#2d2d6e');
    skyGrad.addColorStop(1, '#4a4a8e');
    ctx.fillStyle = skyGrad;
    ctx.fillRect(this.windowX, this.windowY, this.windowW, this.windowH);

    const stars = 20;
    ctx.fillStyle = '#fff';
    for (let i = 0; i < stars; i++) {
      const sx = this.windowX + 10 + ((i * 37 + 13) % (this.windowW - 20));
      const sy = this.windowY + 10 + ((i * 53 + 7) % (this.windowH - 40));
      const size = 1 + (i % 2);
      const twinkle = 0.5 + 0.5 * Math.sin(this.time * 2 + i);
      ctx.globalAlpha = twinkle;
      ctx.fillRect(sx, sy, size, size);
    }
    ctx.globalAlpha = 1;

    const moon = ctx.createRadialGradient(this.windowX + 220, this.windowY + 30, 0, this.windowX + 220, this.windowY + 30, 20);
    moon.addColorStop(0, 'rgba(255,255,200,0.8)');
    moon.addColorStop(1, 'rgba(255,255,200,0)');
    ctx.fillStyle = moon;
    ctx.beginPath();
    ctx.arc(this.windowX + 220, this.windowY + 30, 20, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#ddd';
    ctx.beginPath();
    ctx.arc(this.windowX + 220, this.windowY + 30, 12, 0, Math.PI * 2);
    ctx.fill();

    ctx.strokeStyle = '#5d4037';
    ctx.lineWidth = 4;
    ctx.strokeRect(this.windowX, this.windowY, this.windowW, this.windowH);
    ctx.beginPath();
    ctx.moveTo(this.windowX + this.windowW / 2, this.windowY);
    ctx.lineTo(this.windowX + this.windowW / 2, this.windowY + this.windowH);
    ctx.moveTo(this.windowX, this.windowY + this.windowH / 2);
    ctx.lineTo(this.windowX + this.windowW, this.windowY + this.windowH / 2);
    ctx.stroke();
  }

  drawDoor() {
    ctx.fillStyle = '#5d4037';
    ctx.fillRect(this.doorX, this.doorY, this.doorW, this.doorH);
    ctx.strokeStyle = '#3e2723';
    ctx.lineWidth = 2;
    ctx.strokeRect(this.doorX, this.doorY, this.doorW, this.doorH);
    ctx.fillStyle = '#ffd700';
    ctx.beginPath();
    ctx.arc(this.doorX + 48, this.doorY + 75, 4, 0, Math.PI * 2);
    ctx.fill();
  }

  drawFloor() {
    ctx.fillStyle = this.floorColor;
    ctx.fillRect(50, 380, 700, 100);

    for (let y = 390; y < 480; y += 20) {
      ctx.strokeStyle = 'rgba(255,255,255,0.05)';
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(50, y);
      ctx.lineTo(750, y);
      ctx.stroke();
    }
  }

  drawBaseboard() {
    ctx.fillStyle = '#2d2d44';
    ctx.fillRect(48, 378, 704, 6);
  }
}

class Character {
  constructor(x, y) {
    this.x = x;
    this.y = y;
    this.radius = 24;
    this.emotion = '😊';
    this.state = 'idle';
    this.bobPhase = 0;
    this.armAngle = 0;
    this.emotions = ['😊', '😴', '💃', '⚡', '😎'];
  }

  setEmotion(emoji) {
    this.emotion = emoji;
  }

  setState(state) {
    this.state = state;
  }

  update(dt) {
    this.bobPhase += dt * 2;
    this.armAngle = Math.sin(this.bobPhase) * 0.1;
  }

  draw(ctx) {
    const bobY = Math.sin(this.bobPhase) * 2;

    ctx.save();
    ctx.translate(this.x, this.y + bobY);

    ctx.fillStyle = '#e94560';
    ctx.beginPath();
    ctx.arc(0, 0, this.radius, 0, Math.PI * 2);
    ctx.fill();

    ctx.strokeStyle = '#c73650';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(0, 0, this.radius, 0, Math.PI * 2);
    ctx.stroke();

    ctx.fillStyle = '#fff';
    ctx.beginPath();
    ctx.arc(-8, -6, 4, 0, Math.PI * 2);
    ctx.fill();
    ctx.beginPath();
    ctx.arc(8, -6, 4, 0, Math.PI * 2);
    ctx.fill();

    ctx.fillStyle = '#222';
    ctx.beginPath();
    ctx.arc(-7, -6, 2, 0, Math.PI * 2);
    ctx.fill();
    ctx.beginPath();
    ctx.arc(9, -6, 2, 0, Math.PI * 2);
    ctx.fill();

    ctx.font = '16px Arial';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(this.emotion, 0, -32);

    if (this.state === 'working') {
      ctx.strokeStyle = '#e94560';
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.moveTo(-20, 10);
      ctx.lineTo(-30 + Math.sin(this.bobPhase * 3) * 5, 35);
      ctx.moveTo(20, 10);
      ctx.lineTo(30 + Math.cos(this.bobPhase * 3) * 5, 35);
      ctx.stroke();
    }

    ctx.restore();
  }
}

class Furniture {
  constructor(type, x, y, rarity = 'common') {
    this.type = type;
    this.x = x;
    this.y = y;
    this.rarity = rarity;
    this.time = 0;
  }

  update(dt) {
    this.time += dt;
  }

  draw(ctx) {}

  getColor() {
    return RARITY_COLORS[this.rarity] || RARITY_COLORS.common;
  }
}

class Chair extends Furniture {
  constructor(x, y, rarity) {
    super('chair', x, y, rarity);
    this.w = 50;
    this.h = 60;
  }

  draw(ctx) {
    const [c1, c2] = this.getColor();
    ctx.fillStyle = c1;
    ctx.fillRect(this.x, this.y + 20, this.w, this.h - 20);
    ctx.fillRect(this.x + 5, this.y, this.w - 10, 25);
    ctx.fillStyle = '#333';
    ctx.fillRect(this.x, this.y + this.h - 5, 8, 15);
    ctx.fillRect(this.x + this.w - 8, this.y + this.h - 5, 8, 15);
  }
}

class Table extends Furniture {
  constructor(x, y, rarity) {
    super('table', x, y, rarity);
    this.w = 80;
    this.h = 50;
  }

  draw(ctx) {
    const [c1, c2] = this.getColor();
    ctx.fillStyle = c1;
    ctx.fillRect(this.x, this.y, this.w, 10);
    ctx.fillStyle = c2;
    ctx.fillRect(this.x, this.y + 10, this.w, 4);
    ctx.fillStyle = '#333';
    ctx.fillRect(this.x + 5, this.y + 10, 6, 40);
    ctx.fillRect(this.x + this.w - 11, this.y + 10, 6, 40);
  }
}

class Lamp extends Furniture {
  constructor(x, y, rarity) {
    super('lamp', x, y, rarity);
    this.w = 30;
    this.h = 80;
    this.glowPhase = 0;
  }

  update(dt) {
    super.update(dt);
    this.glowPhase += dt * 3;
  }

  draw(ctx) {
    const [c1] = this.getColor();
    ctx.fillStyle = '#555';
    ctx.fillRect(this.x + 12, this.y + 30, 6, 50);
    ctx.fillStyle = c1;
    ctx.beginPath();
    ctx.moveTo(this.x, this.y + 35);
    ctx.lineTo(this.x + this.w, this.y + 35);
    ctx.lineTo(this.x + this.w - 5, this.y + 5);
    ctx.lineTo(this.x + 5, this.y + 5);
    ctx.closePath();
    ctx.fill();
    const glow = 0.1 + 0.05 * Math.sin(this.glowPhase);
    const grad = ctx.createRadialGradient(this.x + 15, this.y + 20, 0, this.x + 15, this.y + 20, 60);
    grad.addColorStop(0, `rgba(255,255,200,${glow})`);
    grad.addColorStop(1, 'rgba(255,255,200,0)');
    ctx.fillStyle = grad;
    ctx.beginPath();
    ctx.arc(this.x + 15, this.y + 20, 60, 0, Math.PI * 2);
    ctx.fill();
  }
}

class Carpet extends Furniture {
  constructor(x, y, rarity) {
    super('carpet', x, y, rarity);
    this.w = 120;
    this.h = 70;
  }

  draw(ctx) {
    const [c1, c2] = this.getColor();
    ctx.fillStyle = c1;
    ctx.beginPath();
    ctx.ellipse(this.x + this.w / 2, this.y + this.h / 2, this.w / 2, this.h / 2, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.strokeStyle = c2;
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.ellipse(this.x + this.w / 2, this.y + this.h / 2, this.w / 2 - 5, this.h / 2 - 5, 0, 0, Math.PI * 2);
    ctx.stroke();
  }
}

class Painting extends Furniture {
  constructor(x, y, rarity) {
    super('painting', x, y, rarity);
    this.w = 80;
    this.h = 60;
  }

  draw(ctx) {
    const [c1] = this.getColor();
    ctx.fillStyle = '#8B4513';
    ctx.fillRect(this.x - 3, this.y - 3, this.w + 6, this.h + 6);
    ctx.fillStyle = c1;
    ctx.fillRect(this.x, this.y, this.w, this.h);
    ctx.fillStyle = '#222';
    ctx.font = '20px Arial';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText('🎨', this.x + this.w / 2, this.y + this.h / 2);
  }
}

class Aquarium extends Furniture {
  constructor(x, y, rarity) {
    super('aquarium', x, y, rarity);
    this.w = 80;
    this.h = 60;
    this.fish = [
      { x: 20, y: 20, speed: 30, phase: 0 },
      { x: 50, y: 35, speed: 25, phase: 1.5 },
      { x: 35, y: 45, speed: 35, phase: 3 },
    ];
  }

  update(dt) {
    super.update(dt);
    this.fish.forEach((fish, i) => {
      fish.x += Math.sin(this.time * fish.speed + fish.phase) * dt * 20;
      fish.y += Math.cos(this.time * fish.speed * 0.7 + fish.phase + 1) * dt * 10;
      if (fish.x < 10) fish.x = 10;
      if (fish.x > this.w - 10) fish.x = this.w - 10;
      if (fish.y < 10) fish.y = 10;
      if (fish.y > this.h - 15) fish.y = this.h - 15;
    });
  }

  draw(ctx) {
    ctx.fillStyle = '#1a4a6e';
    ctx.fillRect(this.x, this.y, this.w, this.h);
    ctx.strokeStyle = '#5dade2';
    ctx.lineWidth = 2;
    ctx.strokeRect(this.x, this.y, this.w, this.h);
    ctx.fillStyle = 'rgba(255,255,255,0.1)';
    ctx.fillRect(this.x + 2, this.y + 2, 10, 10);
    this.fish.forEach(fish => {
      ctx.fillStyle = '#ff6b6b';
      ctx.beginPath();
      ctx.arc(this.x + fish.x, this.y + fish.y, 4, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = '#ffd700';
      ctx.beginPath();
      ctx.arc(this.x + fish.x + 3, this.y + fish.y - 1, 2, 0, Math.PI * 2);
      ctx.fill();
    });
    ctx.fillStyle = '#5dade2';
    ctx.font = '10px Arial';
    ctx.textAlign = 'center';
    ctx.fillText('💧', this.x + this.w / 2, this.y + this.h - 5);
  }
}

class Fireplace extends Furniture {
  constructor(x, y, rarity) {
    super('fireplace', x, y, rarity);
    this.w = 100;
    this.h = 80;
    this.flames = [
      { x: 30, h: 25, speed: 4, phase: 0 },
      { x: 50, h: 35, speed: 3, phase: 1.2 },
      { x: 70, h: 20, speed: 5, phase: 2.5 },
    ];
    this.glowPhase = 0;
  }

  update(dt) {
    super.update(dt);
    this.glowPhase += dt * 2;
    this.flames.forEach(f => {
      f.h = f.h + Math.sin(this.time * f.speed + f.phase) * 3;
    });
  }

  draw(ctx) {
    const [c1] = this.getColor();
    ctx.fillStyle = '#5d4037';
    ctx.fillRect(this.x, this.y + 15, this.w, this.h - 15);
    ctx.strokeStyle = '#3e2723';
    ctx.lineWidth = 2;
    ctx.strokeRect(this.x, this.y + 15, this.w, this.h - 15);
    ctx.fillRect(this.x + 5, this.y, 8, 20);
    ctx.fillRect(this.x + this.w - 13, this.y, 8, 20);

    ctx.fillStyle = '#1a1a1a';
    ctx.fillRect(this.x + 15, this.y + 35, this.w - 30, this.h - 45);

    const glow = 0.3 + 0.1 * Math.sin(this.glowPhase);
    const grad = ctx.createRadialGradient(
      this.x + this.w / 2, this.y + 40, 0,
      this.x + this.w / 2, this.y + 40, 60
    );
    grad.addColorStop(0, `rgba(255,150,50,${glow})`);
    grad.addColorStop(1, 'rgba(255,150,50,0)');
    ctx.fillStyle = grad;
    ctx.beginPath();
    ctx.arc(this.x + this.w / 2, this.y + 40, 60, 0, Math.PI * 2);
    ctx.fill();

    this.flames.forEach(f => {
      ctx.fillStyle = '#ff6b35';
      ctx.beginPath();
      ctx.moveTo(this.x + f.x, this.y + 40);
      ctx.quadraticCurveTo(this.x + f.x - 8, this.y + 40 - f.h, this.x + f.x, this.y + 40 - f.h - 5);
      ctx.quadraticCurveTo(this.x + f.x + 8, this.y + 40 - f.h, this.x + f.x, this.y + 40);
      ctx.fill();
      ctx.fillStyle = 'rgba(255,200,50,0.6)';
      ctx.beginPath();
      ctx.moveTo(this.x + f.x, this.y + 40);
      ctx.quadraticCurveTo(this.x + f.x - 4, this.y + 40 - f.h * 0.6, this.x + f.x, this.y + 40 - f.h * 0.7);
      ctx.quadraticCurveTo(this.x + f.x + 4, this.y + 40 - f.h * 0.6, this.x + f.x, this.y + 40);
      ctx.fill();
    });

    ctx.fillStyle = '#8d6e63';
    ctx.fillRect(this.x - 5, this.y + this.h - 5, this.w + 10, 8);
  }
}

class Sofa extends Furniture {
  constructor(x, y, rarity) {
    super('sofa', x, y, rarity);
    this.w = 130;
    this.h = 50;
  }

  draw(ctx) {
    const [c1, c2] = this.getColor();
    ctx.fillStyle = c1;
    ctx.fillRect(this.x, this.y + 10, this.w, this.h - 10);
    ctx.fillRect(this.x + 15, this.y, this.w - 30, 15);
    ctx.fillStyle = c2;
    ctx.fillRect(this.x + 5, this.y + 20, this.w - 10, 5);
    ctx.fillStyle = '#333';
    ctx.fillRect(this.x + 10, this.y + this.h - 5, 8, 12);
    ctx.fillRect(this.x + this.w - 18, this.y + this.h - 5, 8, 12);
  }
}

class Bookshelf extends Furniture {
  constructor(x, y, rarity) {
    super('bookshelf', x, y, rarity);
    this.w = 60;
    this.h = 100;
  }

  draw(ctx) {
    const [c1, c2] = this.getColor();
    ctx.fillStyle = '#5d4037';
    ctx.fillRect(this.x, this.y, this.w, this.h);
    ctx.strokeStyle = '#3e2723';
    ctx.lineWidth = 2;
    ctx.strokeRect(this.x, this.y, this.w, this.h);
    for (let i = 1; i < 4; i++) {
      ctx.fillStyle = '#3e2723';
      ctx.fillRect(this.x, this.y + i * 25, this.w, 2);
    }
    const bookColors = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c'];
    for (let i = 0; i < 6; i++) {
      const bx = this.x + 5 + (i % 2) * 25;
      const by = this.y + 3 + Math.floor(i / 2) * 25;
      ctx.fillStyle = bookColors[i % bookColors.length];
      ctx.fillRect(bx, by, 18, 20);
    }
  }
}

class Plant extends Furniture {
  constructor(x, y, rarity) {
    super('plant', x, y, rarity);
    this.w = 40;
    this.h = 60;
  }

  draw(ctx) {
    const [c1] = this.getColor();
    ctx.fillStyle = '#8d6e63';
    ctx.fillRect(this.x + 10, this.y + 40, 20, 20);
    ctx.fillStyle = '#2ecc71';
    ctx.beginPath();
    ctx.arc(this.x + 20, this.y + 30, 20, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#27ae60';
    ctx.beginPath();
    ctx.arc(this.x + 10, this.y + 20, 12, 0, Math.PI * 2);
    ctx.arc(this.x + 30, this.y + 22, 14, 0, Math.PI * 2);
    ctx.arc(this.x + 20, this.y + 12, 10, 0, Math.PI * 2);
    ctx.fill();
  }
}

class FloorLamp extends Furniture {
  constructor(x, y, rarity) {
    super('floor_lamp', x, y, rarity);
    this.w = 40;
    this.h = 110;
    this.glowPhase = 0;
  }

  update(dt) {
    super.update(dt);
    this.glowPhase += dt * 2;
  }

  draw(ctx) {
    const [c1] = this.getColor();
    ctx.fillStyle = '#666';
    ctx.fillRect(this.x + 17, this.y + 40, 6, 70);
    ctx.fillStyle = c1;
    ctx.beginPath();
    ctx.moveTo(this.x, this.y + 5);
    ctx.lineTo(this.x + this.w, this.y + 5);
    ctx.lineTo(this.x + this.w - 8, this.y + 40);
    ctx.lineTo(this.x + 8, this.y + 40);
    ctx.closePath();
    ctx.fill();
    ctx.fillStyle = '#444';
    ctx.ellipse(this.x + 20, this.y + 110, 15, 5, 0, 0, Math.PI * 2);
    ctx.fill();
    const glow = 0.08 + 0.04 * Math.sin(this.glowPhase);
    const grad = ctx.createRadialGradient(this.x + 20, this.y + 20, 0, this.x + 20, this.y + 20, 50);
    grad.addColorStop(0, `rgba(255,255,200,${glow})`);
    grad.addColorStop(1, 'rgba(255,255,200,0)');
    ctx.fillStyle = grad;
    ctx.beginPath();
    ctx.arc(this.x + 20, this.y + 20, 50, 0, Math.PI * 2);
    ctx.fill();
  }
}

class CoffeeTable extends Furniture {
  constructor(x, y, rarity) {
    super('coffee_table', x, y, rarity);
    this.w = 70;
    this.h = 35;
  }

  draw(ctx) {
    const [c1] = this.getColor();
    ctx.fillStyle = c1;
    ctx.fillRect(this.x, this.y, this.w, 8);
    ctx.fillStyle = '#555';
    ctx.fillRect(this.x + 5, this.y + 8, 6, 27);
    ctx.fillRect(this.x + this.w - 11, this.y + 8, 6, 27);
    ctx.fillStyle = 'rgba(255,255,255,0.1)';
    ctx.fillRect(this.x + 2, this.y + 2, 12, 4);
  }
}

class Mirror extends Furniture {
  constructor(x, y, rarity) {
    super('mirror', x, y, rarity);
    this.w = 50;
    this.h = 70;
  }

  draw(ctx) {
    const [c1] = this.getColor();
    ctx.fillStyle = '#8B4513';
    ctx.fillRect(this.x - 3, this.y - 3, this.w + 6, this.h + 6);
    ctx.fillStyle = '#b0e0e6';
    ctx.beginPath();
    ctx.ellipse(this.x + this.w / 2, this.y + this.h / 2, this.w / 2 - 5, this.h / 2 - 5, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.strokeStyle = 'rgba(255,255,255,0.3)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.ellipse(this.x + this.w / 2, this.y + this.h / 2, this.w / 2 - 5, this.h / 2 - 5, 0, 0, Math.PI * 2);
    ctx.stroke();
  }
}

class Clock extends Furniture {
  constructor(x, y, rarity) {
    super('clock', x, y, rarity);
    this.w = 50;
    this.h = 50;
  }

  draw(ctx) {
    const [c1] = this.getColor();
    ctx.fillStyle = '#8B4513';
    ctx.beginPath();
    ctx.arc(this.x + this.w / 2, this.y + this.h / 2, this.w / 2 + 2, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#fff';
    ctx.beginPath();
    ctx.arc(this.x + this.w / 2, this.y + this.h / 2, this.w / 2 - 4, 0, Math.PI * 2);
    ctx.fill();
    const cx = this.x + this.w / 2, cy = this.y + this.h / 2;
    const angle = this.time * 0.5;
    ctx.strokeStyle = '#333';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.lineTo(cx + Math.sin(angle) * 15, cy - Math.cos(angle) * 15);
    ctx.stroke();
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.lineTo(cx + Math.sin(angle * 6) * 10, cy - Math.cos(angle * 6) * 10);
    ctx.stroke();
    ctx.fillStyle = '#e74c3c';
    ctx.beginPath();
    ctx.arc(cx, cy, 2, 0, Math.PI * 2);
    ctx.fill();
  }
}

class Fountain extends Furniture {
  constructor(x, y, rarity) {
    super('fountain', x, y, rarity);
    this.w = 70;
    this.h = 80;
    this.particles = [];
    for (let i = 0; i < 15; i++) {
      this.particles.push({
        x: 0, y: 0, vy: -40 - Math.random() * 30,
        vx: (Math.random() - 0.5) * 20,
        life: Math.random(),
      });
    }
  }

  update(dt) {
    super.update(dt);
    this.particles.forEach(p => {
      p.x += p.vx * dt;
      p.y += p.vy * dt;
      p.vy += 80 * dt;
      p.life -= dt * 0.5;
      if (p.life <= 0 || p.y > 0) {
        p.x = (Math.random() - 0.5) * 10;
        p.y = 0;
        p.vy = -40 - Math.random() * 30;
        p.vx = (Math.random() - 0.5) * 20;
        p.life = 1 + Math.random();
      }
    });
  }

  draw(ctx) {
    const [c1] = this.getColor();
    ctx.fillStyle = '#888';
    ctx.fillRect(this.x + 5, this.y + 50, this.w - 10, 30);
    ctx.fillRect(this.x + 25, this.y + 30, 20, 25);
    ctx.fillStyle = '#5dade2';
    ctx.beginPath();
    ctx.arc(this.x + this.w / 2, this.y + 40, 15, 0, Math.PI * 2);
    ctx.fill();
    this.particles.forEach(p => {
      ctx.fillStyle = `rgba(100,180,255,${Math.max(0, p.life * 0.5)})`;
      ctx.beginPath();
      ctx.arc(this.x + this.w / 2 + p.x, this.y + 40 + p.y, 2, 0, Math.PI * 2);
      ctx.fill();
    });
  }
}

const FURNITURE_CLASSES = {
  chair: Chair, table: Table, lamp: Lamp, carpet: Carpet,
  painting: Painting, aquarium: Aquarium, fireplace: Fireplace,
  sofa: Sofa, bookshelf: Bookshelf, plant: Plant,
  floor_lamp: FloorLamp, coffee_table: CoffeeTable,
  mirror: Mirror, clock: Clock, fountain: Fountain,
};

const room = new Room();

room.addItem(new Chair(320, 360, 'common'));
room.addItem(new Table(200, 340, 'common'));
room.addItem(new Lamp(540, 320, 'uncommon'));
room.addItem(new Carpet(300, 400, 'common'));
room.addItem(new Painting(100, 150, 'rare'));

let lastTime = 0;

function gameLoop(timestamp) {
  const dt = Math.min((timestamp - lastTime) / 1000, 0.05);
  lastTime = timestamp;

  room.update(dt);
  room.draw();

  requestAnimationFrame(gameLoop);
}

resizeRoomCanvas();

requestAnimationFrame((t) => {
  lastTime = t;
  gameLoop(t);
});
