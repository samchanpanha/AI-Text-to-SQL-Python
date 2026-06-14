export function formatDate(iso: string): string {
  if (!iso) return ''
  return new Date(iso).toLocaleString()
}

export function truncate(str: string, max: number): string {
  if (!str || str.length <= max) return str
  return str.slice(0, max) + '...'
}

export function maskApiKey(key: string): string {
  if (!key || key.length <= 12) return key || ''
  return key.slice(0, 8) + '...' + key.slice(-4)
}
