import { getIdToken } from "../auth/auth";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

/**
 * Wraps fetch() to automatically:
 *  - prefix the API base URL
 *  - attach the current user's Cognito ID token as the Authorization header
 *  - parse JSON responses and throw on non-2xx statuses, so callers can
 *    just `await apiFetch(...)` and use try/catch instead of checking
 *    response.ok everywhere
 */
export async function apiFetch(path, options = {}) {
  const token = await getIdToken();
  if (!token) {
    throw new Error("Not logged in");
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      Authorization: token,
      ...(options.body ? { "Content-Type": "application/json" } : {}),
      ...options.headers,
    },
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(data.error || `Request failed (${response.status})`);
  }

  return data;
}
