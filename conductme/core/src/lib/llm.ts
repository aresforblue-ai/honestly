import { useEffect, useState } from "react";

export type LlmHealth = { healthy: boolean; status?: number; error?: string };

export function useLlmHealth(pollMs = 10000): LlmHealth {
  const [state, setState] = useState<LlmHealth>({ healthy: false });

  useEffect(() => {
    let active = true;
    const run = async () => {
      try {
        const res = await fetch("/api/llm/health");
        const json = (await res.json()) as LlmHealth;
        if (!active) return;
        setState({ healthy: json.healthy, status: json.status, error: json.error });
      } catch (err) {
        if (!active) return;
        setState({ healthy: false, error: (err as Error).message });
      }
    };
    run();
    const id = setInterval(run, pollMs);
    return () => {
      active = false;
      clearInterval(id);
    };
  }, [pollMs]);

  return state;
}

