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
let csrfTokenRequest: Promise<string> | null = null;

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
  if (csrfToken) {
    return csrfToken;
  }
  if (!csrfTokenRequest) {
    csrfTokenRequest = request<DataResponse<{ csrf_token: string }>>(
      "/api/v1/auth/csrf/",
    )
      .then((response) => {
        csrfToken = response.data.csrf_token;
        return csrfToken;
      })
      .finally(() => {
        csrfTokenRequest = null;
      });
  }
  return csrfTokenRequest;
}

function clearCsrfToken(): void {
  csrfToken = null;
  csrfTokenRequest = null;
}

async function csrfMutation<T>(path: string, init: RequestInit): Promise<T> {
  async function send(retriedAfterCsrfFailure: boolean): Promise<T> {
    const token = await ensureCsrfToken();
    try {
      return await request<T>(path, {
        ...init,
        headers: {
          ...init.headers,
          "X-CSRFToken": token,
        },
      });
    } catch (error) {
      if (
        !retriedAfterCsrfFailure &&
        error instanceof ApiError &&
        error.code === "csrf_failed"
      ) {
        clearCsrfToken();
        return send(true);
      }
      throw error;
    }
  }

  return send(false);
}

export async function getCurrentUser(): Promise<User> {
  const response = await request<DataResponse<User>>("/api/v1/auth/me/");
  return response.data;
}

export async function loginUser(credentials: {
  email: string;
  password: string;
}): Promise<User> {
  const response = await csrfMutation<DataResponse<User>>("/api/v1/auth/login/", {
    method: "POST",
    body: JSON.stringify(credentials),
  });
  clearCsrfToken();
  await ensureCsrfToken();
  return response.data;
}

export async function logoutUser(): Promise<void> {
  await csrfMutation<void>("/api/v1/auth/logout/", {
    method: "POST",
  });
  clearCsrfToken();
}
