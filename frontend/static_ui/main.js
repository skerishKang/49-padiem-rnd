const apiBaseInput = document.getElementById("apiBase");
const pollIntervalInput = document.getElementById("pollInterval");
const maxPollsInput = document.getElementById("maxPolls");
const logView = document.getElementById("log");

const inputMediaPath = document.getElementById("inputMediaPath");
const outputAudioPath = document.getElementById("outputAudioPath");
const audioConfigPath = document.getElementById("audioConfigPath");
const audioAsync = document.getElementById("audioAsync");
const audioStatus = document.getElementById("audioStatus");

declareStepHandlers();

function declareStepHandlers() {
  bindStep("runAudio", audioStatus, async () => ({
    endpoint: "audio/extract",
    payload: {
      input_media: inputMediaPath.value,
      output_audio: outputAudioPath.value,
      config: normalizePath(audioConfigPath.value),
    },
    asyncMode: audioAsync.checked,
  }));

  bindStep("runSTT", document.getElementById("sttStatus"), async () => ({
    endpoint: "stt/",
    payload: {
      input_audio: document.getElementById("sttInputAudio").value,
      output_json: document.getElementById("sttOutputJson").value,
      config: normalizePath(document.getElementById("sttConfigPath").value),
    },
    asyncMode: document.getElementById("sttAsync").checked,
  }));

  bindStep("runText", document.getElementById("textStatus"), async () => ({
    endpoint: "text/process",
    payload: {
      input_json: document.getElementById("textInputJson").value,
      output_json: document.getElementById("textOutputJson").value,
      config: normalizePath(document.getElementById("textConfigPath").value),
    },
    asyncMode: document.getElementById("textAsync").checked,
  }));

  bindStep("runTTS", document.getElementById("ttsStatus"), async () => ({
    endpoint: "tts/",
    payload: {
      input_json: document.getElementById("ttsInputJson").value,
      output_audio: document.getElementById("ttsOutputAudio").value,
      config: normalizePath(document.getElementById("ttsConfigPath").value),
    },
    asyncMode: document.getElementById("ttsAsync").checked,
  }));

  bindStep("runXTTS", document.getElementById("xttsStatus"), async () => ({
    endpoint: "tts-backup/",
    payload: {
      input_json: document.getElementById("xttsInputJson").value,
      output_audio: document.getElementById("xttsOutputAudio").value,
      config: normalizePath(document.getElementById("xttsConfigPath").value),
    },
    asyncMode: document.getElementById("xttsAsync").checked,
  }));

  bindStep("runRVC", document.getElementById("rvcStatus"), async () => ({
    endpoint: "rvc/",
    payload: {
      input_audio: document.getElementById("rvcInputAudio").value,
      output_audio: document.getElementById("rvcOutputAudio").value,
      config: normalizePath(document.getElementById("rvcConfigPath").value),
    },
    asyncMode: document.getElementById("rvcAsync").checked,
  }));

  bindStep("runLipsync", document.getElementById("lipsyncStatus"), async () => ({
    endpoint: "lipsync/",
    payload: {
      input_video: document.getElementById("lipsyncInputVideo").value,
      input_audio: document.getElementById("lipsyncInputAudio").value,
      output_video: document.getElementById("lipsyncOutputVideo").value,
      config: normalizePath(document.getElementById("lipsyncConfigPath").value),
    },
    asyncMode: document.getElementById("lipsyncAsync").checked,
  }));

  const pipelineStatus = document.getElementById("pipelineStatus");
  document.getElementById("runPipeline").addEventListener("click", async () => {
    pipelineStatus.textContent = "전체 파이프라인 실행 중...";
    try {
      const steps = [
        () => ({
          endpoint: "audio/extract",
          payload: {
            input_media: document.getElementById("pipelineInput").value,
            output_audio: outputAudioPath.value,
            config: normalizePath(audioConfigPath.value),
          },
        }),
        () => ({
          endpoint: "stt/",
          payload: {
            input_audio: document.getElementById("sttInputAudio").value,
            output_json: document.getElementById("sttOutputJson").value,
            config: normalizePath(document.getElementById("sttConfigPath").value),
          },
        }),
        () => ({
          endpoint: "text/process",
          payload: {
            input_json: document.getElementById("textInputJson").value,
            output_json: document.getElementById("textOutputJson").value,
            config: normalizePath(document.getElementById("textConfigPath").value),
          },
        }),
        () => ({
          endpoint: "tts/",
          payload: {
            input_json: document.getElementById("ttsInputJson").value,
            output_audio: document.getElementById("ttsOutputAudio").value,
            config: normalizePath(document.getElementById("ttsConfigPath").value),
          },
        }),
        () => ({
          endpoint: "rvc/",
          payload: {
            input_audio: document.getElementById("rvcInputAudio").value,
            output_audio: document.getElementById("rvcOutputAudio").value,
            config: normalizePath(document.getElementById("rvcConfigPath").value),
          },
        }),
        () => ({
          endpoint: "lipsync/",
          payload: {
            input_video: document.getElementById("lipsyncInputVideo").value,
            input_audio: document.getElementById("lipsyncInputAudio").value,
            output_video: document.getElementById("lipsyncOutputVideo").value,
            config: normalizePath(document.getElementById("lipsyncConfigPath").value),
          },
        }),
      ];

      for (const stepFn of steps) {
        const { endpoint, payload } = stepFn();
        pipelineStatus.textContent = `${endpoint} 실행 중...`;
        const result = await executeStep(endpoint, payload, false);
        if (!result) {
          throw new Error(`${endpoint} 단계 실패`);
        }
      }

      pipelineStatus.textContent = "전체 파이프라인 완료";
    } catch (err) {
      pipelineStatus.textContent = "오류가 발생했습니다.";
      appendLog("파이프라인 오류", { error: String(err) });
    }
  });
}

function bindStep(buttonId, statusEl, buildRequest) {
  const button = document.getElementById(buttonId);
  button.addEventListener("click", async () => {
    statusEl.textContent = "실행 중...";
    try {
      const { endpoint, payload, asyncMode } = await buildRequest();
      await executeStep(endpoint, payload, Boolean(asyncMode));
      statusEl.textContent = "완료되었습니다.";
    } catch (err) {
      statusEl.textContent = "오류가 발생했습니다.";
      appendLog(`${buttonId} 오류`, { error: String(err) });
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
  const effectivePayload = { ...payload };
  if (asyncMode) {
    effectivePayload.async_run = true;
  }

  const response = await callApi(endpoint, effectivePayload);

  if (asyncMode && response.job_id) {
    const jobId = response.job_id;
    appendLog("작업이 큐에 등록되었습니다.", { jobId });

    const maxPolls = Number(maxPollsInput.value || 10);
    const interval = Number(pollIntervalInput.value || 1) * 1000;

    let jobResult = null;
    for (let i = 0; i < maxPolls; i++) {
      await new Promise((resolve) => setTimeout(resolve, interval));
      jobResult = await getJobStatus(jobId);
      if (jobResult.status === "success" || jobResult.status === "failed") {
        break;
      }
    }

    appendLog("작업 결과", jobResult);
    return jobResult;
  }

  appendLog("응답", response);
  return response;
}

function normalizePath(value) {
  const trimmed = (value || "").trim();
  return trimmed.length ? trimmed : null;
}
