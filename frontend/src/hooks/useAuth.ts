import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { post, get } from "@/services/api";
import { useAuthStore } from "@/stores/auth";
import type { AuthResponse, User } from "@/types";

export function useLogin() {
  const login = useAuthStore((s) => s.login);
  return useMutation({
    mutationFn: (data: { email: string; password: string }) =>
      post<AuthResponse>("/api/v1/auth/login", data),
    onSuccess: (res) => {
      login(res.access_token, res.refresh_token, res.user);
    },
  });
}

export function useRegister() {
  const login = useAuthStore((s) => s.login);
  return useMutation({
    mutationFn: (data: { email: string; password: string; name: string }) =>
      post<AuthResponse>("/api/v1/auth/register", data),
    onSuccess: (res) => {
      login(res.access_token, res.refresh_token, res.user);
    },
  });
}

export function useRequestMagicLink() {
  return useMutation({
    mutationFn: (data: { email: string }) =>
      post<{ message: string }>("/api/v1/auth/magic-link", data),
  });
}

export function useMe() {
  const token = useAuthStore((s) => s.token);
  const setUser = useAuthStore((s) => s.setUser);
  return useQuery({
    queryKey: ["me"],
    queryFn: () => get<User>("/api/v1/auth/me"),
    enabled: !!token,
    onSuccess: (user) => {
      setUser(user);
    },
  });
}

export function useLogout() {
  const logout = useAuthStore((s) => s.logout);
  const queryClient = useQueryClient();
  return () => {
    logout();
    queryClient.clear();
  };
}
