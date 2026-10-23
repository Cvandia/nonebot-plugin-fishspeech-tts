import { handleTTS } from "../../../lib/fish-proxy.mjs";
export const dynamic = "force-dynamic";
export async function POST(request: Request) { return handleTTS(request); }
