import type { ApiError } from "@/types";

class ApiClientError extends Error {
  code: string;
  details?: Record<string, unknown>;

  constructor(message: string, code: string, details?: Record<string, unknown>) {
    super(message);
    this.name = "ApiClientError";
    this.code = code;
    this.details = details;
  }
}

let getToken: () => string | null;
let onUnauthorized: () => void;

export function configureAuth(
  tokenGetter: () => string | null,
  unauthorizedHandler: () => void,
) {
  getToken = tokenGetter;
  onUnauthorized = unauthorizedHandler;
}

async function request<T>(
  method: string,
  path: string,
  body?: unknown,
): Promise<T> {
  const headers: Record<string, string> = {
    Accept: "application/json",
  };

  const token = getToken?.();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  if (body !== undefined) {
    headers["Content-Type"] = "application/json";
  }

  const res = await fetch(path, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (!res.ok) {
    if (res.status === 401) {
      onUnauthorized?.();
    }

    let errorBody: ApiError | undefined;
    try {
      errorBody = (await res.json()) as ApiError;
    } catch {
      // ignore parse errors
    }

    throw new ApiClientError(
      errorBody?.error ?? `Request failed with status ${res.status}`,
      errorBody?.code ?? "UNKNOWN_ERROR",
      errorBody?.details,
    );
  }

  if (res.status === 204) {
    return undefined as T;
  }

  return res.json() as Promise<T>;
}

export function get<T>(path: string): Promise<T> {
  return request<T>("GET", path);
}

export function post<T>(path: string, body?: unknown): Promise<T> {
  return request<T>("POST", path, body);
}

export function put<T>(path: string, body?: unknown): Promise<T> {
  return request<T>("PUT", path, body);
}

export function del<T>(path: string): Promise<T> {
  return request<T>("DELETE", path);
}

export { ApiClientError };
