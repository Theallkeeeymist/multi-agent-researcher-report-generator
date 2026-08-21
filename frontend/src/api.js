const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export async function checkHealth() {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error(`Health check failed (${res.status})`);
  const data = await res.json();
  return data.status === "ok";
}

export async function streamResearch(question, { onStage, onResult, onError, signal }) {
  const res = await fetch(`${API_BASE}/research/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
    signal,
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Request failed (${res.status})`);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (!line.startsWith("data: ")) continue;
      const raw = line.slice(6).trim();
      if (!raw) continue;

      try {
        const event = JSON.parse(raw);
        if (event.type === "stage") onStage?.(event);
        else if (event.type === "result") onResult?.(event);
      } catch {
        onError?.(new Error("Failed to parse SSE event"));
      }
    }
  }
}
