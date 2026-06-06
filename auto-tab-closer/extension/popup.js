let pendingData = {};

function esc(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function fmtCountdown(closeAt) {
  const ms = closeAt - Date.now();
  if (ms <= 0) return '0:00';
  const totalSec = Math.ceil(ms / 1000);
  const min = Math.floor(totalSec / 60);
  const sec = totalSec % 60;
  return `${min}:${sec.toString().padStart(2, '0')}`;
}

function truncate(str, max = 38) {
  return str.length > max ? str.slice(0, max) + '…' : str;
}

function renderTabs() {
  const el = document.getElementById('tabs-list');
  const entries = Object.entries(pendingData);

  if (entries.length === 0) {
    el.innerHTML = '<div class="empty">No tabs pending closure</div>';
    document.getElementById('cancelAllBtn').disabled = true;
    return;
  }

  document.getElementById('cancelAllBtn').disabled = false;

  el.innerHTML = entries.map(([tabId, info]) => {
    const secsLeft = (info.closeAt - Date.now()) / 1000;
    const urgentClass = secsLeft < 60 ? ' urgent' : '';
    return `
      <div class="tab-item" data-tab-id="${tabId}">
        <div class="tab-info">
          <div class="tab-site">${esc(info.name)}</div>
          <div class="tab-title">${esc(truncate(info.title || info.url))}</div>
        </div>
        <span class="tab-countdown${urgentClass}" data-close-at="${info.closeAt}">
          closes in ${fmtCountdown(info.closeAt)}
        </span>
        <button class="cancel-btn" data-tab-id="${tabId}">Keep</button>
      </div>`;
  }).join('');

  el.querySelectorAll('.cancel-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      const tabId = parseInt(btn.dataset.tabId, 10);
      btn.textContent = '…';
      btn.disabled = true;
      await chrome.runtime.sendMessage({ type: 'cancel_tab', tabId });
      delete pendingData[tabId];
      renderTabs();
    });
  });
}

function tickCountdowns() {
  document.querySelectorAll('.tab-countdown[data-close-at]').forEach(el => {
    const closeAt = parseInt(el.dataset.closeAt, 10);
    const secsLeft = (closeAt - Date.now()) / 1000;
    el.textContent = `closes in ${fmtCountdown(closeAt)}`;
    if (secsLeft < 60) el.classList.add('urgent');
    else el.classList.remove('urgent');
  });
}

async function refresh() {
  pendingData = await chrome.runtime.sendMessage({ type: 'get_pending' }) || {};
  renderTabs();
}

document.getElementById('cancelAllBtn').addEventListener('click', async () => {
  const btn = document.getElementById('cancelAllBtn');
  btn.textContent = 'Cancelling…';
  btn.disabled = true;
  await chrome.runtime.sendMessage({ type: 'cancel_all' });
  pendingData = {};
  renderTabs();
  btn.textContent = 'Cancel All';
  document.getElementById('status').textContent = `All cancelled at ${new Date().toLocaleTimeString()}`;
});

document.getElementById('reloadBtn').addEventListener('click', async () => {
  const btn = document.getElementById('reloadBtn');
  btn.textContent = 'Reloading…';
  btn.disabled = true;
  const res = await chrome.runtime.sendMessage({ type: 'reload_config' });
  btn.textContent = 'Reload Config';
  btn.disabled = false;
  if (res?.idleMin) {
    document.getElementById('idle-label').textContent = `${res.idleMin} min idle`;
    document.getElementById('status').textContent = `Config reloaded — idle: ${res.idleMin} min`;
  }
});

// Initial load
refresh().then(() => {
  chrome.runtime.sendMessage({ type: 'reload_config' }, res => {
    if (res?.idleMin) {
      document.getElementById('idle-label').textContent = `${res.idleMin} min idle`;
    }
  });
});

// Refresh pending list every 5s, tick countdowns every second
setInterval(refresh, 5000);
setInterval(tickCountdowns, 1000);
