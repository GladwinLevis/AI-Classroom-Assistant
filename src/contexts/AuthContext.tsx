import { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { apiFetch } from "@/services/api";
import type { UserRole, UserProfile } from "@/types";

interface AuthContextValue {
  user: UserProfile | null;
  isAuthenticated: boolean;
  loading: boolean;
  login: (email: string, password: string, role: UserRole) => Promise<void>;
  signup: (data: { first_name: string; last_name: string; email: string; password: string; role: UserRole }) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);

  // On mount, try to load user profile from stored token
  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (token) {
      apiFetch<any>("/users/me")
        .then((profile) => {
          setUser({
            id: profile.id,
            name: `${profile.first_name || ""} ${profile.last_name || ""}`.trim(),
            email: profile.email,
            role: profile.role || "student",
            avatarUrl: profile.avatar_url || "",
            grade: profile.grade || "",
            rollNumber: profile.roll_number || "",
          });
        })
        .catch(() => {
          localStorage.removeItem("access_token");
          localStorage.removeItem("refresh_token");
          setUser(null);
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (email: string, password: string, role: UserRole) => {
    const response = await apiFetch<any>("/auth/login", {
      method: "POST",
      body: { email, password, role },
    });

    localStorage.setItem("access_token", response.access_token);
    if (response.refresh_token) {
      localStorage.setItem("refresh_token", response.refresh_token);
    }

    const profile = response.user || (await apiFetch<any>("/users/me"));
    setUser({
      id: profile.id,
      name: `${profile.first_name || ""} ${profile.last_name || ""}`.trim() || profile.name || email,
      email: profile.email || email,
      role: profile.role || role,
      avatarUrl: profile.avatar_url || "",
      grade: profile.grade || "",
      rollNumber: profile.roll_number || "",
    });
  };

  const signup = async (data: { first_name: string; last_name: string; email: string; password: string; role: UserRole }) => {
    await apiFetch<any>("/auth/register", {
      method: "POST",
      body: data,
    });
  };

  const logout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{ user, isAuthenticated: !!user, loading, login, signup, logout }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
