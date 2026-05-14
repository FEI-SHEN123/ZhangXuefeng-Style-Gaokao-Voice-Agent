# 语音咨询 MVP

这个项目跑通：

```text
录音 -> 阿里百炼 Paraformer 语音识别 -> Qwen 生成回复 -> 阿里百炼 TTS 合成 -> 浏览器播放
```

默认 TTS 使用 `sambert-zhida-v1`。如果你已经在阿里百炼创建了自己的复刻音色，可以切换到 `dashscope_cloned` 使用自己的声音。

## 启动

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

编辑 `.env`，填入：

```text
DASHSCOPE_API_KEY=你的阿里云百炼 API Key（只需要填写这个便可以运行基础版）
```

启动：

```powershell
python -m uvicorn app.backend.main:app --host 127.0.0.1 --port 8000
```

打开：

```text
http://127.0.0.1:8000
```

## 默认配置

```text
DASHSCOPE_API_KEY=你的阿里云百炼 API Key
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen3.5-flash

ASR_PROVIDER=dashscope
ASR_MODEL=paraformer-realtime-8k-v2

TTS_PROVIDER=dashscope
TTS_MODEL=sambert-zhida-v1
TTS_VOICE=sambert-zhida-v1

ZHANG_SKILL_PATH=SKILL.md
```

当前本地录音直传方案使用 `paraformer-realtime-8k-v2`。`paraformer-v2` 是录音文件转写模型，通常需要公网音频 URL；这个 MVP 不接 OSS 上传，所以不使用它。

## 使用自己的复刻声音

只复刻你自己的声音，或你明确获得授权的声音。页面里保留“AI 生成”的披露，不要把输出伪装成真人实时发言。

录音建议：

- 安静环境，普通话，自然语速。
- 录 10-30 秒。
- WAV 或 MP3，单人声音，不要背景音乐。
- 内容随意，但要连续、清楚，避免长时间停顿。
- 上传到 OSS 或任意公网可访问 URL，确保阿里百炼服务器能直接下载。

在 `.env` 里先填：

```text
VOICE_CLONE_AUDIO_URL=https://your-public-audio-url.wav
VOICE_CLONE_PREFIX=myvoice
```

创建复刻音色：

```powershell
.\.venv\Scripts\Activate.ps1
python scripts/create_dashscope_voice.py
```

脚本会输出：

```text
voice_id=...
```

把返回的 `voice_id` 写入 `.env`，并切换 TTS：

```text
TTS_PROVIDER=dashscope_cloned
TTS_MODEL=cosyvoice-v3.5-flash
TTS_VOICE_ID=脚本返回的 voice_id
```

重启服务后，文字输入和录音输入的回复都会使用你的复刻音色朗读。

## 关键文件

- `app/backend/services/tts.py`：Sambert 和复刻音色 TTS 分支。
- `scripts/create_dashscope_voice.py`：调用阿里百炼声音复刻 API 创建 `voice_id`。
- `app/backend/services/asr.py`：Paraformer 实时识别。

## 购买和开通

1. 打开阿里云百炼控制台：`https://bailian.console.aliyun.com/`
2. 开通百炼 / DashScope 模型服务。
3. 创建 API Key，写入 `.env` 的 `DASHSCOPE_API_KEY`。
4. 如需复刻声音，额外开通 CosyVoice 声音复刻相关服务。

官方参考：

- 阿里声音复刻 API：<https://help.aliyun.com/zh/model-studio/voice-clone-design-http-api>
- 阿里实时语音合成：<https://www.alibabacloud.com/help/zh/model-studio/text-to-speech>

## 限制

- 仍是一问一答模式，不是实时电话式对话。
- 没有自动上传 OSS；复刻录音 URL 需要你手动准备。
- 没有实时搜索。涉及院校、分数线、就业、薪资、政策时，模型会被要求不要编造数据，先追问关键条件。
