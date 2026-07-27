interface CustomErrorBody {
  status?: string;
  error?: {
    code?: string;
    message?: string;
    details?: { field?: string; msg?: string }[] | string;
  };
  detail?: string | { msg?: string; loc?: (string | number)[] }[];
}

export function extractErrorMessage(err: unknown, fallback: string): string {
  if (!err || typeof err !== 'object') return fallback;

  const body = (err as { error?: CustomErrorBody }).error;
  if (!body) return fallback;

  // Custom ErrorResponseEnvelope ({ error: { code, message, details } })
  if (body.error?.message) {
    return body.error.message;
  }

  // Detailed validation list from custom envelope
  if (Array.isArray(body.error?.details) && body.error.details.length > 0) {
    const first = body.error.details[0];
    if (typeof first === 'object' && first !== null) {
      if (first.field && first.msg) return `${first.field}: ${first.msg}`;
      if (first.msg) return first.msg;
    }
  }

  // Standard Starlette/FastAPI detail string/array
  if (typeof body.detail === 'string') {
    return body.detail;
  }
  if (Array.isArray(body.detail) && body.detail.length > 0) {
    const first = body.detail[0];
    if (typeof first === 'string') return first;
    if (first?.msg) return first.msg;
  }

  return fallback;
}
