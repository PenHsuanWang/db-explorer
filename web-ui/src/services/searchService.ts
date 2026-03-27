import apiClient from './api'
import type { SearchRequest, SearchResponse } from '../types/api'

export async function search(request: SearchRequest): Promise<SearchResponse> {
  const response = await apiClient.post<SearchResponse>('/search', request)
  return response.data
}
