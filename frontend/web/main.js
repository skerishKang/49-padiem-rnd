const apiBaseInput = document.getElementById("apiBase");
const pollIntervalInput = document.getElementById("pollInterval");
const maxPollsInput = document.getElementById("maxPolls");
const logView = document.getElementById("log");

const presetMeta = {
  videoPresets: { label: "영상 경로 프리셋", hint: "버튼을 클릭하면 입력칸이 즉시 채워집니다." },
  audioPresets: { label: "오디오 경로 프리셋", hint: "필요한 파일 경로를 한 번에 불러오세요." },
  jsonPresets: { label: "JSON 경로 프리셋", hint: "STT/텍스트 처리 결과 경로를 빠르게 선택합니다." },
  configPresets: { label: "설정 파일 프리셋", hint: "대표 설정 파일을 클릭해서 적용하세요." },
};

const stepConfig = {
  audio: {
    button: "runAudio",
    status: "audioStatus",
    async: "audioAsync",
    payload: () => ({
      input_media: document.getElementById("audioInputMedia").value,
      output_audio: document.getElementById("audioOutputPath").value,
      config: normalizePath(document.getElementById("audioConfigPath").value),
    }),
    endpoint: "audio/extract",
  },
  stt: {
    button: "runStt",
    status: "sttStatus",
    async: "sttAsync",
    payload: () => ({
      input_audio: document.getElementById("sttInputAudio").value,
      output_json: document.getElementById("sttOutputJson").value,
      config: normalizePath(document.getElementById("sttConfigPath").value),
    }),
    endpoint: "stt/",
  },
  text: {
    button: "runText",
    status: "textStatus",
    async: "textAsync",
    payload: () => {
      const payload = {
        input_json: document.getElementById("textInputJson").value,
        output_json: document.getElementById("textOutputJson").value,
        config: normalizePath(document.getElementById("textConfigPath").value),
        target_language: document.getElementById("textTargetLang").value,
      };
      const sourceLang = document.getElementById("textSourceLang").value;
      if (sourceLang !== "auto") {
        payload.source_language = sourceLang;
      }
      return payload;
    },
    endpoint: "text/process",
  },
  tts: {
    button: "runTts",
    status: "ttsStatus",
    async: "ttsAsync",
    payload: () => ({
      input_json: document.getElementById("ttsInputJson").value,
      output_audio: document.getElementById("ttsOutputAudio").value,
      config: normalizePath(document.getElementById("ttsConfigPath").value),
    }),
    endpoint: "tts/",
  },
  xtts: {
    button: "runXtts",
    status: "xttsStatus",
    async: "xttsAsync",
    payload: () => ({
      input_json: document.getElementById("xttsInputJson").value,
      output_audio: document.getElementById("xttsOutputAudio").value,
      config: normalizePath(document.getElementById("xttsConfigPath").value),
    }),
    endpoint: "tts-backup/",
  },
  rvc: {
    button: "runRvc",
    status: "rvcStatus",
    async: "rvcAsync",
    payload: () => ({
      input_audio: document.getElementById("rvcInputAudio").value,
      output_audio: document.getElementById("rvcOutputAudio").value,
      config: normalizePath(document.getElementById("rvcConfigPath").value),
    }),
    endpoint: "rvc/",
  },
  lipsync: {
    button: "runLipsync",
    status: "lipsyncStatus",
    async: "lipsyncAsync",
    payload: () => ({
      input_video: document.getElementById("lipsyncInputVideo").value,
      input_audio: document.getElementById("lipsyncInputAudio").value,
      output_video: document.getElementById("lipsyncOutputVideo").value,
      config: normalizePath(document.getElementById("lipsyncConfigPath").value),
    }),
    endpoint: "lipsync/",
  },
};

Object.values(stepConfig).forEach((step) => {
  bindStep(step);
});

initPresetPanels();
enhanceFieldInputs();
setupPresetDropdownClosers();
initOutputSync();
initAudioPreview();

document.getElementById("runPipeline").addEventListener("click", async () => {
  const status = document.getElementById("pipelineStatus");
  status.textContent = "전체 파이프라인 실행 중...";
  try {
    const chain = ["audio", "stt", "text", "tts", "rvc", "lipsync"];
    for (const key of chain) {
      const step = stepConfig[key];
      status.textContent = `${step.endpoint} 실행 중...`;
      const payload = step.payload();
      const result = await executeStep(step.endpoint, payload, false);
      if (!result) throw new Error(`${step.endpoint} 실패`);
    }
    status.textContent = "전체 파이프라인 완료";
  } catch (err) {
    status.textContent = "오류가 발생했습니다.";
    appendLog("파이프라인 오류", { error: String(err) });
  }
});

function initPresetPanels() {
  const panels = document.querySelectorAll(".preset-panel");
  panels.forEach((panel) => {
    if (panel.dataset.ready === "true") return;
    const datalistId = panel.dataset.preset;
    const targetId = panel.dataset.target;
    const datalist = document.getElementById(datalistId);
    if (!datalist) return;

    const { label, hint } = presetMeta[datalistId] || {
      label: "경로 프리셋",
      hint: "원하는 경로 버튼을 클릭해 입력칸을 채워주세요.",
    };

    panel.replaceChildren();

    const info = document.createElement("div");
    info.className = "preset-panel-info";
    info.innerHTML = `<strong>📁 ${label}</strong><span>${hint}</span>`;

    const grid = document.createElement("div");
    grid.className = "preset-cell-grid";

    Array.from(datalist.options).forEach((opt) => {
      if (!opt.value) return;
      const cell = document.createElement("button");
      cell.type = "button";
      cell.className = "preset-cell";
      cell.innerHTML = `<span class="preset-cell-text">${opt.value}</span>`;
      cell.addEventListener("click", () => {
        const target = document.getElementById(targetId);
        if (target) {
          target.value = opt.value;
        }
      });
      grid.appendChild(cell);
    });

    panel.appendChild(info);
    panel.appendChild(grid);
    panel.dataset.ready = "true";
  });
}

function enhanceFieldInputs() {
  const containers = document.querySelectorAll(".field-with-presets");
  containers.forEach((container) => {
    if (container.dataset.enhanced === "true") return;
    const input = container.querySelector(".field-input");
    const panel = container.querySelector(".preset-panel");
    if (!input || !panel) return;

    container.dataset.enhanced = "true";
    container.classList.add("field-with-enhancer");

    const shell = document.createElement("div");
    shell.className = "field-input-shell";
    container.insertBefore(shell, input);
    shell.appendChild(input);

    const toggle = document.createElement("button");
    toggle.type = "button";
    toggle.className = "preset-toggle";
    toggle.setAttribute("aria-expanded", "false");
    toggle.setAttribute("aria-label", "프리셋 드롭다운 토글");
    toggle.innerHTML = "프리셋";
    shell.appendChild(toggle);

    const applyOpenState = (open) => setPresetOpenState(container, toggle, open);

    toggle.addEventListener("click", (event) => {
      event.stopPropagation();
      const willOpen = !container.classList.contains("preset-open");
      closePresetDropdowns(container);
      applyOpenState(willOpen);
    });

    applyOpenState(true);

    // 출력 경로 필드에는 드롭존을 추가하지 않음
    if (input.id.toLowerCase().includes("output")) {
      return;
    }

    const dropzone = document.createElement("div");
    dropzone.className = "dropzone";
    dropzone.setAttribute("role", "button");
    dropzone.setAttribute("tabindex", "0");
    dropzone.innerHTML = `
      <div class="dropzone-face">
        <strong>파일 드래그 & 드롭</strong>
        <span>탐색기에서 경로를 끌어오거나 붙여넣으면 자동 입력됩니다.</span>
      </div>
      <div class="dropzone-feedback" aria-live="polite"></div>
    `;
    container.insertBefore(dropzone, panel);
    setupDropzone(dropzone, input);
  });
}

function setupPresetDropdownClosers() {
  document.addEventListener("click", () => closePresetDropdowns());
  document.addEventListener("keyup", (event) => {
    if (event.key === "Escape") {
      closePresetDropdowns();
    }
  });
}

function closePresetDropdowns(except) {
  document.querySelectorAll(".field-with-presets.preset-open").forEach((container) => {
    if (except && container === except) return;
    const toggle = container.querySelector(".preset-toggle");
    setPresetOpenState(container, toggle, false);
  });
}

function setPresetOpenState(container, toggle, open) {
  container.classList.toggle("preset-open", open);
  if (toggle) {
    toggle.setAttribute("aria-expanded", String(open));
  }
}

function setupDropzone(zone, input) {
  const feedback = zone.querySelector(".dropzone-feedback");
  const listId = input.getAttribute("list");

  const showFeedback = (message, isError = false) => {
    if (feedback) {
      feedback.textContent = message;
      feedback.className = isError ? "dropzone-feedback is-error" : "dropzone-feedback";
    }
    zone.classList.toggle("has-feedback", Boolean(message));
    zone.classList.toggle("is-error", isError);
  };

  const handleFiles = async (files) => {
    if (files.length === 0) return;
    if (files.length > 1) {
      showFeedback("파일은 한 번에 하나만 드롭할 수 있습니다.", true);
      return;
    }
    const file = files[0];
    showFeedback(`'${file.name}' 파일 처리 중...`);

    try {
      const result = await uploadFileToServer(file);
      input.value = result.path;
      showFeedback(`업로드 완료: ${result.path}`);
      input.dispatchEvent(new Event("change", { bubbles: true }));
    } catch (err) {
      showFeedback(err.message, true);
    }
  };

  zone.addEventListener("dragenter", (e) => {
    e.preventDefault();
    zone.classList.add("is-active");
  });
  zone.addEventListener("dragover", (e) => {
    e.preventDefault();
    zone.classList.add("is-active");
  });
  zone.addEventListener("dragleave", (e) => {
    e.preventDefault();
    zone.classList.remove("is-active");
  });
  zone.addEventListener("drop", (e) => {
    e.preventDefault();
    zone.classList.remove("is-active");
    handleFiles(e.dataTransfer.files);
  });
  zone.addEventListener("paste", (e) => {
    handleFiles(e.clipboardData.files);
  });
  zone.addEventListener("click", () => input.click());
  zone.addEventListener("keyup", (e) => {
    if (e.key === "Enter" || e.key === " ") input.click();
  });
}

function initAudioPreview() {
  const outputInput = document.getElementById("audioOutputPath");
  const wrapper = document.getElementById("audioOutputPreviewWrapper");
  const player = document.getElementById("audioOutputPreview");
  const statusEl = document.getElementById("audioPreviewStatus");
  const refreshBtn = document.getElementById("refreshAudioPreview");
  if (!outputInput || !wrapper || !player || !statusEl || !refreshBtn) return;

  const hidePreview = (message) => {
    wrapper.classList.add("is-hidden");
    player.removeAttribute("src");
    player.load();
    statusEl.textContent = message;
  };

  const showPreview = () => {
    wrapper.classList.remove("is-hidden");
  };

  const refreshPreview = () => {
    const rawPath = (outputInput.value || "").trim();
    const path = rawPath.replace(/^@/, ""); // Remove leading '@'
    if (!path) {
      hidePreview("출력 경로가 비어 있어 미리듣기를 사용할 수 없습니다.");
      return;
    }

    showPreview();
    statusEl.textContent = "미리듣기 링크를 준비 중입니다...";
    try {
      const base = apiBaseInput.value.replace(/\/$/, "");
      const url = `${base}/files?path=${encodeURIComponent(path)}`;
      player.src = `${url}&_=${Date.now()}`;
      player.load();
      statusEl.textContent = "재생 버튼을 눌러 바로 확인하세요.";
    } catch (error) {
      console.error(error);
      statusEl.textContent = "미리듣기 URL을 생성하지 못했습니다.";
    }
  };

  refreshBtn.addEventListener("click", (event) => {
    event.preventDefault();
    refreshPreview();
  });

  apiBaseInput.addEventListener("change", refreshPreview);
}

function initOutputSync() {
  const masterInput = document.getElementById("audioInputMedia");
  if (!masterInput) return;

  const syncAll = () => {
    const base = extractStem(masterInput.value);
    if (!base) return;

    const paths = {
      // Step 1 output
      audioOutputPath: `data/runs/${base}_audio.wav`,
      // Step 2 inputs and outputs
      sttInputAudio: `data/runs/${base}_audio.wav`,
      sttOutputJson: `data/runs/${base}_stt_result.json`,
      // Step 3
      textInputJson: `data/runs/${base}_stt_result.json`,
      textOutputJson: `data/runs/${base}_text_processed.json`,
      // Step 4
      ttsInputJson: `data/runs/${base}_text_processed.json`,
      ttsOutputAudio: `data/runs/${base}_tts_output.wav`,
      // Step 5
      xttsInputJson: `data/runs/${base}_text_processed.json`,
      xttsOutputAudio: `data/runs/${base}_xtts_output.wav`,
      // Step 6
      rvcInputAudio: `data/runs/${base}_tts_output.wav`,
      rvcOutputAudio: `data/runs/${base}_rvc_output.wav`,
      // Step 7
      lipsyncInputVideo: masterInput.value,
      lipsyncInputAudio: `data/runs/${base}_rvc_output.wav`,
      lipsyncOutputVideo: `data/runs/${base}_final_dubbed.mp4`,
    };

    for (const id in paths) {
      const el = document.getElementById(id);
      if (el && el.value !== paths[id]) {
        el.value = paths[id];
        el.dispatchEvent(new Event("change", { bubbles: true }));
      }
    }
  };

  masterInput.addEventListener("change", syncAll);
  masterInput.addEventListener("blur", syncAll);
}

function extractStem(path) {
  const normalized = (path || "").trim();
  if (!normalized) return "";
  const filePart = normalized.split(/[\\/]/).pop() || "";
  const stem = filePart.split(".").slice(0, -1).join(".");
  return stem || filePart;
}

function guessPathFromFile(input, fileName, listId) {
  if (!fileName) return "";
  const ext = (fileName.split(".").pop() || "").toLowerCase();

  const mapByList = {
    videoPresets: "data/inputs",
    audioPresets: "data/runs",
    jsonPresets: "data/runs",
    configPresets: "modules",
  };

  const baseByList = mapByList[listId];
  if (baseByList) {
    return `${baseByList}/${fileName}`;
  }

  if (ext === "json") return `data/runs/${fileName}`;
  if (["wav", "mp3", "flac"].includes(ext)) return `data/runs/${fileName}`;
  if (["mp4", "mov", "mkv"].includes(ext)) return `data/inputs/${fileName}`;
  if (fileName.includes("config")) return `modules/${fileName}`;

  if (/input.*video/i.test(input.id)) return `data/inputs/${fileName}`;
  if (/input.*audio/i.test(input.id)) return `data/runs/${fileName}`;
  if (/output/i.test(input.id)) return `data/runs/${fileName}`;

  return fileName;
}

function bindStep(step) {
  const button = document.getElementById(step.button);
  const status = document.getElementById(step.status);
  button.addEventListener("click", async () => {
    status.textContent = "실행 중...";
    try {
      const payload = step.payload();
      const asyncMode = document.getElementById(step.async)?.checked;
      await executeStep(step.endpoint, payload, Boolean(asyncMode));
      status.textContent = "완료되었습니다.";

      if (step.endpoint === "audio/extract") {
        const refreshBtn = document.getElementById("refreshAudioPreview");
        if (refreshBtn) {
          refreshBtn.click();
        }
      }
    } catch (err) {
      status.textContent = "오류가 발생했습니다.";
      appendLog(`${step.endpoint} 오류`, { error: String(err) });
    }
  });
}

function appendLog(message, jsonObj) {
  const time = new Date().toISOString().substring(11, 19);
  let text = `[${time}] ${message}`;
  if (jsonObj) {
    text += "\n" + JSON.stringify(jsonObj, null, 2);
  }
  text += "\n\n";
  logView.textContent = text + logView.textContent;
}

async function callApi(endpoint, payload) {
  const base = apiBaseInput.value.replace(/\/$/, "");
  const url = `${base}/${endpoint.replace(/^\//, "")}`;
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`HTTP ${res.status}: ${text}`);
  }
  return await res.json();
}

async function getJobStatus(jobId) {
  const base = apiBaseInput.value.replace(/\/$/, "");
  const url = `${base}/jobs/${jobId}`;
  const res = await fetch(url);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`상태 조회 실패: ${res.status} ${text}`);
  }
  return await res.json();
}

async function executeStep(endpoint, payload, asyncMode) {
  const effective = { ...payload };
  if (asyncMode) {
    effective.async_run = true;
  }
  const response = await callApi(endpoint, effective);
  if (asyncMode && response.job_id) {
    const jobId = response.job_id;
    appendLog("작업이 큐에 등록되었습니다.", { jobId });
    const max = Number(maxPollsInput.value || 10);
    const interval = Number(pollIntervalInput.value || 1) * 1000;
    for (let i = 0; i < max; i++) {
      await wait(interval);
      const status = await getJobStatus(jobId);
      if (status.status === "success" || status.status === "failed") {
        appendLog("작업 결과", status);
        return status;
      }
    }
    appendLog("작업 결과", { status: "pending" });
    return null;
  }
  appendLog("응답", response);
  return response;
}

async function uploadFileToServer(file, preferredPath) {
  const base = apiBaseInput.value.replace(/\/$/, "");
  const formData = new FormData();
  formData.append("file", file, file.name || "upload.bin");
  if (preferredPath) {
    formData.append("target_path", preferredPath);
  }

  const res = await fetch(`${base}/uploads`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`업로드 실패 (${res.status}): ${text}`);
  }
  return await res.json();
}

function normalizePath(value) {
  const trimmed = (value || "").trim();
  return trimmed.length ? trimmed : null;
}

function wait(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

document.addEventListener("DOMContentLoaded", () => {
  const sttAsyncCheckbox = document.getElementById("sttAsync");
  if (sttAsyncCheckbox) {
    sttAsyncCheckbox.checked = true;
    sttAsyncCheckbox.disabled = true;

    const note = document.createElement("p");
    note.className = "caption";
    note.style.marginTop = "0.5rem";
    note.textContent = "STT는 시간이 오래 걸릴 수 있어 항상 비동기로 실행됩니다.";
    sttAsyncCheckbox.parentElement.insertAdjacentElement("afterend", note);
  }
});