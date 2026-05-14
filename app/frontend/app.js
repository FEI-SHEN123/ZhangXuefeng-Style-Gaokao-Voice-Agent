const conversation = document.getElementById("conversation");
const statusEl = document.getElementById("status");
const textForm = document.getElementById("textForm");
const textInput = document.getElementById("textInput");
const sendButton = document.getElementById("sendButton");
const recordButton = document.getElementById("recordButton");

let audioContext = null;
let mediaStream = null;
let sourceNode = null;
let processorNode = null;
let recordedChunks = [];
let recordingSampleRate = 16000;
const targetSampleRate = 8000;
let isRecording = false;
let history = [];

renderEmpty();

function setStatus(text) {
  statusEl.textContent = text;
}

function setBusy(isBusy) {
  sendButton.disabled = isBusy;
  recordButton.disabled = isBusy && !isRecording;
}

function renderEmpty() {
  if (history.length === 0) {
    conversation.innerHTML = '<div class="empty">点击录音，或直接输入文字开始。</div>';
  }
}

function addMessage(role, text, audioBase64 = null, audioMime = "audio/wav") {
  if (conversation.querySelector(".empty")) {
    conversation.innerHTML = "";
  }

  const node = document.createElement("article");
  node.className = `message ${role}`;

  const label = document.createElement("span");
  label.className = "label";
  label.textContent = role === "user" ? "你" : "AI 咨询";

  const content = document.createElement("div");
  content.textContent = text;

  node.append(label, content);

  if (audioBase64) {
    const audio = document.createElement("audio");
    audio.controls = true;
    audio.autoplay = true;
    audio.src = `data:${audioMime};base64,${audioBase64}`;
    node.append(audio);
  }

  conversation.append(node);
  conversation.scrollTop = conversation.scrollHeight;
}

function speakWithBrowser(text) {
  if (!("speechSynthesis" in window)) return;
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = "zh-CN";
  utterance.rate = 1.18;
  utterance.pitch = 0.9;
  window.speechSynthesis.speak(utterance);
}

function pushHistory(userText, assistantText) {
  history.push({ role: "user", content: userText });
  history.push({ role: "assistant", content: assistantText });
  history = history.slice(-12);
}

async function handleResponse(response) {
  const data = await response.json();
  if (!response.ok) {
    const detail = data.detail || "请求失败";
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }

  addMessage("user", data.transcript);
  addMessage("assistant", data.reply, data.audio_base64, data.audio_mime || "audio/wav");
  if (!data.audio_base64 && data.audio_fallback === "browser-speech") {
    speakWithBrowser(data.reply);
  }
  pushHistory(data.transcript, data.reply);
}

textForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const text = textInput.value.trim();
  if (!text) return;

  setBusy(true);
  setStatus("生成中");

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, history }),
    });
    textInput.value = "";
    await handleResponse(response);
    setStatus("完成");
  } catch (error) {
    setStatus("出错");
    addMessage("assistant", `出错了：${error.message}`);
  } finally {
    setBusy(false);
  }
});

recordButton.addEventListener("click", async () => {
  if (isRecording) {
    stopRecording();
    return;
  }

  try {
    mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
    audioContext = new AudioContext();
    recordingSampleRate = audioContext.sampleRate;
    sourceNode = audioContext.createMediaStreamSource(mediaStream);
    processorNode = audioContext.createScriptProcessor(4096, 1, 1);
    recordedChunks = [];

    processorNode.onaudioprocess = (event) => {
      const input = event.inputBuffer.getChannelData(0);
      recordedChunks.push(new Float32Array(input));
    };

    sourceNode.connect(processorNode);
    processorNode.connect(audioContext.destination);
    isRecording = true;
    recordButton.classList.add("recording");
    recordButton.textContent = "停止录音";
    setStatus("录音中");
  } catch (error) {
    setStatus("麦克风失败");
    addMessage("assistant", `无法使用麦克风：${error.message}`);
  }
});

async function stopRecording() {
  isRecording = false;
  recordButton.classList.remove("recording");
  recordButton.textContent = "开始录音";
  setBusy(true);
  setStatus("识别中");

  try {
    if (processorNode) processorNode.disconnect();
    if (sourceNode) sourceNode.disconnect();
    if (mediaStream) mediaStream.getTracks().forEach((track) => track.stop());
    if (audioContext) await audioContext.close();

    const wavBlob = encodeWav(recordedChunks, recordingSampleRate, targetSampleRate);
    const formData = new FormData();
    formData.append("audio", wavBlob, "recording.wav");
    formData.append("history_json", JSON.stringify(history));

    const response = await fetch("/api/voice-chat", {
      method: "POST",
      body: formData,
    });
    await handleResponse(response);
    setStatus("完成");
  } catch (error) {
    setStatus("出错");
    addMessage("assistant", `出错了：${error.message}`);
  } finally {
    setBusy(false);
    audioContext = null;
    mediaStream = null;
    sourceNode = null;
    processorNode = null;
    recordedChunks = [];
  }
}

function encodeWav(chunks, inputSampleRate, outputSampleRate) {
  const totalLength = chunks.reduce((sum, chunk) => sum + chunk.length, 0);
  const samples = new Float32Array(totalLength);
  let offset = 0;
  for (const chunk of chunks) {
    samples.set(chunk, offset);
    offset += chunk.length;
  }

  const resampled = resample(samples, inputSampleRate, outputSampleRate);
  const buffer = new ArrayBuffer(44 + resampled.length * 2);
  const view = new DataView(buffer);

  writeString(view, 0, "RIFF");
  view.setUint32(4, 36 + resampled.length * 2, true);
  writeString(view, 8, "WAVE");
  writeString(view, 12, "fmt ");
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, 1, true);
  view.setUint32(24, outputSampleRate, true);
  view.setUint32(28, outputSampleRate * 2, true);
  view.setUint16(32, 2, true);
  view.setUint16(34, 16, true);
  writeString(view, 36, "data");
  view.setUint32(40, resampled.length * 2, true);

  floatTo16BitPcm(view, 44, resampled);
  return new Blob([view], { type: "audio/wav" });
}

function resample(input, inputSampleRate, outputSampleRate) {
  if (inputSampleRate === outputSampleRate) return input;
  const ratio = inputSampleRate / outputSampleRate;
  const outputLength = Math.floor(input.length / ratio);
  const output = new Float32Array(outputLength);

  for (let i = 0; i < outputLength; i += 1) {
    const sourceIndex = i * ratio;
    const left = Math.floor(sourceIndex);
    const right = Math.min(left + 1, input.length - 1);
    const weight = sourceIndex - left;
    output[i] = input[left] * (1 - weight) + input[right] * weight;
  }

  return output;
}

function floatTo16BitPcm(view, offset, input) {
  for (let i = 0; i < input.length; i += 1, offset += 2) {
    const sample = Math.max(-1, Math.min(1, input[i]));
    view.setInt16(offset, sample < 0 ? sample * 0x8000 : sample * 0x7fff, true);
  }
}

function writeString(view, offset, string) {
  for (let i = 0; i < string.length; i += 1) {
    view.setUint8(offset + i, string.charCodeAt(i));
  }
}
