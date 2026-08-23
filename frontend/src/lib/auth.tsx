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

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function bootstrap() {
      try {
        const session = await authClient.getSession();
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

        // Fallback: existing FastAPI JWT (demo accounts)
        const token = localStorage.getItem("si_token");
        if (token) {
          const me = await authApi.me();
          if (!cancelled) setUser(me);
        }
      } catch {
        localStorage.removeItem("si_token");
        if (!cancelled) setUser(null);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    bootstrap();
    return () => {
      cancelled = true;
    };
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const result = await authClient.signIn.email({ email, password });
    if (result.error) {
      // Fallback to FastAPI auth if Better Auth user doesn't exist yet
      try {
        const data = await authApi.login({ email, password });
        localStorage.setItem("si_token", data.access_token);
        setUser(data.user);
        return;
      } catch {
        throw new Error(result.error.message || "Login failed");
      }
    }
    const baUser = result.data?.user;
    const bridged = await bridgeToApi(
      email,
      baUser?.name || email.split("@")[0],
      baUser?.id
    );
    setUser(bridged);
  }, []);

  const register = useCallback(
    async (fullName: string, email: string, password: string) => {
      const result = await authClient.signUp.email({
        email,
        password,
        name: fullName,
      });
      if (result.error) {
        // Fallback when PostgreSQL/Better Auth is offline — still create FastAPI user
        try {
          const data = await authApi.register({
            full_name: fullName,
            email,
            password,
          });
          localStorage.setItem("si_token", data.access_token);
          setUser(data.user);
          return;
        } catch {
          throw new Error(
            result.error.message ||
              "Registration failed. Start PostgreSQL with `docker compose up -d` for Better Auth."
          );
        }
      }
      const baUser = result.data?.user;
      const bridged = await bridgeToApi(email, fullName, baUser?.id);
      setUser(bridged);
    },
    []
  );

  const logout = useCallback(() => {
    void authClient.signOut();
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
