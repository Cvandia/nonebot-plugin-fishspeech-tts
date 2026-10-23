"use client";
import { useEffect, useRef, useState } from "react";
import { ArrowUp, AudioLines, Check, Download, ExternalLink, KeyRound, MessageCircle, Plus, Settings2, ShieldCheck, Square, Volume2, X } from "lucide-react";

type Chat = { id: number; role: "user" | "bot"; text: string; audio?: string; voice?: string; seconds?: string; error?: boolean };
const welcome: Chat = { id: 0, role: "bot", text: "你好呀！准备好听听可莉的声音了吗？\n发一句想让我说的话，也可以加上 [开心]、[轻声] 这样的语气标签。" };
const presets = [
  { title: "✦ 开心一点", tag: "[happy]", text: "你好呀，我是可莉！今天也要开开心心！" },
  { title: "◌ 悄悄告诉你", tag: "[whispering]", text: "嘘，这是我们之间的小秘密。" },
  { title: "↗ 激情演绎", tag: "[excited]", text: "出发吧！我们的冒险现在开始！" },
];
export default function Home() {
  const [messages, setMessages] = useState<Chat[]>([welcome]);
  const [draft, setDraft] = useState("");
  const [key, setKey] = useState("");
  const [voiceName, setVoiceName] = useState("可莉");
  const [referenceId, setReferenceId] = useState("626bb6d3f3364c9cbc3aa6a67300a664");
  const [busy, setBusy] = useState(false);
  const [settings, setSettings] = useState(false);
  const [notice, setNotice] = useState("");
  const [copied, setCopied] = useState(false);
  const abort = useRef<AbortController | null>(null);
  const urls = useRef<string[]>([]);
  const bottom = useRef<HTMLDivElement>(null);
  const input = useRef<HTMLTextAreaElement>(null);
  useEffect(() => { bottom.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, busy]);
  useEffect(() => () => { abort.current?.abort(); urls.current.forEach(URL.revokeObjectURL); }, []);
  function reset() {
    if (busy) return;
    urls.current.forEach(URL.revokeObjectURL); urls.current = [];
    setMessages([welcome]); setDraft(""); setNotice("");
  }
  async function send() {
    if (busy || !draft.trim()) return;
    if (!key.trim()) { setSettings(true); setNotice("请先填写你自己的 Fish Audio API 密钥。"); return; }
    const command = draft;
    const controller = new AbortController(); abort.current = controller;
    setMessages(m => [...m, { id: Date.now(), role: "user", text: command }]);
    setDraft(""); setBusy(true); setNotice("");
    const start = performance.now();
    try {
      const response = await fetch("/api/tts", { method: "POST", headers: { "Content-Type": "application/json", Authorization: `Bearer ${key.trim().replace(/^Bearer\s+/i, "")}` }, body: JSON.stringify({ command, voiceName, referenceId }), signal: controller.signal });
      if (!response.ok) { const data = await response.json() as { error?: string }; throw new Error(typeof data.error === "string" ? data.error : "合成失败，请稍后重试。"); }
      const blob = await response.blob();
      if (!blob.size || !blob.type.startsWith("audio/")) throw new Error("接口没有返回有效音频。");
      const url = URL.createObjectURL(blob); urls.current.push(url);
      const voice = decodeURIComponent(response.headers.get("X-Voice-Name") || encodeURIComponent(voiceName));
      setMessages(m => [...m, { id: Date.now(), role: "bot", text: "语音已生成", audio: url, voice, seconds: ((performance.now() - start) / 1000).toFixed(1) }]);
    } catch (e) {
      const cancelled = controller.signal.aborted;
      setMessages(m => [...m, { id: Date.now(), role: "bot", text: cancelled ? "已取消本次生成。" : e instanceof Error ? e.message : "网络连接失败，请重试。", error: !cancelled }]);
      if (!cancelled) setDraft(command);
    } finally { setBusy(false); abort.current = null; }
  }
  async function copyConfig() {
    const value = `TTS_IS_ONLINE=true\nONLINE_MODEL=s2.1-pro-free\nONLINE_API_URL=https://api.fish.audio\nONLINE_REFERENCE_IDS='${JSON.stringify({ [voiceName]: referenceId })}'\n# ONLINE_AUTHORIZATION=填写你的密钥`;
    try { await navigator.clipboard.writeText(value); setCopied(true); setTimeout(() => setCopied(false), 1800); }
    catch { setNotice("浏览器未允许复制，请参阅仓库配置文档。"); }
  }
  return <div className="shell">
    <aside className="sidebar">
      <a className="brand" href="https://github.com/Cvandia/nonebot-plugin-fishspeech-tts" target="_blank" rel="noreferrer"><span className="brand-icon"><AudioLines size={23}/></span><span>Fish Speech<small>VOICE PLAYGROUND</small></span></a>
      <button className="new-chat" onClick={reset} disabled={busy}><Plus size={16}/>新建对话<span>↗</span></button>
      <div className="nav-label">体验空间</div><div className="nav-active"><MessageCircle size={16}/>语音对话<i/></div>
      <div className="session-card"><span>当前会话</span><strong>{voiceName || "自定义音色"}的语音小屋</strong><p>每一句文字，都可以有声音。</p><div className="mini-wave">▁ ▃ ▆ ▄ ▂ ▇ ▅ ▂ ▁</div></div>
      <div className="sidebar-bottom"><a href="https://github.com/Cvandia/nonebot-plugin-fishspeech-tts" target="_blank" rel="noreferrer">查看插件项目 <ExternalLink size={12}/></a><p>由 Fish Audio 驱动<br/>nonebot-plugin-fishspeech-tts</p></div>
    </aside>
    <main className="main">
      <header className="chat-header"><div className="avatar small">{(voiceName || "音").slice(0, 1)}</div><div><h1>{voiceName || "自定义音色"}<span>⌄</span></h1><p>让文字带上情绪，听见角色的声音</p></div><span className="free-badge"><i/>免费模型</span><button className="settings-toggle icon-button" aria-label="打开音色与密钥设置" onClick={() => setSettings(true)}><Settings2 size={19}/></button></header>
      <div className="chat-area">
        <div className="intro"><span>TEXT → VOICE</span><h2>像聊天一样，<em>听见文字。</em></h2><p>输入一句话，让熟悉的声音为你回应。</p></div>
        <div className="date-divider"><span>本次对话 · 仅保留在当前页面</span></div>
        <div className="messages" aria-live="polite" aria-relevant="additions">
          {messages.map(m => <article key={m.id} className={`message ${m.role} ${m.error ? "error" : ""}`}>
            {m.role === "bot" && <div className="avatar">{(m.voice || voiceName || "音").slice(0, 1)}</div>}
            <div className="message-content"><div className="message-author">{m.role === "bot" ? m.voice || voiceName : "你"}</div><div className="bubble">{m.audio ? <><div className="voice-label"><Volume2 size={16}/><span>给你的一条语音</span><span className="audio-type">MP3</span></div><audio controls preload="metadata" src={m.audio} aria-label={`${m.voice}生成的语音`}/><div className="audio-bottom"><span>生成用时 {m.seconds} 秒</span><a href={m.audio} download={`fishspeech-${m.id}.mp3`}><Download size={13}/>下载</a></div></> : <p>{m.text}</p>}</div>{m.audio && <div className="under-bubble"><ShieldCheck size={12}/>s2.1-pro-free · 免费模型</div>}</div>
            {m.role === "user" && <div className="user-avatar">你</div>}
          </article>)}
          {busy && <article className="message bot"><div className="avatar">{(voiceName || "音").slice(0, 1)}</div><div className="message-content"><div className="message-author">正在合成</div><div className="bubble typing"><i/><i/><i/><span>把文字变成声音…</span></div></div></article>}
          <div ref={bottom}/>
        </div>
      </div>
      <div className="composer-wrap"><div className="suggestions">{presets.map(p => <button key={p.tag} disabled={busy} onClick={() => { setDraft(`/${voiceName || "可莉"}说${p.tag}${p.text}`); input.current?.focus(); }}>{p.title}</button>)}</div>
        {notice && <p role="alert" className="notice">{notice}</p>}
        <form className="composer" onSubmit={e => { e.preventDefault(); void send(); }}><label className="sr-only" htmlFor="draft">聊天消息或插件指令</label><textarea ref={input} id="draft" value={draft} maxLength={2200} placeholder={`说点什么，或试试 /${voiceName || "可莉"}说[开心]你好呀`} onChange={e => setDraft(e.target.value)} onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) { e.preventDefault(); void send(); } }} rows={2}/><div className="composer-footer"><span><AudioLines size={14}/>{voiceName || "自定义音色"}<b>/</b>语气指令原样保留</span>{busy ? <button type="button" className="send-button" aria-label="取消生成" onClick={() => abort.current?.abort()}><Square size={15}/></button> : <button className="send-button" disabled={!draft.trim()} aria-label="发送并生成语音"><ArrowUp size={20}/></button>}</div></form>
        <p className="composer-hint">Enter 发送 · Shift + Enter 换行<span>语气由模型演绎，效果可能不同</span></p>
      </div>
    </main>
    {settings && <button className="settings-backdrop" aria-label="关闭设置" onClick={() => setSettings(false)}/>}
    <aside className={`settings ${settings ? "open" : ""}`}><div className="settings-heading"><Settings2 size={16}/><h2>体验设置</h2><button className="icon-button close-settings" aria-label="关闭设置" onClick={() => setSettings(false)}><X size={18}/></button></div>
      <div className="settings-section"><h3><KeyRound size={15}/>连接你的声音</h3><label htmlFor="api-key">Fish Audio API 密钥</label><input id="api-key" type="password" autoComplete="off" spellCheck={false} value={key} onChange={e => { setKey(e.target.value); setNotice(""); }} placeholder="粘贴你的 API Key"/><p className="field-help">仅用于本次调用，不写入浏览器存储。经本站代理发送至 Fish Audio。</p><a className="text-link" href="https://fish.audio/app/api-keys" target="_blank" rel="noreferrer">获取 API 密钥 <ExternalLink size={12}/></a>{key && <button className="clear-key" onClick={() => setKey("")}>清除密钥</button>}</div>
      <div className="settings-section"><h3><Volume2 size={16}/>角色音色</h3><label htmlFor="voice-name">角色名称</label><input id="voice-name" value={voiceName} maxLength={60} disabled={busy} onChange={e => { setVoiceName(e.target.value); setReferenceId(""); }} placeholder="例如：可莉"/><label htmlFor="reference-id">音色 ID <span className="optional">可选</span></label><input id="reference-id" value={referenceId} disabled={busy} onChange={e => setReferenceId(e.target.value)} placeholder="留空时按角色名称查找"/><p className="field-help">默认使用已测试的可莉音色。更换角色后留空 ID，可按名称自动查找。</p><button className="preset-voice" disabled={busy} onClick={() => { setVoiceName("可莉"); setReferenceId("626bb6d3f3364c9cbc3aa6a67300a664"); }}>恢复可莉音色</button></div>
      <div className="model-card"><div><i/>S2.1 Pro Free<span>FREE</span></div><p>固定免费模型，无付费模型回退。可用期限与限流以官方政策为准。</p></div>
      <details className="tips"><summary>语气标签怎么用？</summary><p>放在要演绎的文字之前：</p><code>[happy] 今天真开心！</code><code>[whispering] 这是个秘密。</code><p>中文描述也可以，建议每句使用一个主要语气。</p></details>
      <button className="config-copy" onClick={() => void copyConfig()}>{copied ? <Check size={14}/> : <Download size={14}/>} {copied ? "已复制（不含密钥）" : "复制对应插件配置"}</button>
      <p className="settings-footnote">本页体验插件的语音接口与指令格式；完整 NoneBot 响应需在机器人中使用。</p>
    </aside>
  </div>;
}
