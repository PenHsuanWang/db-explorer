import api from './api'

export interface SavedWorkbench {
  id: string
  name: string
  panes_config: Record<string, unknown>
  cleaning_cfg: Record<string, unknown>
  created_at: string
  updated_at: string
}

export interface SavedWorkbenchCreate {
  name: string
  panes_config: Record<string, unknown>
  cleaning_cfg: Record<string, unknown>
}

export async function listSavedWorkbenches(): Promise<SavedWorkbench[]> {
  const { data } = await api.get('/workbench/saved')
  return data
}

export async function getSavedWorkbench(id: string): Promise<SavedWorkbench> {
  const { data } = await api.get(`/workbench/saved/${id}`)
  return data
}

export async function createSavedWorkbench(body: SavedWorkbenchCreate): Promise<SavedWorkbench> {
  const { data } = await api.post('/workbench/saved', body)
  return data
}

export async function deleteSavedWorkbench(id: string): Promise<void> {
  await api.delete(`/workbench/saved/${id}`)
}
