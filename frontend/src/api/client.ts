export type User = {
  id: string;
  email: string;
  display_name: string;
  is_staff: boolean;
};

type DataResponse<T> = { data: T };
type ErrorPayload = {
  error?: {
    code?: string;
    message?: string;
    field_errors?: Record<string, string[]>;
  };
};

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly fieldErrors: Record<string, string[]>;

  constructor(status: number, payload: ErrorPayload) {
    super(payload.error?.message ?? "请求失败，请稍后重试。");
    this.name = "ApiError";
    this.status = status;
    this.code = payload.error?.code ?? "request_error";
    this.fieldErrors = payload.error?.field_errors ?? {};
  }
}

let csrfToken: string | null = null;

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    ...init,
    credentials: "include",
    headers: {
      Accept: "application/json",
      ...(init?.body ? { "Content-Type": "application/json" } : {}),
      ...init?.headers,
    },
  });

  if (!response.ok) {
    let payload: ErrorPayload = {};
    try {
      payload = (await response.json()) as ErrorPayload;
    } catch {
      // Keep the safe generic message when a proxy returns a non-JSON error.
    }
    throw new ApiError(response.status, payload);
  }

  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

export async function ensureCsrfToken(): Promise<string> {
  const response = await request<DataResponse<{ csrf_token: string }>>(
    "/api/v1/auth/csrf/",
  );
  csrfToken = response.data.csrf_token;
  return csrfToken;
}

async function mutationHeaders(): Promise<Record<string, string>> {
  const token = csrfToken ?? (await ensureCsrfToken());
  return { "X-CSRFToken": token };
}

export async function getCurrentUser(): Promise<User> {
  const response = await request<DataResponse<User>>("/api/v1/auth/me/");
  return response.data;
}

export async function loginUser(credentials: {
  email: string;
  password: string;
}): Promise<User> {
  const response = await request<DataResponse<User>>("/api/v1/auth/login/", {
    method: "POST",
    headers: await mutationHeaders(),
    body: JSON.stringify(credentials),
  });
  return response.data;
}

export async function logoutUser(): Promise<void> {
  await request<void>("/api/v1/auth/logout/", {
    method: "POST",
    headers: await mutationHeaders(),
  });
}
