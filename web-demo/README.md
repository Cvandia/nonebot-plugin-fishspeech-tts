# Fish Speech 聊天体验站

在线体验：https://fishspeech-chat-demo.arcane-krill-2332.chatgpt.site

公开聊天式体验页，访客填写自己的 Fish Audio API 密钥，默认可莉音色。支持输入 `/可莉说[激情]你好呀`、纯文本、语气快捷按钮、语音播放/下载、取消、新建对话和复制不含密钥的插件配置。

## 运行

需要 Node.js >=22.13。在本目录执行：

```sh
npm ci
npm run dev
```

打开终端显示的本地地址。测试和构建：

```sh
node --test tests/fish-proxy.test.mjs
npx tsc --noEmit
npm run build
```

站点使用 Vinext + React，并保留 Sites/Cloudflare Worker 构建集成。`.openai/hosting.json` 记录部署项目 ID，不包含凭据。自行部署时使用自己的 Sites 项目 ID；其他 Cloudflare 环境可按 Vinext 部署方式配置。构建结果位于 `dist/`，不能只把 HTML 上传到 GitHub Pages：官方 `/v1/tts` 没有允许跨域浏览器调用，需要同源服务端 `/api/tts` 代理。

## 请求边界

- 仅允许官方 `https://api.fish.audio`，合成模型请求头固定 `s2.1-pro-free`。不接受模型或目标 URL 覆盖，不回退付费模型，不跟随上游重定向。
- 浏览器通过 Authorization 请求头传入访客密钥。应用不将密钥或聊天写入数据库、localStorage、sessionStorage 或 cookie，也不在日志中主动记录密钥。响应为 `Cache-Control: no-store`。刷新页面会清除会话；音频可主动下载保存。
- 代理会临时处理密钥并转发给 Fish Audio。公开访问者应使用自己的密钥；本仓库和部署中没有内置共享密钥。部署运营方仍需按其托管环境配置日志与访问策略。
- 正文限 2000 字，请求体限 16 KB，音频限 12 MB，90 秒超时。音色 ID 留空时按角色名称查找；指令中切换角色时不会误用旧音色 ID。
- 页面只体验插件的合成接口和命令格式，不运行 NoneBot/OneBot 事件循环。插件的群聊、@、回复消息合成等完整行为请在机器人中体验。
- 免费模型可用期限、账户权限及限流由 Fish Audio 决定；语气遵循程度由模型决定。

核心逻辑：`lib/fish-proxy.mjs`；页面：`app/page.tsx`；测试：`tests/fish-proxy.test.mjs`。
