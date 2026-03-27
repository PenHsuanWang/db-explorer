import apiClient from './api'
import type { WorkbenchRequest, WorkbenchResponse } from '../types/api'

export async function fetchWorkbench(request: WorkbenchRequest): Promise<WorkbenchResponse> {
  const response = await apiClient.post<WorkbenchResponse>('/workbench', request)
  return response.data
}
