const DEFAULT_HEADERS = {
  "Content-Type": "application/json",
};

type RequestHeaders = Record<string, string>;

export async function getJson<T>(url: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(url, { signal });
  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }
  return (await response.json()) as T;
}

export async function postJson<T>(
  url: string,
  body: unknown,
  signal?: AbortSignal,
  headers?: RequestHeaders,
): Promise<T> {
  const response = await fetch(url, {
    method: "POST",
    headers: {
      ...DEFAULT_HEADERS,
      ...headers,
    },
    body: JSON.stringify(body),
    signal,
  });
  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }
  return (await response.json()) as T;
}
