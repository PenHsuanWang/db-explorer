import api from './api'
import type { Job, JobCreate } from '../types/job'

export async function listJobs(): Promise<Job[]> {
  const { data } = await api.get('/jobs')
  return data
}

export async function getJob(id: string): Promise<Job> {
  const { data } = await api.get(`/jobs/${id}`)
  return data
}

export async function createJob(body: JobCreate): Promise<Job> {
  const { data } = await api.post('/jobs', body)
  return data
}

export async function deleteJob(id: string): Promise<void> {
  await api.delete(`/jobs/${id}`)
}
