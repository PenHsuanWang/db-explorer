import apiClient from './api'
import type { ConnectionsResponse } from '../types/api'

export async function getConnections(): Promise<ConnectionsResponse> {
  const response = await apiClient.get<ConnectionsResponse>('/connections')
  return response.data
}

export async function deleteConnection(id: string): Promise<void> {
  await apiClient.delete(`/connections/${id}`)
}
