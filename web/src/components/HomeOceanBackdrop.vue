<template>
  <div ref="container" class="ocean-backdrop" aria-hidden="true">
    <canvas ref="canvas" class="ocean-scene"></canvas>
    <div class="ocean-veil"></div>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, ref } from 'vue'

const container = ref(null)
const canvas = ref(null)
let dispose = () => {}

onMounted(() => {
  const element = canvas.value
  const context = element.getContext('2d')
  if (!context) return

  const ocean = new Image()
  ocean.src = '/illustrations/home-ocean/sea.webp'
  const images = {}
  for (const name of ['boat', 'cruise', 'cargo']) {
    images[name] = new Image()
    images[name].src = `/illustrations/home-ocean/${name}.webp`
  }

  const ships = [
    { type: 'boat', x: 0.08, y: 0.91, width: 0.10, speed: 0.0018, phase: 0, response: 1, direction: 1, trim: 0.99 },
    { type: 'cargo', x: 0.37, y: 0.88, width: 0.17, speed: 0.0012, phase: 1.8, response: 0.3, direction: 1, trim: 0.9 },
    { type: 'cruise', x: 0.78, y: 0.94, width: 0.21, speed: 0.0015, phase: 3.7, response: 0.45, direction: -1, trim: 0.97 },
    { type: 'boat', x: 0.92, y: 0.84, width: 0.045, speed: 0.001, phase: 5, response: 0.8, direction: 1, trim: 0.99 }
  ].sort((a, b) => a.y - b.y)
  const motion = window.matchMedia('(prefers-reduced-motion: reduce)')
  let width = 0
  let height = 0
  let elapsed = 0
  let previous = 0
  let frameId = 0
  let ready = false
  let disposed = false

  /** 绘制不同船型的随浪起伏、倒影和尾流。 */
  function drawShip(ship, time) {
    const image = images[ship.type]
    const sourceHeight = image.height * ship.trim
    const bw = Math.min(width * ship.width, height * ship.width * 2.15)
    const bh = bw * sourceHeight / image.width
    const span = width + bw * 2
    const position = ship.x * width + ship.direction * time * ship.speed * width
    const x = ((position + bw) % span + span) % span - bw
    const wave = Math.sin((x + bw / 2) * 0.008 - time * 0.6 + ship.phase)
      + 0.3 * Math.sin((x + bw / 2) * 0.017 - time * 0.93 + ship.phase * 0.7)
    const y = height * ship.y + wave * (0.65 + ship.response * 0.85)
    const roll = (Math.sin(x * 0.008 - time * 0.6 + ship.phase) * 0.0035
      + 0.2 * Math.sin(time * 0.93 + ship.phase) * 0.004) * ship.response

    context.save()
    context.translate(x + bw / 2, y)
    context.scale(ship.direction, 1)
    const wake = context.createLinearGradient(-bw * 1.2, 0, -bw * 0.35, 0)
    wake.addColorStop(0, 'rgba(225,246,255,0)')
    wake.addColorStop(1, 'rgba(239,251,255,.3)')
    context.strokeStyle = wake
    context.lineWidth = 1
    context.beginPath()
    context.moveTo(-bw * 0.38, 1)
    context.quadraticCurveTo(-bw * 0.85, 2 + wave, -bw * 1.3, 7 + wave)
    context.moveTo(-bw * 0.38, 1)
    context.quadraticCurveTo(-bw * 0.85, 1 - wave, -bw * 1.3, -2 - wave)
    context.stroke()
    context.save()
    context.globalAlpha = 0.07
    context.translate(0, 2)
    context.scale(1, -0.13)
    context.drawImage(image, 0, 0, image.width, sourceHeight, -bw / 2, -bh, bw, bh)
    context.restore()
    context.rotate(roll)
    context.drawImage(image, 0, 0, image.width, sourceHeight, -bw / 2, -bh, bw, bh)
    context.restore()
  }

  /** 绘制当前时刻的海面和船队。 */
  function draw() {
    if (!ready || !width || !height || disposed) return
    const scale = Math.max(width / ocean.width, height / ocean.height)
    const sw = width / scale
    const sh = height / scale
    const sx = (ocean.width - sw) / 2
    const sy = (ocean.height - sh) / 2
    context.clearRect(0, 0, width, height)
    context.drawImage(ocean, sx, sy, sw, sh, 0, 0, width, height)
    for (let y = Math.floor(height * 0.43); y < height; y += 2) {
      const depth = (y / height - 0.43) / 0.57
      const shift = (Math.sin(y * 0.028 - elapsed * 0.35)
        + 0.25 * Math.sin(y * 0.057 - elapsed * 0.61)) * depth * 1.25
      context.drawImage(ocean, sx, sy + y / scale, sw, 2 / scale, shift, y, width + 2, 2.2)
    }
    for (const ship of ships) drawShip(ship, elapsed)
  }

  /** 将连续动画限制为30帧并冻结后台时间。 */
  function frame(now) {
    frameId = 0
    if (disposed || document.hidden || motion.matches) return
    if (!previous || now - previous >= 1000 / 30) {
      elapsed += previous ? Math.min((now - previous) / 1000, 0.1) : 0
      previous = now
      draw()
    }
    frameId = requestAnimationFrame(frame)
  }

  /** 随页面可见性与减少动态效果设置启停循环。 */
  function syncMotion() {
    cancelAnimationFrame(frameId)
    frameId = 0
    previous = 0
    if (!disposed && ready && !document.hidden) {
      draw()
      if (!motion.matches) frameId = requestAnimationFrame(frame)
    }
  }

  /** 根据容器尺寸更新画布，避免高像素密度下过度渲染。 */
  function resize() {
    if (disposed || !container.value) return
    const bounds = container.value.getBoundingClientRect()
    width = bounds.width
    height = bounds.height
    const dpr = Math.min(window.devicePixelRatio || 1, 1.5)
    element.width = Math.max(1, Math.round(width * dpr))
    element.height = Math.max(1, Math.round(height * dpr))
    context.setTransform(dpr, 0, 0, dpr, 0, 0)
    draw()
  }

  const observer = new ResizeObserver(resize)
  observer.observe(container.value)
  motion.addEventListener('change', syncMotion)
  document.addEventListener('visibilitychange', syncMotion)
  resize()
  Promise.all([ocean.decode(), ...Object.values(images).map(image => image.decode())])
    .then(() => {
      if (disposed) return
      ready = true
      syncMotion()
    })
    .catch(() => { /* 船体素材或画布不可用时保留CSS静态背景。 */ })

  dispose = () => {
    disposed = true
    cancelAnimationFrame(frameId)
    observer.disconnect()
    motion.removeEventListener('change', syncMotion)
    document.removeEventListener('visibilitychange', syncMotion)
  }
})

onUnmounted(() => dispose())
</script>

<style scoped>
.ocean-backdrop {
  position: absolute;
  inset: 0;
  overflow: hidden;
  pointer-events: none;
  background: url('/illustrations/home-ocean/sea.webp') center / cover no-repeat;
  background-color: var(--main-100);
}
.ocean-scene, .ocean-veil { position: absolute; inset: 0; width: 100%; height: 100%; }
.ocean-veil {
  background: linear-gradient(180deg,
    color-mix(in srgb, var(--gray-0) 22%, transparent),
    color-mix(in srgb, var(--gray-0) 32%, transparent) 30%,
    color-mix(in srgb, var(--gray-0) 18%, transparent) 49%, transparent 75%);
}
:global(.dark) .ocean-veil {
  background: linear-gradient(180deg,
    color-mix(in srgb, var(--gray-0) 72%, transparent),
    color-mix(in srgb, var(--gray-0) 48%, transparent) 55%,
    color-mix(in srgb, var(--gray-0) 15%, transparent));
}
</style>
