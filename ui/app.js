// базовый URL API
const API_BASE = "http://localhost:5000"; // если работаешь локально
// const API_BASE = ""; // если UI и API в одном контейнере (docker-compose)

async function apiCall(endpoint, method = "GET", data = null) {
    try {
        const options = {
            method,
            headers: { "Content-Type": "application/json" }
        };
        if (data) options.body = JSON.stringify(data);

        const res = await fetch(`${API_BASE}${endpoint}`, options);
        return await res.json();
    } catch (err) {
        console.error("API error:", err);
        return { error: err.message };
    }
}

// ===== Привязка к кнопкам UI =====

async function checkHealth() {
    const result = await apiCall("/health");
    alert("Health: " + JSON.stringify(result));
}

async function armDrone() {
    const result = await apiCall("/api/arm", "POST");
    alert("Arm: " + JSON.stringify(result));
}

async function takeoffDrone() {
    const alt = prompt("Введите высоту взлета (м):", "10");
    const result = await apiCall("/api/takeoff", "POST", { alt: parseFloat(alt) });
    alert("Takeoff: " + JSON.stringify(result));
}

async function landDrone() {
    const result = await apiCall("/api/land", "POST");
    alert("Land: " + JSON.stringify(result));
}