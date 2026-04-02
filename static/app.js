const state = {
  terminal: {
    sessionId: null,
    offset: 0,
    timer: null,
  },
};

const deviceName = document.querySelector("#device-name");
const deviceMeta = document.querySelector("#device-meta");
const runtimeJson = document.querySelector("#runtime-json");
const gpioList = document.querySelector("#gpio-list");
const terminalOutput = document.querySelector("#terminal-output");
const terminalForm = document.querySelector("#terminal-form");
const terminalInput = document.querySelector("#terminal-input");

async function request(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json();
}

async function refreshStatus() {
  const payload = await request("/api/status");
  deviceName.textContent = payload.device.device_name;
  deviceMeta.textContent = `${payload.device.device_id} · hotspot ${payload.device.hotspot.ssid} · ${payload.device.hotspot.address}`;
  runtimeJson.textContent = JSON.stringify(payload.runtime, null, 2);
  renderGpio(payload.runtime.gpio.pins);
}

function renderGpio(pins) {
  gpioList.innerHTML = "";
  pins.forEach((entry) => {
    const row = document.createElement("div");
    row.className = "gpio-item";
    row.innerHTML = `
      <strong>GPIO ${entry.pin}</strong>
      <span class="pill">State ${entry.value}</span>
    `;

    const onButton = document.createElement("button");
    onButton.textContent = "ON";
    onButton.addEventListener("click", () => updateGpio(entry.pin, 1));

    const offButton = document.createElement("button");
    offButton.textContent = "OFF";
    offButton.addEventListener("click", () => updateGpio(entry.pin, 0));

    row.appendChild(onButton);
    row.appendChild(offButton);
    gpioList.appendChild(row);
  });
}

async function updateGpio(pin, value) {
  await request("/api/gpio/write", {
    method: "POST",
    body: JSON.stringify({ pin, value }),
  });
  await refreshStatus();
}

async function startRuntime() {
  await request("/api/runtime/start", {
    method: "POST",
    body: JSON.stringify({}),
  });
  await refreshStatus();
}

async function createTerminal() {
  const payload = await request("/api/terminal/session", {
    method: "POST",
    body: JSON.stringify({}),
  });
  state.terminal.sessionId = payload.session_id;
  state.terminal.offset = 0;
  terminalOutput.textContent = "";
  startTerminalPolling();
}

async function pollTerminal() {
  if (!state.terminal.sessionId) {
    return;
  }
  const payload = await request(
    `/api/terminal/session/${state.terminal.sessionId}?offset=${state.terminal.offset}`
  );
  if (payload.output) {
    terminalOutput.textContent += payload.output;
    terminalOutput.scrollTop = terminalOutput.scrollHeight;
  }
  state.terminal.offset = payload.offset;
}

function startTerminalPolling() {
  if (state.terminal.timer) {
    clearInterval(state.terminal.timer);
  }
  state.terminal.timer = setInterval(() => {
    pollTerminal().catch((error) => {
      console.error(error);
    });
  }, 700);
}

async function sendTerminalInput(command) {
  if (!state.terminal.sessionId) {
    await createTerminal();
  }
  await request(`/api/terminal/session/${state.terminal.sessionId}/input`, {
    method: "POST",
    body: JSON.stringify({ input: `${command}\n` }),
  });
  terminalInput.value = "";
}

document.querySelector("#start-runtime").addEventListener("click", () => {
  startRuntime().catch((error) => console.error(error));
});

document.querySelector("#refresh-gpio").addEventListener("click", () => {
  refreshStatus().catch((error) => console.error(error));
});

document.querySelector("#create-terminal").addEventListener("click", () => {
  createTerminal().catch((error) => console.error(error));
});

terminalForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const value = terminalInput.value.trim();
  if (!value) {
    return;
  }
  sendTerminalInput(value).catch((error) => console.error(error));
});

refreshStatus().catch((error) => console.error(error));
