<div align="center">

# nonebot-plugin-fishspeech-tts

<a href="https://v2.nonebot.dev/store"><img src="https://count.getloli.com/get/@nonebot-plugin-fishspeech-tts?theme=asoul"></a>

_⭐ A TTS plugin based on Nonebot2 that calls online [fish-audio](https://fish.audio/zh-CN/) or offline [fish-speech](https://github.com/fishaudio/fish-speech) APIs ⭐_
_⭐Text-to-speech `tts` plugin⭐_

<a href="https://www.python.org/downloads/release/python-390/"><img src="https://img.shields.io/badge/python-3.10+-blue"></a>  <a href=""><img src="https://img.shields.io/badge/QQ-1141538825-yellow"></a> <a href="https://github.com/Cvandia/nonebot-plugin-game-torrent/blob/main/LICENCE"><img src="https://img.shields.io/badge/license-MIT-blue"></a> <a href="https://v2.nonebot.dev/"><img src="https://img.shields.io/badge/Nonebot2-2.2.0+-red"></a>

[**简体中文**](../README.md) | **English**
</div>

---

## ⭐ Introduction

**With just a 5-second voice sample, you can ~~perfectly~~ excellently clone the original voice!**
Simply prepare the voice of the character you wish to clone, label the voice file (see below), and you can quickly generate speech.

> Alternatively, use the official online API -> [fish-audio](https://fish.audio/zh-CN/) for fast cloud-based speech generation.

## 📜 Disclaimer

> [!note]
> This plugin is for **learning** and **research** purposes only. Users must assume all risks associated with using the plugin. The author is not responsible for any losses or issues arising from the use of the plugin. Please use the plugin responsibly and **comply with relevant laws and regulations.**
Using **this plugin indicates that you have read and agree to the above disclaimer**. If you do not agree or cannot comply with the above statement, please do not use this plugin.

## 💿 Installation

<details>
<summary>installation</summary>

**Using `pipx`:**
```bash
pipx install nonebot-plugin-fishspeech-tts -U
```
> [!note] Add this plugin to the `plugins = ["xxx"]` section in `pyproject.toml`.

**Using `nb-cli`:**
```bash
nb plugin install nonebot-plugin-fishspeech-tts -U
```

**Using `git clone` (not recommended):**
- Run the following command in the command prompt:
```bash
git clone https://github.com/Cvandia/nonebot-plugin-fishspeech-tts
```
- Copy the `nonebot-plugin-fishspeech-tts` folder to the `src/plugins` directory in the bot's root directory (or another name you used when creating the bot).
 </details>

 <details>
 <summary>note</summary>

Recommended mirror sites for download:

- Tsinghua Source: `https://pypi.tuna.tsinghua.edu.cn/simple`
- Alibaba Source: `https://mirrors.aliyun.com/pypi/simple/`

</details>

## ⚙️ Configuration

**Add the following configurations to `.env`:**

| Basic Configuration | Type | Required | Default Value | Description |
|:-----:|:----:|:----:|:---:|:----:|
| tts_is_online | bool | Yes | True | Whether to use the cloud API |
| tts_chunk_length | literal | No | "normal" | Audio chunk length for requests, defaults to normal; options: short, normal, long |
| tts_max_new_tokens | int or None | No | None | Per-chunk token limit; omit to use server defaults |
| tts_prefix | str or None | No | None | Command prefix |
| tts_audio_path | str | No | "./data/参考音频" | Path for voice samples, defaults to "./data/参考音频" |

**Note:** The file name format for reference audio should be: `[Character Name]Text Label.[Audio Extension]`

**! Supports different voices for the same character!**

**Currently supported audio extensions are detailed in [files.py](./nonebot_plugin_fishspeech_tts/files.py) under `AUDIO_FILE_SUFFIX`.**

---

If you want to use the official API, set the configuration item `tts_is_online` to `True` and configure the following:

| Configuration Item | Type | Required | Default Value | Description |
|:-----:|:----:|:----:|:---:|:----:|
| online_authorization | str | Yes | None | API key for official authorization, see [link](https://fish.audio/zh-CN/go-api/api-keys/) |
| online_model_first | bool | No | True | Set this to `False` if you want to call the official model with your reference audio to customize character voice; if you don't have reference audio, it will call existing voices from the official website. See [link](https://fish.audio/zh-CN/) for details. |

---

If you want to use a [self-hosted](#self-hosted-api) or other [fish-speech](https://github.com/fishaudio/fish-speech) project APIs, set the configuration item `tts_is_online` to `False` and configure the following:

| Configuration Item | Type | Required | Default Value | Description |
|:----:|:----:|:----:|:---:|:----:|
| offline_api_url | str | Yes | "http://127.0.0.1:8080" | Your `fish-speech` API address |

## Current API compatibility (2026-10-19)

- Cloud base URL: `https://api.fish.audio`. `POST /v1/tts` takes a `model` header; set `online_model` (default `s2.1-pro`) to `s2-pro`, `s2.1-pro-free`, `drama-3`, or the deprecated `s1` as needed. The default uses paid API credit; free-tier availability and limits are determined by Fish Audio.
- `online_language` (optional, e.g. `zh-CN`) controls text normalization, not the voice or accent. Bracket directions in synthesis text are preserved.
- `online_reference_ids={"Speaker":"voice-id"}` avoids title search when `online_model_first=True`. Reference voice IDs are different from base model names.
- Cloud reference audio uses MessagePack; voice-ID requests use JSON. HTTP errors, invalid content types and empty responses cannot be sent as audio.
- `offline_api_url` now defaults to `http://127.0.0.1:8080`. Set `offline_authorization` if the server uses `--api-key`; `offline_reference_ids` maps names to server-side saved references.
- Local model weights are selected when starting the server. `offline_single_chunk=True` enables Drama 3 single-chunk generation. Leave it False for other models.
- Omit `tts_max_new_tokens` to use server defaults; explicit existing values still apply. `tts_is_stream` requests local streaming WAV, but the plugin collects the complete response before sending a voice message.
- `speech-1.5` and `speech-1.6` are retired; `s1` retires on December 31, 2026. Keep explicit URL/port settings for deployments using the old defaults.

Sources: [TTS API](https://docs.fish.audio/api-reference/endpoint/openapi-v1/text-to-speech), [changelog](https://docs.fish.audio/developer-guide/getting-started/changelog), [local schema](https://github.com/fishaudio/fish-speech/blob/main/fish_speech/utils/schema.py).

## ⭐ Usage

> [!note]
> Please pay attention to your `COMMAND_START` and the above configuration items.

### Commands:

| Command | Requires @ | Scope | Description | Permissions |
|:---:|:---:|:---:|:---:|:---:|
| xxx says xxx | Based on configuration | all | TTS speech generation | all |
| Voice list | Yes | all | Retrieve all character lists | all |
| Voice balance | Yes | all | Check API balance | all |

## 🌙 Future
- No plans at the moment.
If you like it, remember to give it a star ⭐

## 💝 Special Thanks

- [x] [nonebot2](https://github.com/nonebot/nonebot2): The foundation of this project, a very useful chatbot framework.
- [x] [fish-speech](https://github.com/fishaudio/fish-speech): Zero-shot & few-shot TTS: Generate high-quality TTS output with just 10 to 30 seconds of voice samples.

## ⭐ Additional Help

### Self-hosted API

Follow the upstream [installation](https://github.com/fishaudio/fish-speech/blob/main/docs/en/install.md) and [server](https://github.com/fishaudio/fish-speech/blob/main/docs/en/server.md) guides. After downloading S2-Pro weights:

```bash
python tools/api_server.py --llama-checkpoint-path checkpoints/s2-pro --decoder-checkpoint-path checkpoints/s2-pro/codec.pth --listen 127.0.0.1:8080
```

Check `GET /v1/health`, configure `tts_is_online=False`, and provide local reference audio or `offline_reference_ids`. No cloud `model` header is sent to self-hosted servers.

### Tests

Run `uv venv`, `uv pip install -e . --group dev`, then `uv run --no-project pytest -q`. Tests use mocked HTTP responses and do not require API credentials or perform billed synthesis.
