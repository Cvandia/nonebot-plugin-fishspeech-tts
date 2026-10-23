export const MODEL = "s2.1-pro-free";
const API = "https://api.fish.audio";
const MAX_AUDIO = 12 * 1024 * 1024;
const errors = { 400: "请求参数无效，请检查音色及文本。", 401: "API 密钥无效或已失效，请重新填写。", 402: "账户或当前免费模型不可用，请检查 Fish Audio 账户。", 403: "API 密钥没有访问权限。", 404: "音色或 API 不存在，请检查音色 ID。", 422: "API 参数校验失败，请检查文本和音色。", 429: "请求频率或并发超限，请稍后重试。", 503: "免费合成服务暂时繁忙，请稍后重试。" };
class ClientError extends Error { constructor(message, status = 400) { super(message); this.status = status; } }
const jsonError = (message, status) => Response.json({ error: message }, { status, headers: { "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff" } });
async function limitedBytes(body, max) {
  if (!body) throw new ClientError("响应为空，请重试。", 502);
  const reader = body.getReader(); const chunks = []; let size = 0;
  try { for (;;) { const { value, done } = await reader.read(); if (done) break; size += value.length; if (size > max) { await reader.cancel(); throw new ClientError("请求或音频过长，请缩短文本。", 413); } chunks.push(value); } }
  finally { reader.releaseLock(); }
  const bytes = new Uint8Array(size); let offset = 0;
  for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.length; }
  return bytes;
}
export function parseInput(body) {
  if (!body || typeof body !== "object" || Array.isArray(body)) throw new ClientError("请提交有效的合成内容。");
  if (Object.keys(body).some(k => !["command", "voiceName", "referenceId"].includes(k))) throw new ClientError("不支持自定义模型或 API 地址。");
  const { command, voiceName = "可莉", referenceId = "" } = body;
  if (typeof command !== "string" || typeof voiceName !== "string" || typeof referenceId !== "string") throw new ClientError("文本和音色配置格式无效。");
  const matched = /^[/!](?<speaker>[^\r\n]+?)说(?<text>[\s\S]*)$/.exec(command);
  if (/^[/!]/.test(command) && !matched) throw new ClientError("指令格式：/角色名说需要合成的文本。");
  const speaker = matched ? matched.groups.speaker : voiceName;
  const text = matched ? matched.groups.text : command;
  if (!text.trim()) throw new ClientError("请输入需要合成的文本。");
  if (text.length > 2000 || !speaker.trim() || speaker.length > 60 || /[\r\n]/.test(speaker)) throw new ClientError("正文限 2000 字，角色名称限 60 字。");
  const id = speaker === voiceName ? referenceId.trim() : "";
  if (id && !/^[a-f0-9]{32}$/i.test(id)) throw new ClientError("音色 ID 应为 32 位十六进制字符，或留空自动查找。");
  return { speaker, text, referenceId: id };
}
export async function handleTTS(request, fetcher = fetch) {
  if (request.method !== "POST") return jsonError("请使用 POST 请求。", 405);
  const origin = request.headers.get("Origin");
  if (origin && origin !== new URL(request.url).origin) return jsonError("不允许跨站请求。", 403);
  if (!request.headers.get("Content-Type")?.startsWith("application/json")) return jsonError("请使用 JSON 格式。", 415);
  const auth = request.headers.get("Authorization") || "";
  if (!/^Bearer [^\s]{1,2048}$/i.test(auth)) return jsonError("请先填写 Fish Audio API 密钥。", 401);
  const signal = AbortSignal.any([request.signal, AbortSignal.timeout(90000)]);
  try {
    const raw = await limitedBytes(request.body, 16000);
    let body; try { body = JSON.parse(new TextDecoder().decode(raw)); } catch { throw new ClientError("请求 JSON 格式无效。"); }
    const parsed = parseInput(body);
    let referenceId = parsed.referenceId;
    if (!referenceId) {
      for (const sort of ["score", "task_count", "created_at"]) {
        const url = new URL(API + "/model"); url.searchParams.set("title", parsed.speaker); url.searchParams.set("sort_by", sort);
        const response = await fetcher(url, { headers: { Authorization: auth }, signal, redirect: "manual" });
        if (!response.ok) { await response.body?.cancel(); throw new ClientError(errors[response.status] || "音色查询服务暂不可用。", response.status >= 500 ? 502 : response.status); }
        const data = JSON.parse(new TextDecoder().decode(await limitedBytes(response.body, 512000)));
        if (!Array.isArray(data.items)) throw new ClientError("音色查询返回格式异常。", 502);
        const voice = data.items.find(item => typeof item?.title === "string" && item.title.includes(parsed.speaker) && /^[a-f0-9]{32}$/i.test(item._id));
        if (voice) { referenceId = voice._id; break; }
      }
      if (!referenceId) throw new ClientError("未找到该角色，请在设置中填写准确的音色 ID。", 404);
    }
    const response = await fetcher(API + "/v1/tts", { method: "POST", headers: { Authorization: auth, "Content-Type": "application/json", model: MODEL }, body: JSON.stringify({ text: parsed.text, reference_id: referenceId, format: "mp3", mp3_bitrate: 128, language: "zh-CN", chunk_length: 200, normalize: true, latency: "normal" }), signal, redirect: "manual" });
    if (!response.ok) { await response.body?.cancel(); throw new ClientError(errors[response.status] || "语音服务暂时不可用，请稍后重试。", response.status >= 500 ? 502 : response.status); }
    const type = response.headers.get("Content-Type")?.split(";")[0];
    if (!type || (!type.startsWith("audio/") && type !== "application/octet-stream")) { await response.body?.cancel(); throw new ClientError("API 未返回音频，请稍后重试。", 502); }
    const audio = await limitedBytes(response.body, MAX_AUDIO);
    if (!audio.length) throw new ClientError("API 返回空音频，请重试。", 502);
    return new Response(audio, { headers: { "Content-Type": "audio/mpeg", "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff", "X-Voice-Name": encodeURIComponent(parsed.speaker), "X-Model": MODEL } });
  } catch (error) {
    if (error instanceof ClientError) return jsonError(error.message, error.status);
    return jsonError(signal.aborted ? "请求已取消或超时，请稍后重试。" : "连接 Fish Audio 失败，请稍后重试。", signal.aborted ? 504 : 502);
  }
}
