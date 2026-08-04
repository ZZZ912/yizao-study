export type User = {
  id: string;
  email: string;
  display_name: string;
  is_staff: boolean;
};

export type DashboardData = {
  exam: { date: string; days_remaining: number; location: string; specialty: string; syllabus: string };
  today: {
    answered: number;
    correct: number;
    accuracy: number;
    due_reviews: number;
    target_questions: number;
    completed_lessons: number;
  };
  question_count: number;
  knowledge_count: number;
  section_count: number;
  completed_section_count: number;
  course_progress: number;
  wrong_count: number;
  next_section: null | {
    id: string;
    subject: string;
    chapter: string;
    title: string;
    question_count: number;
    knowledge_count: number;
    estimated_minutes: number;
  };
  quick_card: QuickCard | null;
};

export type SubjectSummary = {
  id: string;
  code: string;
  title: string;
  question_count: number;
  knowledge_count: number;
  section_count: number;
  completed_sections: number;
  progress: number;
};

export type ChapterSummary = {
  number: number;
  title: string;
  question_count: number;
  attempted_questions: number;
  wrong_count: number;
  sections: Array<{
    id: string;
    number: number;
    title: string;
    question_count: number;
    attempted_questions: number;
    attempt_count: number;
    correct_count: number;
    accuracy: number;
    wrong_count: number;
    knowledge_count: number;
    is_completed: boolean;
  }>;
};

export type LearningReport = {
  overview: {
    question_count: number;
    attempted_questions: number;
    attempt_count: number;
    correct_count: number;
    accuracy: number;
    study_minutes: number;
    active_wrong: number;
    mastered_wrong: number;
    due_reviews: number;
    completed_sections: number;
    section_count: number;
  };
  subjects: Array<{
    code: string;
    title: string;
    question_count: number;
    attempted_questions: number;
    attempt_count: number;
    correct_count: number;
    accuracy: number;
    wrong_count: number;
    section_count: number;
    completed_sections: number;
    course_progress: number;
  }>;
  weak_sections: Array<{
    section_id: string;
    subject: string;
    section: string;
    attempt_count: number;
    wrong_count: number;
    accuracy: number;
  }>;
  wrong_reasons: Array<{ code: string; label: string; count: number }>;
  activity: Array<{
    date: string;
    answered: number;
    correct: number;
    completed_lessons: number;
  }>;
  recent_attempts: Array<{
    id: string;
    question_id: string;
    stem: string;
    subject: string;
    section: string;
    selected_answer: string[];
    correct_answer: string[];
    is_correct: boolean;
    elapsed_seconds: number;
    wrong_reason: string;
    created_at: string;
  }>;
};

export type ContentBlock = { type: string; content: string };
export type SectionDetail = {
  id: string;
  subject: { code: string; title: string };
  chapter: { number: number; title: string };
  number: number;
  title: string;
  question_count: number;
  knowledge_points: Array<{
    id: string;
    title: string;
    summary: string;
    content_blocks: ContentBlock[];
    exam_edition: string;
  }>;
  progress: null | { status: "started" | "completed"; completed_at: string | null };
};

export type QuickCard = {
  id: string;
  title: string;
  summary: string;
  content_blocks: ContentBlock[];
  subject: { code: string; title: string };
  chapter: { number: number; title: string };
  section: { id: string; title: string };
  position: number;
  total: number;
};

export type PracticeQuestion = {
  id: string;
  version_id: string;
  external_id: string;
  question_type: "single_choice" | "multiple_choice";
  stem: string;
  options: Array<{ label: string; text: string }>;
  difficulty: string;
  subject: { code: string; title: string };
  chapter: { number: number; title: string };
  section: { id: string; number: number; title: string };
};

export type AttemptResult = {
  attempt_id: string;
  is_correct: boolean;
  selected_answer: string[];
  correct_answer: string[];
  analysis: string;
  options: Array<{ label: string; text: string; is_correct: boolean }>;
  review: null | { status: string; wrong_count: number; next_review_at: string };
};

export type WrongQuestionSummary = {
  id: string;
  question_id: string;
  stem: string;
  subject: string;
  section: string;
  wrong_count: number;
  correct_streak: number;
  status: string;
  next_review_at: string;
  wrong_reason: string;
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

export async function getDashboard(): Promise<DashboardData> {
  return (await request<DataResponse<DashboardData>>("/api/v1/learning/dashboard/")).data;
}

export async function getSubjects(): Promise<SubjectSummary[]> {
  return (await request<DataResponse<SubjectSummary[]>>("/api/v1/learning/subjects/")).data;
}

export async function getChapters(subjectCode: string): Promise<{ subject: string; chapters: ChapterSummary[] }> {
  return (await request<DataResponse<{ subject: string; chapters: ChapterSummary[] }>>(
    `/api/v1/learning/subjects/${encodeURIComponent(subjectCode)}/chapters/`,
  )).data;
}

export async function getSection(sectionId: string): Promise<SectionDetail> {
  return (await request<DataResponse<SectionDetail>>(
    `/api/v1/learning/sections/${encodeURIComponent(sectionId)}/`,
  )).data;
}

export async function updateSectionProgress(
  sectionId: string,
  status: "started" | "completed",
): Promise<{ status: "started" | "completed"; completed_at: string | null }> {
  return (await csrfMutation<DataResponse<{ status: "started" | "completed"; completed_at: string | null }>>(
    `/api/v1/learning/sections/${encodeURIComponent(sectionId)}/progress/`,
    { method: "POST", body: JSON.stringify({ status }) },
  )).data;
}

export async function getQuickCard(offset: number): Promise<QuickCard | null> {
  return (await request<DataResponse<QuickCard | null>>(
    `/api/v1/learning/quick-card/?offset=${encodeURIComponent(String(offset))}`,
  )).data;
}

export async function getLearningReport(): Promise<LearningReport> {
  return (await request<DataResponse<LearningReport>>("/api/v1/learning/report/")).data;
}

export async function getNextQuestion(params: { subject?: string; section?: string; mode?: string }): Promise<PracticeQuestion | null> {
  const search = new URLSearchParams();
  if (params.subject) search.set("subject", params.subject);
  if (params.section) search.set("section", params.section);
  if (params.mode) search.set("mode", params.mode);
  const suffix = search.size ? `?${search.toString()}` : "";
  return (await request<DataResponse<PracticeQuestion | null>>(
    `/api/v1/learning/questions/next/${suffix}`,
  )).data;
}

export async function submitAttempt(payload: {
  question_version_id: string;
  selected_answer: string[];
  elapsed_seconds: number;
}): Promise<AttemptResult> {
  return (await csrfMutation<DataResponse<AttemptResult>>("/api/v1/learning/attempts/", {
    method: "POST",
    body: JSON.stringify({ ...payload, wrong_reason: "" }),
  })).data;
}

export async function updateWrongReason(attemptId: string, wrongReason: string): Promise<void> {
  await csrfMutation(`/api/v1/learning/attempts/${attemptId}/wrong-reason/`, {
    method: "PATCH",
    body: JSON.stringify({ wrong_reason: wrongReason }),
  });
}

export async function getWrongQuestions(): Promise<WrongQuestionSummary[]> {
  return (await request<DataResponse<WrongQuestionSummary[]>>(
    "/api/v1/learning/wrong-questions/",
  )).data;
}
