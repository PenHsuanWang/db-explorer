import apiClient from './api'
import type { PeekRequest, PeekResponse } from '../types/api'

export async function peek(request: PeekRequest): Promise<PeekResponse> {
  const response = await apiClient.post<PeekResponse>('/peek', request)
  return response.data
}
