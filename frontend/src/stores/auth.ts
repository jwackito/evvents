import { create } from "zustand";
import type { User } from "@/types";

interface AuthState {
  token: string | null;
  refreshToken: string | null;
  user: User | null;
  isAuthenticated: boolean;
  login: (token: string, refreshToken: string, user: User) => void;
  logout: () => void;
  setUser: (user: User) => void;
}

function loadFromStorage(): { token: string | null; refreshToken: string | null; user: User | null } {
  try {
    const token = localStorage.getItem("auth_token");
    const refreshToken = localStorage.getItem("auth_refresh_token");
    const userRaw = localStorage.getItem("auth_user");
    return {
      token,
      refreshToken,
      user: userRaw ? (JSON.parse(userRaw) as User) : null,
    };
  } catch {
    return { token: null, refreshToken: null, user: null };
  }
}

function saveToStorage(token: string | null, refreshToken: string | null, user: User | null) {
  if (token && user) {
    localStorage.setItem("auth_token", token);
    localStorage.setItem("auth_refresh_token", refreshToken ?? "");
    localStorage.setItem("auth_user", JSON.stringify(user));
  } else {
    localStorage.removeItem("auth_token");
    localStorage.removeItem("auth_refresh_token");
    localStorage.removeItem("auth_user");
  }
}

const stored = loadFromStorage();

export const useAuthStore = create<AuthState>((set) => ({
  token: stored.token,
  refreshToken: stored.refreshToken,
  user: stored.user,
  isAuthenticated: stored.token !== null && stored.user !== null,

  login: (token, refreshToken, user) => {
    saveToStorage(token, refreshToken, user);
    set({ token, refreshToken, user, isAuthenticated: true });
  },

  logout: () => {
    saveToStorage(null, null, null);
    set({ token: null, refreshToken: null, user: null, isAuthenticated: false });
  },

  setUser: (user) => {
    const token = loadFromStorage().token;
    const refreshToken = loadFromStorage().refreshToken;
    saveToStorage(token, refreshToken, user);
    set({ user });
  },
}));
