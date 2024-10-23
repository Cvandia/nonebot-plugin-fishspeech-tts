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
| tts_is_to_me | bool | No | True | Whether to respond only when mentioned |
| tts_audio_path | str | No | "./data/reference_audio" | Path for voice samples, defaults to "./data/reference_audio" |

**Note:** The file name format for reference audio should be: `[Character Name]Text Label.[Audio Extension]`

**! Supports different voices for the same character!**

**Currently supported audio extensions are detailed in [files.py](./nonebot_plugin_fishspeech_tts/files.py) under `AUDIO_FILE_SUFFIX`.**

---

If you want to use the official API, set the configuration item `tts_is_online` to `True` and configure the following:

| Configuration Item | Type | Required | Default Value | Description |
|:-----:|:----:|:----:|:---:|:----:|
| online_authorization | str | Yes | "xxxxx" | API key for official authorization, see [link](https://fish.audio/zh-CN/go-api/api-keys/) |
| online_model_first | bool | No | True | Set this to `False` if you want to call the official model with your reference audio to customize character voice; if you don't have reference audio, it will call existing voices from the official website. See [link](https://fish.audio/zh-CN/) for details. |

---

If you want to use a [self-hosted](#offline-setup-fish-speech) or other [fish-speech](https://github.com/fishaudio/fish-speech) project APIs, set the configuration item `tts_is_online` to `False` and configure the following:

| Configuration Item | Type | Required | Default Value | Description |
|:----:|:----:|:----:|:---:|:----:|
| offline_api_url | str | Yes | "http://127.0.0.1:8080" | Your `fish-speech` API address |

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

### Brief Tutorial for Offline Setup

**Prepare `fish-speech`:**
1. Clone the `fish-speech` repository locally:
```bash
git clone https://github.com/fishaudio/fish-speech
```
2. Run `install_env.bat` to set up the virtual environment and required dependencies.
3. Run `start.bat` for the initial startup.
4. Modify `API_FLAGS.txt` and restart.

**Start API Service:**
1. Modify `API_FLAGS.txt` to uncomment (remove `#`) in front of `api`:
```
# --infer
--api
--listen 0.0.0.0:8080 \ # Listening interface
...
```

**Add Additional Parameters in `API_FLAGS.txt`:**
1. `--compile` -> Whether to start the compiled model (faster TTS generation but slower startup).
2. `--workers <number>` -> Start `<number>` of concurrent processes (must set, as default one can easily block).
3. More details can be found in the [official documentation](https://speech.fish.audio/zh).