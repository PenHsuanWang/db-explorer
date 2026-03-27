import apiClient from './api'
import type { Connection, ConnectionsResponse } from '../types/api'

export async function getConnections(): Promise<ConnectionsResponse> {
  const response = await apiClient.get<ConnectionsResponse>('/connections')
  return response.data
}

export async function createConnection(conn: Connection): Promise<Connection> {
  const response = await apiClient.post<Connection>('/connections', conn)
  return response.data
}

export async function deleteConnection(id: string): Promise<void> {
  await apiClient.delete(`/connections/${id}`)
}
