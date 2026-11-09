<template>
  <div class="document-motion" :class="{ paused }">
    <svg viewBox="0 0 400 320" aria-hidden="true">
      <ellipse cx="200" cy="286" rx="115" ry="10" class="ground" />
      <circle cx="200" cy="158" r="124" class="halo" />
      <g class="back-page page-left">
        <rect x="64" y="81" width="134" height="170" rx="16" />
        <path d="M87 114h79 M87 134h64 M87 154h70" />
      </g>
      <g class="back-page page-right">
        <rect x="211" y="76" width="125" height="165" rx="16" />
        <path d="M233 110h79 M233 130h64 M233 150h70" />
      </g>
      <g class="main-page">
        <rect x="122" y="105" width="155" height="178" rx="18" />
        <path d="M146 144h69 M146 165h102 M146 186h89 M146 207h72 M146 228h87" />
        <rect class="scan" x="134" y="125" width="131" height="5" rx="2" />
      </g>
      <path class="flight-line" d="M253 88 Q282 24 352 40" />
      <g class="plane">
        <path d="M308 38 367 20 344 68 333 49Z" />
        <path d="m333 49 34-29" />
      </g>
      <g class="verified">
        <circle cx="274" cy="242" r="27" />
        <path d="m262 242 8 8 16-18" />
      </g>
    </svg>
    <button :aria-pressed="paused" @click="paused = !paused">
      {{ paused ? '播放插画动效' : '暂停插画动效' }}
    </button>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const paused = ref(false)
</script>

<style scoped>
.document-motion { max-width: 360px; margin: 22px auto 0; text-align: center; }
svg { display: block; width: 100%; overflow: visible; }
.halo { fill: var(--main-50); }
.ground { fill: var(--main-100); opacity: 0.5; }
.back-page rect { fill: var(--gray-0); stroke: var(--main-200); }
.back-page path, .main-page path { fill: none; stroke: var(--main-200); stroke-width: 7; stroke-linecap: round; }
.page-left { transform: rotate(-12deg); transform-origin: 132px 168px; }
.page-right { transform: rotate(10deg); transform-origin: 270px 160px; }
.main-page rect { fill: var(--gray-0); stroke: var(--main-200); }
.main-page { animation: document-float 7s ease-in-out infinite; }
.main-page .scan { fill: var(--main-300); stroke: none; opacity: 0.55; animation: scan-page 5s ease-in-out infinite; }
.flight-line { fill: none; stroke: var(--main-300); stroke-width: 2; stroke-dasharray: 5 7; }
.plane { animation: plane-float 8s ease-in-out infinite; }
.plane path:first-child { fill: var(--main-200); stroke: var(--main-400); stroke-width: 1.5; }
.plane path:last-child { fill: none; stroke: var(--main-500); stroke-width: 1.5; }
.verified circle { fill: var(--main-600); stroke: var(--gray-0); stroke-width: 5; }
.verified path { fill: none; stroke: var(--brand-on-primary); stroke-width: 4; stroke-linecap: round; stroke-linejoin: round; }
.verified { animation: document-float 7s ease-in-out infinite reverse; }
button { margin-top: 8px; background: transparent; border: 0; padding: 5px 10px; color: var(--gray-600); font: inherit; font-size: 11px; cursor: pointer; border-radius: 14px; }
button:focus-visible { outline: 2px solid var(--main-400); }
.paused .main-page, .paused .scan, .paused .plane, .paused .verified { animation-play-state: paused; }
@keyframes document-float { 50% { transform: translateY(-7px); } }
@keyframes plane-float { 50% { transform: translate(5px,-7px) rotate(-3deg); } }
@keyframes scan-page { 50% { transform: translateY(125px); opacity: 0.2; } }
@media (prefers-reduced-motion: reduce) {
  .main-page, .scan, .plane, .verified { animation: none; }
  button { display: none; }
}
</style>
