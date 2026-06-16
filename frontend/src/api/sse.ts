export interface ParsedEvent<T = unknown> {
  id: string;
  event: string;
  data: T;
}

function parseChunk(chunk: string): ParsedEvent | null {
  const lines = chunk
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);
  if (!lines.length) {
    return null;
  }

  let id = "";
  let event = "message";
  let data = "";

  for (const line of lines) {
    if (line.startsWith("id:")) {
      id = line.slice(3).trim();
      continue;
    }
    if (line.startsWith("event:")) {
      event = line.slice(6).trim();
      continue;
    }
    if (line.startsWith("data:")) {
      data += line.slice(5).trim();
    }
  }

  return {
    id,
    event,
    data: data ? JSON.parse(data) : null,
  };
}

export async function* streamEvents<T>(
  url: string,
  options: { signal?: AbortSignal; lastEventId?: string } = {},
): AsyncGenerator<ParsedEvent<T>, void, void> {
  const headers: Record<string, string> = {};
  if (options.lastEventId) {
    headers["Last-Event-ID"] = options.lastEventId;
  }

  const response = await fetch(url, { signal: options.signal, headers });
  if (!response.body) {
    return;
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) {
      break;
    }

    buffer += decoder.decode(value, { stream: true });
    const chunks = buffer.split(/\n\n/);
    buffer = chunks.pop() ?? "";

    for (const chunk of chunks) {
      const parsed = parseChunk(chunk);
      if (parsed) {
        yield parsed as ParsedEvent<T>;
      }
    }
  }

  const tail = parseChunk(buffer);
  if (tail) {
    yield tail as ParsedEvent<T>;
  }
}
