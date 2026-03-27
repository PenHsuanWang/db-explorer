import apiClient from './api'
import type { User, LoginRequest, RegisterRequest } from '../types/auth'

export async function login(data: LoginRequest): Promise<User> {
  const response = await apiClient.post<User>('/auth/login', data)
  return response.data
}

export async function register(data: RegisterRequest): Promise<User> {
  const response = await apiClient.post<User>('/auth/register', data)
  return response.data
}

export async function logout(): Promise<void> {
  await apiClient.post('/auth/logout')
}

export async function getMe(): Promise<User> {
  const response = await apiClient.get<User>('/auth/me')
  return response.data
}
