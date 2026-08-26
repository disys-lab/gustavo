import apiClient from "./client";
import type { ApiResponse } from "@/lib/types/api";
import type { NebulaUser, UserGroup, CredentialResponse } from "@/lib/types/users";

export const listUsers = () =>
  apiClient.get<ApiResponse<{ users: NebulaUser[] }>>("/users").then((r) => r.data);

export const getMyGroups = () =>
  apiClient.get<ApiResponse<{ groups: string[] }>>("/users/me/groups").then((r) => r.data);

export const createUser = (username: string, group?: string) =>
  apiClient.post<ApiResponse<CredentialResponse>>("/users", { username, group }).then((r) => r.data);

export const deleteUser = (username: string) =>
  apiClient.delete<ApiResponse<string>>(`/users/${username}`).then((r) => r.data);

export const regenerateUserToken = (username: string) =>
  apiClient.post<ApiResponse<CredentialResponse>>(`/users/${username}/regenerate-token`).then((r) => r.data);

export const regenerateMyToken = () =>
  apiClient.post<ApiResponse<CredentialResponse>>("/users/me/regenerate-token").then((r) => r.data);

export const listGroups = () =>
  apiClient.get<ApiResponse<{ groups: UserGroup[] }>>("/users/groups").then((r) => r.data);

export const createGroup = (group: Omit<UserGroup, "name"> & { name: string }) =>
  apiClient.post<ApiResponse<string>>("/users/groups", group).then((r) => r.data);

export const updateGroup = (name: string, partial: Partial<Omit<UserGroup, "name">>) =>
  apiClient.put<ApiResponse<string>>(`/users/groups/${name}`, partial).then((r) => r.data);

export const addGroupGrant = (
  name: string,
  resource_type: "app" | "device_group",
  resource_name: string,
  perm: "ro" | "rw"
) =>
  apiClient
    .post<ApiResponse<string>>(`/users/groups/${name}/grants`, { resource_type, resource_name, perm })
    .then((r) => r.data);

export const removeGroupGrant = (name: string, resource_type: "app" | "device_group", resource_name: string) =>
  apiClient
    .post<ApiResponse<string>>(`/users/groups/${name}/grants/revoke`, { resource_type, resource_name })
    .then((r) => r.data);

export const deleteGroup = (name: string) =>
  apiClient.delete<ApiResponse<string>>(`/users/groups/${name}`).then((r) => r.data);
