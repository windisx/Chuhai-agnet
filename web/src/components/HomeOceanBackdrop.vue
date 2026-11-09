<template>
  <div class="ocean-backdrop">
    <div class="ocean-light light-one" aria-hidden="true"></div>
    <div class="ocean-light light-two" aria-hidden="true"></div>
    <svg class="ocean-scene" viewBox="0 0 1600 1000" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
      <defs>
        <linearGradient id="home-wave-fill" x1="0" y1="0" x2="0.8" y2="1">
          <stop offset="0%" stop-color="currentColor" stop-opacity="0.02" />
          <stop offset="100%" stop-color="currentColor" stop-opacity="0.2" />
        </linearGradient>
        <linearGradient id="home-route-stroke">
          <stop offset="0%" stop-color="currentColor" stop-opacity="0" />
          <stop offset="50%" stop-color="currentColor" stop-opacity="0.45" />
          <stop offset="100%" stop-color="currentColor" stop-opacity="0" />
        </linearGradient>
      </defs>
      <g class="ocean-layer layer-far">
        <path d="M-200 710 C180 450 410 1050 880 740 S1470 510 1800 690 V1200 H-200Z" fill="url(#home-wave-fill)" />
        <path v-for="n in 11" :key="n" :d="`M-200 ${710+n*17} C180 ${450+n*17} 410 ${1050+n*17} 880 ${740+n*17} S1470 ${510+n*17} 1800 ${690+n*17}`" class="wave-line" />
      </g>
      <g class="ocean-layer layer-near">
        <path d="M-200 840 C200 1050 520 610 950 810 S1510 1090 1800 740 V1200 H-200Z" fill="url(#home-wave-fill)" />
        <path v-for="n in 9" :key="n" :d="`M-200 ${840+n*19} C200 ${1050+n*19} 520 ${610+n*19} 950 ${810+n*19} S1510 ${1090+n*19} 1800 ${740+n*19}`" class="wave-line" />
      </g>
      <g class="routes" fill="none" stroke="url(#home-route-stroke)">
        <path d="M-100 460 Q380 30 940 180 T1750 240" />
        <path d="M1080 -100 Q1550 200 1410 620 T1260 1150" />
      </g>
      <g class="route-travel" fill="none" stroke="currentColor">
        <path d="M-100 460 Q380 30 940 180 T1750 240" />
        <path d="M1080 -100 Q1550 200 1410 620 T1260 1150" />
      </g>
    </svg>
  </div>
</template>

<style scoped>
.ocean-backdrop {
  position: absolute;
  inset: 0;
  overflow: hidden;
  pointer-events: none;
  color: var(--main-500);
}
.ocean-scene { position: absolute; width: 100%; height: 100%; inset: 0; }
.ocean-light {
  position: absolute;
  width: 75vw;
  height: 75vw;
  border-radius: 50%;
  background: radial-gradient(ellipse, var(--main-100), transparent 65%);
  opacity: 0.55;
  animation: light-drift 24s ease-in-out infinite alternate;
}
.light-one { top: -65vw; right: -15vw; }
.light-two { bottom: -50vw; left: -28vw; animation-delay: -12s; }
.ocean-layer { transform-origin: center; animation: ocean-drift 24s ease-in-out infinite alternate; }
.layer-far { opacity: 0.65; }
.layer-near { opacity: 0.6; animation-duration: 32s; animation-delay: -12s; }
.wave-line { fill: none; stroke: currentColor; stroke-width: 0.8; opacity: 0.15; }
.routes { stroke-width: 1; opacity: 0.65; }
.route-travel { stroke-width: 2; stroke-linecap: round; stroke-dasharray: 3 1800; opacity: 0.5; animation: route-flow 32s linear infinite; }
@keyframes ocean-drift { from { transform: translate(-28px, 14px) rotate(-2deg); } to { transform: translate(28px, -18px) rotate(2deg); } }
@keyframes light-drift { to { transform: translate(8%, 14%) scale(1.12); } }
@keyframes route-flow { to { stroke-dashoffset: -1803; } }
@media (max-width: 768px) {
  .layer-far { opacity: 0.5; }
}
@media (prefers-reduced-motion: reduce) {
  .ocean-light, .ocean-layer, .route-travel { animation: none; }
}
</style>
