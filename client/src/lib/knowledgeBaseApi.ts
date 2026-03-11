const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export interface KnowledgeBaseQueryParams {
  courseId: string;
  search?: string;
  category?: string;
  page?: number;
  token: string;
}

export async function fetchKnowledgeBase({
  courseId,
  search,
  category,
  page = 1,
  token,
}: KnowledgeBaseQueryParams) {
  const params = new URLSearchParams();
  params.set("course_id", courseId);
  params.set("page", String(page));
  if (search) params.set("search", search);
  if (category) params.set("category", category);

  const res = await fetch(`${API_URL}/knowledge-base?${params.toString()}`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  return res.json();
}

export interface SimilarQuestionsParams {
  courseId: string;
  title: string;
  token: string;
}

export async function fetchSimilarQuestions({
  courseId,
  title,
  token,
}: SimilarQuestionsParams) {
  const params = new URLSearchParams();
  params.set("course_id", courseId);
  params.set("title", title);

  const res = await fetch(
    `${API_URL}/knowledge-base/similar?${params.toString()}`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  return res.json();
}

export async function markQuestionHelpful({
  questionId,
  token,
}: {
  questionId: string;
  token: string;
}) {
  const res = await fetch(`${API_URL}/questions/${questionId}/helpful`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  return res.json();
}

