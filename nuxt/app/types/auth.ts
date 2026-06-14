export interface User {
  id: number
  username: string
  email: string
  role: 'admin' | 'user'
  is_active: boolean
  api_key: string | null
  rate_limit_per_minute: number
  created_at: string
}

export interface LoginRequest {
  username: string
  password: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  user: User
}

export interface ApiKeyResponse {
  api_key: string
  message: string
}

export interface UserCreate {
  username: string
  email: string
  password: string
  role?: 'admin' | 'user'
}

export interface UserUpdate {
  username?: string
  email?: string
  password?: string
  role?: 'admin' | 'user'
  is_active?: boolean
  rate_limit_per_minute?: number
}
