export interface Job {
  id: string
  job_type: string
  status: 'PENDING' | 'STARTED' | 'PROGRESS' | 'SUCCESS' | 'FAILURE'
  payload: Record<string, unknown> | null
  progress_meta: JobProgress | null
  result_data: Record<string, unknown> | null
  error_message: string | null
  created_at: string
  updated_at: string
}

export interface JobProgress {
  current: number
  total: number
  percent: number
  message: string
}

export interface JobCreate {
  job_type: string
  payload: Record<string, unknown>
}
