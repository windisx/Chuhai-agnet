import assert from 'node:assert/strict'
import test from 'node:test'

import {
  AVATAR_BACKGROUND_TOKENS,
  generatePixelAvatar,
  getAvatarColorIndex,
  getAvatarFallbackStyle,
  getAvatarInitials
} from '../../src/utils/pixelAvatar.js'

test('local avatars preserve roles without disclosing identifiers to an external service', () => {
  assert.equal(generatePixelAvatar('user-001'), '/illustrations/user.jpg')
  assert.equal(generatePixelAvatar(' user/中文 '), '/illustrations/user.jpg')
  assert.match(
    generatePixelAvatar('agent-001', 'agent'),
    /^\/illustrations\/agents\/agent-[1-9]\.jpg$/
  )
  assert.equal(generatePixelAvatar('agent-001', 'agent'), generatePixelAvatar('agent-001', 'agent'))
  const agentAvatars = new Set(
    Array.from({ length: 9 }, (_, i) => generatePixelAvatar(`agent-${i}`, 'agent'))
  )
  assert.equal(agentAvatars.size, 9)
  assert.throws(() => generatePixelAvatar(''), /requires an id/)
  assert.throws(() => generatePixelAvatar(null), /requires an id/)

  assert.equal(getAvatarInitials('张三丰', 'user'), '张三')
  assert.equal(getAvatarInitials('Alice', 'user'), 'Al')
  assert.equal(getAvatarInitials('', 'user'), '用户')
  assert.equal(getAvatarInitials('', 'agent'), '智能')

  const first = getAvatarColorIndex('user-001')
  assert.equal(first, getAvatarColorIndex('user-001'))
  assert.notEqual(first, getAvatarColorIndex('user-002'))
  assert.ok(first >= 0 && first < AVATAR_BACKGROUND_TOKENS.length)

  const style = getAvatarFallbackStyle('agent-001')
  assert.equal(typeof style.background, 'string')
  assert.equal(typeof style.color, 'string')
})
