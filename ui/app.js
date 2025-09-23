// если UI и Flask в одном контейнере (по docker-compose) — оставь пустую строку:
const API_BASE = ""; // будет вызывать /health, /api/* на том же хосте/порту

async function apiCall(endpoint, method = "GET", data = null) {
  try {
    const opts = { method, headers: { "Content-Type": "application/json" } };
    if (data) opts.body = JSON.stringify(data);
    const res = await fetch(`${API_BASE}${endpoint}`, opts);
    const json = await res.json();
    return json;
  } catch (e) {
    console.error(e);
    return { error: e.message };
  }
}

// === базовые кнопки ===
async function checkHealth() {
  const r = await apiCall("/health");
  const ok = r && r.ok;
  setStatus(ok ? `OK (gRPC: ${r.autopilot_grpc})` : `Ошибка: ${r.error || "нет ответа"}`);
}

async function armDrone() {
  setStatus("ARM…");
  const r = await apiCall("/api/arm", "POST");
  setStatus(r.error ? `Ошибка ARM: ${r.error}` : "ARM: OK");
}

async function takeoffDrone() {
  const alt = parseFloat(prompt("Высота взлёта, м:", "10") || "10");
  setStatus(`Взлёт до ${alt} м…`);
  const r = await apiCall("/api/takeoff", "POST", { alt });
  setStatus(r.error ? `Ошибка взлёта: ${r.error}` : `В воздухе (целев. ${alt} м)`);
}

async function landDrone() {
  setStatus("Посадка…");
  const r = await apiCall("/api/land", "POST");
  setStatus(r.error ? `Ошибка посадки: ${r.error}` : "Посадка инициирована");
}

// === совместимость со старыми кнопками ===
async function sendCommand(cmd) {
  if (cmd === "start") {
    await armDrone();
    await takeoffDrone();
  } else if (cmd === "stop") {
    await landDrone();
  }
}

// === язык (минимальная локализация заголовка) ===
function changeLanguage() {
  const lang = document.getElementById("languageSelect").value;
  const map = {
    ru: "Панель управления дроном",
    en: "Drone Control Panel",
    de: "Drohnen-Steuerpult",
    pl: "Panel sterowania dronem",
  };
  document.getElementById("title").innerText = map[lang] || map.ru;
}

// === helpers ===
function setStatus(text) {
  document.getElementById("status").innerText = `Статус: ${text}`;
}

// авто-проверка соединения при загрузке
window.addEventListener("load", checkHealth);