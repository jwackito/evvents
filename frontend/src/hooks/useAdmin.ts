import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useAuthStore } from "@/stores/auth";
import { get, post, put, del } from "@/services/api";
import { useToast } from "@/stores/toast";
import type { Organization, User, PaginatedResponse } from "@/types";

export function useAdminOrgs(page = 1) {
  const token = useAuthStore((s) => s.token);
  return useQuery({
    queryKey: ["admin-orgs", page],
    queryFn: () =>
      get<PaginatedResponse<Organization>>(`/api/v1/admin/orgs?page=${page}&per_page=20`),
    enabled: !!token,
  });
}

export function useCreateOrg() {
  const queryClient = useQueryClient();
  const toast = useToast();
  return useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      post<{ data: Organization }>("/api/v1/admin/orgs", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-orgs"] });
      toast.success("Organization created");
    },
    onError: (err: Error) => toast.error(err.message),
  });
}

export function useUpdateOrg() {
  const queryClient = useQueryClient();
  const toast = useToast();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Record<string, unknown> }) =>
      put<{ data: Organization }>(`/api/v1/admin/orgs/${id}`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-orgs"] });
      toast.success("Organization updated");
    },
    onError: (err: Error) => toast.error(err.message),
  });
}

export function useDeleteOrg() {
  const queryClient = useQueryClient();
  const toast = useToast();
  return useMutation({
    mutationFn: (id: string) => del(`/api/v1/admin/orgs/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-orgs"] });
      toast.success("Organization deleted");
    },
    onError: (err: Error) => toast.error(err.message),
  });
}

export function useAdminUsers(page = 1) {
  const token = useAuthStore((s) => s.token);
  return useQuery({
    queryKey: ["admin-users", page],
    queryFn: () =>
      get<PaginatedResponse<User>>(`/api/v1/admin/users?page=${page}&per_page=20`),
    enabled: !!token,
  });
}

export function useCreateUser() {
  const queryClient = useQueryClient();
  const toast = useToast();
  return useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      post<{ data: User }>("/api/v1/admin/users", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-users"] });
      toast.success("User created");
    },
    onError: (err: Error) => toast.error(err.message),
  });
}

export function useUpdateUser() {
  const queryClient = useQueryClient();
  const toast = useToast();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Record<string, unknown> }) =>
      put<{ data: User }>(`/api/v1/admin/users/${id}`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-users"] });
      toast.success("User updated");
    },
    onError: (err: Error) => toast.error(err.message),
  });
}

export function useDeleteUser() {
  const queryClient = useQueryClient();
  const toast = useToast();
  return useMutation({
    mutationFn: (id: string) => del(`/api/v1/admin/users/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-users"] });
      toast.success("User deleted");
    },
    onError: (err: Error) => toast.error(err.message),
  });
}
