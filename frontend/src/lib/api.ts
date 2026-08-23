const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export type User = {
  id: number;
  email: string;
  full_name: string;
  created_at: string;
};

export type BusinessProfile = {
  id: number;
  user_id: number;
  business_name: string;
  business_type: string;
  industry: string;
  location: string;
  currency: string;
  business_size: string;
  created_at: string;
  updated_at: string;
};

function getToken() {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("si_token");
}

export async function api<T>(
  path: string,
  options: RequestInit = {},
  isForm = false
): Promise<T> {
  const headers = new Headers(options.headers || {});
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (!isForm && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    let detail = "Request failed";
    try {
      const data = await res.json();
      detail = data.detail || detail;
    } catch {
      /* ignore */
    }
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

/** Authenticated binary download (e.g. PDF). Triggers a browser file save. */
export async function downloadFile(path: string, fallbackFilename: string): Promise<void> {
  const headers = new Headers();
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const res = await fetch(`${API_URL}${path}`, { headers });
  if (!res.ok) {
    let detail = "Download failed";
    try {
      const data = await res.json();
      detail = data.detail || detail;
    } catch {
      /* ignore */
    }
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }

  const disposition = res.headers.get("Content-Disposition") || "";
  const match = /filename="?([^"]+)"?/i.exec(disposition);
  const filename = match?.[1] || fallbackFilename;
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}


export const authApi = {
  register: (body: { email: string; full_name: string; password: string }) =>
    api<{ access_token: string; user: User }>("/auth/register", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  login: (body: { email: string; password: string }) =>
    api<{ access_token: string; user: User }>("/auth/login", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  me: () => api<User>("/auth/me"),
};

export const businessApi = {
  get: () => api<BusinessProfile | null>("/business/profile"),
  save: (body: Omit<BusinessProfile, "id" | "user_id" | "created_at" | "updated_at">) =>
    api<BusinessProfile>("/business/profile", {
      method: "POST",
      body: JSON.stringify(body),
    }),
};

export const uploadApi = {
  list: () => api<Array<Record<string, unknown>>>("/upload/datasets"),
  upload: (file: File, dataType = "auto") => {
    const form = new FormData();
    form.append("file", file);
    form.append("data_type", dataType);
    return api<Record<string, unknown>>(
      "/upload",
      { method: "POST", body: form },
      true
    );
  },
  remove: (id: number) =>
    api<{ message: string }>(`/upload/datasets/${id}`, { method: "DELETE" }),
};
