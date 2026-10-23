/**
 * Parse JSON off the main thread when payload is large enough.
 * Falls back to JSON.parse when Worker is unavailable or text is small.
 */

const WORKER_THRESHOLD = 48 * 1024; // 48 KiB

type WorkerOk = { id: number; ok: true; value: unknown };
type WorkerErr = { id: number; ok: false; error: string };
type WorkerReply = WorkerOk | WorkerErr;

let worker: Worker | null | undefined;
let nextId = 1;
const pending = new Map<
  number,
  { resolve: (v: unknown) => void; reject: (e: Error) => void }
>();

function getWorker(): Worker | null {
  if (worker !== undefined) return worker;
  if (typeof Worker === "undefined") {
    worker = null;
    return null;
  }
  try {
    worker = new Worker(new URL("./jsonParse.worker.ts", import.meta.url), {
      type: "module",
    });
    worker.onmessage = (ev: MessageEvent<WorkerReply>) => {
      const msg = ev.data;
      const slot = pending.get(msg.id);
      if (!slot) return;
      pending.delete(msg.id);
      if (msg.ok) slot.resolve(msg.value);
      else slot.reject(new Error(msg.error || "JSON worker parse failed"));
    };
    worker.onerror = () => {
      // Disable worker after hard failure; in-flight reject
      for (const [, slot] of pending) {
        slot.reject(new Error("JSON worker crashed"));
      }
      pending.clear();
      worker?.terminate();
      worker = null;
    };
  } catch {
    worker = null;
  }
  return worker;
}

function parseInWorker<T>(text: string): Promise<T> {
  const w = getWorker();
  if (!w) return Promise.resolve(JSON.parse(text) as T);
  const id = nextId++;
  return new Promise<T>((resolve, reject) => {
    pending.set(id, {
      resolve: (v) => resolve(v as T),
      reject,
    });
    w.postMessage({ id, text });
  });
}

/** Parse JSON text; uses a Worker above WORKER_THRESHOLD. */
export async function parseJsonText<T>(text: string): Promise<T> {
  if (text.length < WORKER_THRESHOLD) {
    return JSON.parse(text) as T;
  }
  try {
    return await parseInWorker<T>(text);
  } catch {
    return JSON.parse(text) as T;
  }
}

/** Read Response body as text and parse (worker for large payloads). */
export async function responseJson<T>(res: Response): Promise<T> {
  const text = await res.text();
  return parseJsonText<T>(text);
}
