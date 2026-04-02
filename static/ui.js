const state = {
  device: null,
  runtime: null,
  activeTab: "terminal-panel",
  terminal: {
    sessionId: null,
    offset: 0,
    timer: null,
  },
};

const deviceName = document.querySelector("#device-name");
const deviceMeta = document.querySelector("#device-meta");
const vncStatus = document.querySelector("#vnc-status");
const vncMessage = document.querySelector("#vnc-message");
const vncFrame = document.querySelector("#vnc-frame");
const vncOverlay = document.querySelector("#vnc-overlay");
const openVnc = document.querySelector("#open-vnc");
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

function setActiveTab(panelId) {
  state.activeTab = panelId;
  document.querySelectorAll(".tab-button").forEach((button) => {
    button.classList.toggle("is-active", button.dataset.tabTarget === panelId);
  });
  document.querySelectorAll(".panel").forEach((panel) => {
    panel.classList.toggle("is-active", panel.id === panelId);
  });
}

function buildNoVncUrl(vnc) {
  const host = window.location.hostname;
  return `http://${host}:${vnc.novnc_port}${vnc.client_path}`;
}

function renderVncStatus(vnc) {
  const running = Boolean(vnc?.novnc_running);
  vncStatus.textContent = running ? "VNC Ready" : "VNC Offline";
  vncStatus.classList.toggle("is-online", running);
  vncStatus.classList.toggle("is-offline", !running);

  if (!vnc?.enabled) {
    vncMessage.textContent = "VNC is disabled in the device config.";
    vncOverlay.classList.add("is-visible");
    return;
  }

  if (running) {
    const url = buildNoVncUrl(vnc);
    openVnc.href = url;
    if (vncFrame.dataset.src !== url) {
      vncFrame.src = url;
      vncFrame.dataset.src = url;
    }
    vncOverlay.classList.remove("is-visible");
    return;
  }

  const details = vnc?.errors?.length ? vnc.errors.join(" / ") : "Start VNC to prepare the desktop session.";
  vncMessage.textContent = details;
  vncOverlay.classList.add("is-visible");
}

async function refreshStatus() {
  const payload = await request("/api/status");
  state.device = payload.device;
  state.runtime = payload.runtime;

  deviceName.textContent = payload.device.device_name;
  deviceMeta.textContent = `${payload.device.device_id} - hotspot ${payload.device.hotspot.ssid} - ${window.location.hostname}:8080`;
  renderVncStatus(payload.runtime.vnc);
}

async function startVnc() {
  const payload = await request("/api/vnc/start", {
    method: "POST",
    body: JSON.stringify({}),
  });
  state.runtime = {
    ...(state.runtime || {}),
    vnc: payload,
  };
  renderVncStatus(payload);
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

async function ensureTerminal() {
  if (!state.terminal.sessionId) {
    await createTerminal();
  }
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
  await ensureTerminal();
  await request(`/api/terminal/session/${state.terminal.sessionId}/input`, {
    method: "POST",
    body: JSON.stringify({ input: `${command}\n` }),
  });
  terminalInput.value = "";
}

document.querySelectorAll(".tab-button").forEach((button) => {
  button.addEventListener("click", () => {
    setActiveTab(button.dataset.tabTarget);
  });
});

document.querySelector("#start-vnc").addEventListener("click", () => {
  startVnc()
    .then(() => refreshStatus())
    .catch((error) => {
      console.error(error);
      vncMessage.textContent = "Failed to start VNC.";
      vncOverlay.classList.add("is-visible");
    });
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

Promise.all([refreshStatus(), ensureTerminal()])
  .then(() => {
    setActiveTab(state.activeTab);
  })
  .catch((error) => console.error(error));

setInterval(() => {
  refreshStatus().catch((error) => console.error(error));
}, 3000);
