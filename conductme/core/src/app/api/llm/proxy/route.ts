import { NextRequest, NextResponse } from "next/server";

const TARGET = process.env.LLM_PROXY_TARGET;
const AUTH_HEADER = process.env.LLM_PROXY_AUTH_HEADER || "";

export async function POST(req: NextRequest) {
  if (!TARGET) {
    return NextResponse.json({ error: "LLM_PROXY_TARGET not configured" }, { status: 503 });
  }

  const body = await req.text();
  const headers = new Headers();
  headers.set("Content-Type", req.headers.get("content-type") || "application/json");
  if (AUTH_HEADER) headers.set("Authorization", AUTH_HEADER);

  const res = await fetch(TARGET, {
    method: "POST",
    headers,
    body,
  });

  const text = await res.text();
  return new NextResponse(text, {
    status: res.status,
    headers: {
      "content-type": res.headers.get("content-type") || "application/json",
    },
  });
}

export async function GET(req: NextRequest) {
  // Simple passthrough GET (health or metadata)
  if (!TARGET) {
    return NextResponse.json({ error: "LLM_PROXY_TARGET not configured" }, { status: 503 });
  }
  const url = TARGET;
  const headers = new Headers();
  if (AUTH_HEADER) headers.set("Authorization", AUTH_HEADER);
  const res = await fetch(url, { method: "GET", headers });
  const text = await res.text();
  return new NextResponse(text, {
    status: res.status,
    headers: {
      "content-type": res.headers.get("content-type") || "application/json",
    },
  });
}

