import axios from 'axios'

const configuredApiBase = import.meta.env.VITE_API_URL?.trim()
const API_BASE = configuredApiBase || ''

export const httpClient = axios.create({
  baseURL: API_BASE
})

httpClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

httpClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const message = error?.response?.data?.error || error?.response?.data?.message || error?.message || 'Error de red'
    return Promise.reject(new Error(message))
  }
)

export default httpClient
