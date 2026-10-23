import { test } from "node:test";
import assert from "node:assert/strict";
import { MODEL, handleTTS, parseInput } from "../lib/fish-proxy.mjs";
const id = "626bb6d3f3364c9cbc3aa6a67300a664";
const request = (body, headers = {}) => new Request("https://example.com/api/tts", { method: "POST", headers: { "Content-Type": "application/json", Authorization: "Bearer test-key", ...headers }, body: JSON.stringify(body) });
test("preserves plugin directions, whitespace, quotes, entities and newlines", () => {
  const text = '[激情]你好  "可莉"\n[whispering] &#91;秘密&#93;';
  assert.deepEqual(parseInput({ command: "/可莉说" + text, voiceName: "可莉", referenceId: id }), { speaker: "可莉", text, referenceId: id });
});
test("plain text uses selected voice; switched command resolves a new voice", () => {
  assert.equal(parseInput({ command: "听我说你好", voiceName: "可莉", referenceId: id }).text, "听我说你好");
  assert.equal(parseInput({ command: "/臭企鹅说你好", voiceName: "可莉", referenceId: id }).referenceId, "");
});
for (const command of ["", "/可莉说", "/未知指令", "字".repeat(2001)]) test("rejects invalid input: " + command.slice(0, 10), () => assert.throws(() => parseInput({ command })));
test("rejects paid model override", async () => {
  const result = await handleTTS(request({ command: "你好", model: "s2.1-pro" }), () => assert.fail("must not call upstream"));
  assert.equal(result.status, 400);
});
test("requires credentials and denies cross-site requests", async () => {
  assert.equal((await handleTTS(request({ command: "你好" }, { Authorization: "" }))).status, 401);
  assert.equal((await handleTTS(request({ command: "你好" }, { Origin: "https://evil.example" }))).status, 403);
});
test("uses only the official free model and returns audio without caching", async () => {
  const result = await handleTTS(request({ command: "/可莉说[激情]你好", voiceName: "可莉", referenceId: id }), async (url, init) => {
    assert.equal(url, "https://api.fish.audio/v1/tts"); assert.equal(init.headers.model, MODEL);
    assert.equal(JSON.parse(init.body).text, "[激情]你好"); assert.equal(init.redirect, "manual");
    return new Response(new Uint8Array([73, 68, 51]), { headers: { "Content-Type": "audio/mpeg" } });
  });
  assert.equal(result.status, 200); assert.equal(result.headers.get("Cache-Control"), "no-store"); assert.equal((await result.arrayBuffer()).byteLength, 3);
});
test("searches a new speaker before synthesizing", async () => {
  const calls = [];
  const result = await handleTTS(request({ command: "/可莉说你好" }), async (url, init) => {
    calls.push(String(url));
    if (calls.length === 1) return Response.json({ items: [{ title: "可莉", _id: id }] });
    assert.equal(JSON.parse(init.body).reference_id, id);
    return new Response("ID3", { headers: { "Content-Type": "audio/mpeg" } });
  });
  assert.equal(result.status, 200); assert.equal(calls.length, 2);
});
for (const status of [401, 402, 403, 404, 422, 429, 503]) test("sanitizes upstream error " + status, async () => {
  const result = await handleTTS(request({ command: "你好", voiceName: "可莉", referenceId: id }), async () => new Response("private-upstream-details", { status }));
  assert.equal(result.status, status === 503 ? 502 : status); assert.ok(!(await result.text()).includes("private-upstream-details"));
});
test("never treats JSON errors or empty bytes as audio", async () => {
  for (const response of [Response.json({ error: "bad" }), new Response("", { headers: { "Content-Type": "audio/mpeg" } })]) {
    assert.equal((await handleTTS(request({ command: "你好", voiceName: "可莉", referenceId: id }), async () => response)).status, 502);
  }
});
