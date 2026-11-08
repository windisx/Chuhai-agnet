import { BRAND } from '../config/brand.js'

export const AVATAR_BACKGROUND_TOKENS = [
  { background: 'var(--main-50)', color: 'var(--main-700)' },
  { background: 'var(--main-100)', color: 'var(--main-800)' },
  { background: 'var(--gray-100)', color: 'var(--gray-800)' }
]

const normalizeSeed = (id) => {
  if (id === null || id === undefined || String(id).trim() === '') {
    throw new Error('generatePixelAvatar requires an id')
  }
  return String(id).trim()
}

// 保留原调用入口，默认头像使用本地素材，不向第三方传递用户标识。
export const generatePixelAvatar = (id, kind = 'user') => {
  normalizeSeed(id)
  return kind === 'agent' ? BRAND.assistantAvatar : BRAND.userAvatar
}

export const getAvatarInitials = (name, kind = 'user') => {
  const fallback = kind === 'agent' ? '智能' : '用户'
  const normalizedName = String(name || '').trim()
  if (!normalizedName) return fallback
  return Array.from(normalizedName).slice(0, 2).join('')
}

export const getAvatarColorIndex = (seed) => {
  const normalizedSeed = String(seed || '').trim()
  const value = normalizedSeed || 'avatar'
  let hash = 0
  for (const char of value) {
    hash = (hash * 31 + char.codePointAt(0)) >>> 0
  }
  return hash % AVATAR_BACKGROUND_TOKENS.length
}

export const getAvatarFallbackStyle = (seed) => AVATAR_BACKGROUND_TOKENS[getAvatarColorIndex(seed)]
