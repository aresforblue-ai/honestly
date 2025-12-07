import { NextResponse } from "next/server";

const TARGET = process.env.LLM_PROXY_TARGET;
const AUTH_HEADER = process.env.LLM_PROXY_AUTH_HEADER || "";

export async function GET() {
  if (!TARGET) {
    return NextResponse.json({ healthy: false, error: "LLM_PROXY_TARGET not configured" }, { status: 503 });
  }
  try {
    const headers = new Headers();
    if (AUTH_HEADER) headers.set("Authorization", AUTH_HEADER);
    const res = await fetch(TARGET, { method: "GET", headers });
    const healthy = res.ok;
    return NextResponse.json({ healthy, status: res.status }, { status: healthy ? 200 : 502 });
  } catch (err) {
    return NextResponse.json({ healthy: false, error: (err as Error).message }, { status: 502 });
  }
}

