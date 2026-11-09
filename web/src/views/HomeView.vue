<template>
  <div class="home-container">
    <div v-if="isLoading" class="loading-container" role="status">
      <a-spin size="large" />
      <p>正在连接服务…</p>
    </div>
    <div v-else-if="error" class="error-container">
      <a-result status="error" :title="error.title" :sub-title="error.message">
        <template #extra><a-button type="primary" @click="retryLoad">重试</a-button></template>
      </a-result>
    </div>
    <template v-else>
      <HomeOceanBackdrop :paused="backgroundPaused" />
      <header class="site-header">
        <div class="logo">
          <img :src="BRAND.logo" :alt="BRAND.name" class="logo-img" />
          <span>{{ BRAND.name }}</span>
        </div>
        <UserInfoComponent :show-button="true" />
      </header>
      <main class="hero-section">
        <div class="hero-content">
          <p class="hero-eyebrow">出海资料预审智能体</p>
          <h1>资料有据，<span>出海有序。</span></h1>
          <p class="subtitle">{{ currentSubtitle }}</p>
          <button class="start-button lucide-icon-btn" @click="goToChat">
            <span>开始体验</span><ArrowRight :size="20" />
          </button>
        </div>
      </main>
      <footer class="footer">
        <span>{{ BRAND.footer }}</span>
        <button class="motion-toggle" :aria-pressed="backgroundPaused" @click="backgroundPaused = !backgroundPaused">
          {{ backgroundPaused ? '播放背景动效' : '暂停背景动效' }}
        </button>
      </footer>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useInfoStore } from '@/stores/info'
import { healthApi } from '@/apis/system_api'
import UserInfoComponent from '@/components/UserInfoComponent.vue'
import { ArrowRight } from '@lucide/vue'
import { BRAND } from '@/config/brand'
import HomeOceanBackdrop from '@/components/HomeOceanBackdrop.vue'

const router = useRouter()
const userStore = useUserStore()
const infoStore = useInfoStore()

// 加载状态
const isLoading = ref(true)
const error = ref(null)
const subtitleIndex = ref(0)
const backgroundPaused = ref(false)
let subtitleTimer = null

const subtitleOptions = computed(() => [BRAND.subtitle])

const currentSubtitle = computed(() => subtitleOptions.value[subtitleIndex.value] || '')

const stopSubtitleCarousel = () => {
  if (subtitleTimer) {
    clearInterval(subtitleTimer)
    subtitleTimer = null
  }
}

const startSubtitleCarousel = () => {
  stopSubtitleCarousel()
  subtitleIndex.value = 0

  if (subtitleOptions.value.length <= 1) {
    return
  }

  subtitleTimer = setInterval(() => {
    subtitleIndex.value = (subtitleIndex.value + 1) % subtitleOptions.value.length
  }, 2800)
}

const checkHealth = async () => {
  try {
    const response = await healthApi.checkHealth()
    if (response.status !== 'ok') {
      throw new Error('服务不可用')
    }
  } catch (e) {
    error.value = {
      title: '服务连接失败',
      message: '后端服务无法响应，请检查服务是否正常运行'
    }
    throw e
  }
}

const loadData = async () => {
  isLoading.value = true
  error.value = null

  try {
    // 先检查健康状态
    await checkHealth()
    // 健康检查通过后加载配置
    await infoStore.loadInfoConfig()
    startSubtitleCarousel()
  } catch (e) {
    console.error('加载失败:', e)
    stopSubtitleCarousel()
  } finally {
    isLoading.value = false
  }
}

const retryLoad = () => {
  loadData()
}

const goToChat = async () => {
  if (!userStore.isLoggedIn) {
    sessionStorage.setItem('redirect', '/')
    router.push('/login')
    return
  }

  router.push('/agent')
}

onMounted(() => {
  loadData()
})

onUnmounted(() => {
  stopSubtitleCarousel()
})
</script>

<style lang="less" scoped>
.home-container {
  position: relative;
  isolation: isolate;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--gray-10);
  color: var(--gray-1000);
  overflow: hidden;
}
.site-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 28px 40px;
  gap: 24px;
  z-index: 1;
}
.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 22px;
  font-weight: 650;
}
.logo-img {
  width: 38px;
  height: 38px;
}

.logo span {
  font-weight: 650;
}
.hero-section {
  flex: 1;
  display: grid;
  place-items: center;
  padding: 72px 24px 100px;
  text-align: center;
  z-index: 1;
}
.hero-content {
  width: 100%;
  max-width: 1080px;
}
.hero-eyebrow {
  display: inline-block;
  padding: 7px 17px;
  border: 1px solid var(--gray-150);
  border-radius: 24px;
  background: var(--gray-50);
  color: var(--gray-700);
  font-size: 13px;
  font-weight: 500;
  margin-bottom: 30px;
}
h1 {
  font-size: 60px;
  line-height: 1.35;
  font-weight: 650;
  margin: 0 0 28px;
}
h1 span {
  color: var(--gray-600);
  font-weight: inherit;
  margin-left: 12px;
}
.subtitle {
  margin: 0 auto;
  color: var(--gray-600);
  font-size: 18px;
  line-height: 1.8;
}
.start-button {
  margin-top: 42px;
  padding: 15px 34px;
  border: 1px solid var(--main-color);
  border-radius: 28px;
  background: var(--main-color);
  color: var(--brand-on-primary);
  gap: 12px;
  font-size: 16px;
  font-weight: 550;
  box-shadow: 0 8px 24px var(--shadow-2);
  cursor: pointer;
  transition:
    background 0.18s ease,
    box-shadow 0.18s ease;
}
.start-button:hover {
  background: var(--main-700);
  box-shadow: 0 10px 28px var(--shadow-3);
}
.start-button:focus-visible {
  outline: 3px solid var(--main-200);
  outline-offset: 4px;
}
.footer {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  z-index: 1;
  padding: 28px 20px;
  text-align: center;
  color: var(--gray-600);
  font-size: 12px;
}
.motion-toggle {
  border: 1px solid var(--gray-200);
  border-radius: 20px;
  padding: 6px 12px;
  background: var(--gray-10);
  color: var(--gray-600);
  font: inherit;
  font-size: 11px;
  cursor: pointer;
}
.motion-toggle:focus-visible {
  outline: 3px solid var(--main-200);
  outline-offset: 3px;
}
.loading-container,
.error-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 24px;
  gap: 16px;
  color: var(--gray-600);
}
@media (max-width: 768px) {
  .site-header {
    padding: 22px;
  }
  .logo {
    font-size: 20px;
  }
  h1 {
    font-size: 44px;
  }
  h1 span {
    display: block;
    margin: 5px 0 0;
  }
  .subtitle {
    font-size: 16px;
    max-width: 380px;
  }
  .hero-section {
    padding: 40px 24px 70px;
  }
}
@media (prefers-reduced-motion: reduce) {
  .motion-toggle {
    display: none;
  }
  .start-button {
    transition: none;
  }
}
</style>
