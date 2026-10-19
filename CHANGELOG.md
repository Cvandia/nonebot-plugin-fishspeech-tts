# 更新记录

## 未发布 — 2026-10-19

- 核对官方 2026-10-16 新增的 `language`、2026-10-13 新增的 Drama 3，以及 S2.1-Pro 模型接口。
- 默认云端地址更新为 `https://api.fish.audio`，通过 `online_model` 设置基础模型请求头；默认 `s2.1-pro`，可显式选择 `s2.1-pro-free` 或 `drama-3` 等。
- 新增云端语言提示和角色音色 ID 映射；保留名称搜索及本地音频上传。
- 修复 MessagePack 字节误传 JSON 参数，以及并发请求共用、修改 Content-Type 的问题。
- 检查所有请求的 HTTP 状态及返回格式，区分鉴权、额度、限流及网络错误，避免发送错误正文或空音频。
- 对齐本地 fish-speech 的可选采样参数、Opus 比特率单位、默认 8080 端口、Bearer 鉴权、已保存参考音色和 Drama 3 整段生成参数。
- 未配置 `tts_max_new_tokens` 时不再发送旧版固定上限；显式配置保持生效。
- 修复缺失参考目录导致的未处理异常、正则前缀转义及空文本请求；移除依赖云端根路径正文的启动检测。
- 添加 HTTP 协议回归测试与 Python 3.10–3.13 CI，更新中英文文档和官方服务启动方法。

### 兼容提示

- 显式配置旧域名/端口的部署继续使用原值。未配置的部署将使用新默认地址。
- 默认 `s2.1-pro` 使用付费额度；免费模型可用范围与期限以官方为准。
- `online_model` 是合成基础模型，`reference_id` 是音色；自建服务在启动时选择基础模型。
- `tts_is_stream` 仍需完整接收后发送，不是聊天端实时播放。
- 测试使用模拟 API，不代表已验证真实账户余额、合成音质或 GPU 推理。

### 官方依据

- [官方更新记录](https://docs.fish.audio/developer-guide/getting-started/changelog)
- [云端 TTS API](https://docs.fish.audio/api-reference/endpoint/openapi-v1/text-to-speech)
- [模型退役时间](https://docs.fish.audio/developer-guide/models-pricing/deprecations)
- [本地请求结构](https://github.com/fishaudio/fish-speech/blob/main/fish_speech/utils/schema.py)
- [本地客户端示例](https://github.com/fishaudio/fish-speech/blob/main/tools/api_client.py)
