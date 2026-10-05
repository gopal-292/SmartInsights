"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import { api, authApi, type User } from "./api";
import { authClient } from "./auth-client";

type AuthContextValue = {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (fullName: string, email: string, password: string) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

function withTimeout<T>(promise: Promise<T>, ms: number): Promise<T> {
  return Promise.race([
    promise,
    new Promise<T>((_, reject) =>
      setTimeout(() => reject(new Error("Auth service timeout")), ms)
    ),
  ]);
}

function backendUnavailableMessage(error: unknown): string {
  const msg = error instanceof Error ? error.message : String(error);
  if (
    msg.includes("Failed to fetch") ||
    msg.includes("NetworkError") ||
    msg.includes("fetch")
  ) {
    return (
      "Cannot reach the SmartInsights API. Start the backend with .\\start-backend.ps1 " +
      "from the project folder, then try again."
    );
  }
  return msg;
}

async function bridgeToApi(email: string, fullName: string, betterAuthUserId?: string) {
  const data = await api<{ access_token: string; user: User }>("/auth/bridge", {
    method: "POST",
    body: JSON.stringify({
      email,
      full_name: fullName,
      better_auth_user_id: betterAuthUserId || null,
    }),
  });
  localStorage.setItem("si_token", data.access_token);
  return data.user;
}

/** Sync Better Auth in the background when PostgreSQL is available (PPT stack). */
function syncBetterAuth(
  mode: "signUp" | "signIn",
  email: string,
  password: string,
  fullName?: string
) {
  void (async () => {
    try {
      if (mode === "signUp" && fullName) {
        await authClient.signUp.email({ email, password, name: fullName });
      } else {
        await authClient.signIn.email({ email, password });
      }
    } catch {
      /* PostgreSQL / Better Auth optional in local dev */
    }
  })();
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function bootstrap() {
      // FastAPI JWT first — works with SQLite when Docker/Postgres is offline.
      const token = localStorage.getItem("si_token");
      if (token) {
        try {
          const me = await authApi.me();
          if (!cancelled) setUser(me);
          return;
        } catch {
          localStorage.removeItem("si_token");
        }
      }

      // Optional: restore session from Better Auth when PostgreSQL is up.
      try {
        const session = await withTimeout(authClient.getSession(), 4000);
        const baUser = session.data?.user;
        if (baUser?.email) {
          const bridged = await bridgeToApi(
            baUser.email,
            baUser.name || baUser.email.split("@")[0],
            baUser.id
          );
          if (!cancelled) setUser(bridged);
          return;
        }
      } catch {
        /* Better Auth offline — not required for local dev */
      }

      if (!cancelled) setUser(null);
      if (!cancelled) setLoading(false);
    }

    bootstrap().finally(() => {
      if (!cancelled) setLoading(false);
    });

    return () => {
      cancelled = true;
    };
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    // Primary: FastAPI (SQLite fallback, no Docker required).
    try {
      const data = await authApi.login({ email, password });
      localStorage.setItem("si_token", data.access_token);
      setUser(data.user);
      syncBetterAuth("signIn", email, password);
      return;
    } catch (primaryError) {
      // Fallback: Better Auth when user exists only in PostgreSQL.
      try {
        const result = await authClient.signIn.email({ email, password });
        if (result.error) {
          throw primaryError;
        }
        const baUser = result.data?.user;
        const bridged = await bridgeToApi(
          email,
          baUser?.name || email.split("@")[0],
          baUser?.id
        );
        setUser(bridged);
        return;
      } catch {
        throw new Error(backendUnavailableMessage(primaryError));
      }
    }
  }, []);

  const register = useCallback(
    async (fullName: string, email: string, password: string) => {
      try {
        const data = await authApi.register({
          full_name: fullName,
          email,
          password,
        });
        localStorage.setItem("si_token", data.access_token);
        setUser(data.user);
        syncBetterAuth("signUp", email, password, fullName);
        return;
      } catch (primaryError) {
        try {
          const result = await authClient.signUp.email({
            email,
            password,
            name: fullName,
          });
          if (result.error) {
            throw primaryError;
          }
          const baUser = result.data?.user;
          const bridged = await bridgeToApi(email, fullName, baUser?.id);
          setUser(bridged);
          return;
        } catch {
          throw new Error(backendUnavailableMessage(primaryError));
        }
      }
    },
    []
  );

  const logout = useCallback(() => {
    void authClient.signOut().catch(() => {});
    localStorage.removeItem("si_token");
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({ user, loading, login, register, logout }),
    [user, loading, login, register, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
