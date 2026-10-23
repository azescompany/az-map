/// <reference lib="webworker" />

self.onmessage = (ev: MessageEvent<{ id: number; text: string }>) => {
  const { id, text } = ev.data;
  try {
    const value = JSON.parse(text) as unknown;
    postMessage({ id, ok: true, value });
  } catch (e) {
    const message = e instanceof Error ? e.message : String(e);
    postMessage({ id, ok: false, error: message });
  }
};
