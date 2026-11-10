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
      <HomeOceanBackdrop />
      <header class="site-header">
        <UserInfoComponent :show-button="true" />
      </header>
      <main class="hero-section">
        <div class="hero-content">
          <h1 :aria-label="BRAND.name"><span>链证</span><span class="brand-blue">出海</span></h1>
          <p class="hero-tagline">让出海资料预审更智能</p>
          <p class="hero-description">出海资料预审智能体<br />让每个待办都有依据</p>
          <button class="start-button lucide-icon-btn" @click="goToChat">
            <span>开始体验</span><ArrowRight :size="20" />
          </button>
        </div>
      </main>
      <footer class="features" aria-label="预审工作方式">
        <section><h2>辅助预审</h2><p>核对差异与缺项</p></section>
        <section><h2>证据支撑</h2><p>保留出处与未知</p></section>
        <section><h2>人工确认</h2><p>补件后继续复核</p></section>
      </footer>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
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
  } catch (e) {
    console.error('加载失败:', e)
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

</script>

<style lang="less" scoped>
.home-container {
  position: relative;
  isolation: isolate;
  min-height: max(800px, 100svh);
  background: var(--main-50);
  color: var(--gray-1000);
  overflow: hidden;
}
.site-header {
  position: absolute;
  top: 0;
  right: 0;
  z-index: 2;
  padding: 28px 40px;
}
.site-header :deep(.ant-btn-primary) {
  background: transparent;
  color: var(--gray-1000);
  border-color: var(--main-800);
  border-radius: 16px;
  box-shadow: none;
  padding-inline: 24px;
  height: 40px;
}
.hero-section {
  position: relative;
  z-index: 1;
  padding: max(130px, 17vh) 6vw 270px;
}
.hero-content { max-width: 900px; }
h1 {
  margin: 0 0 16px;
  font-size: clamp(64px, 7.2vw, 116px);
  line-height: 1.08;
  letter-spacing: -4px;
  font-weight: 750;
}
.brand-blue { color: var(--main-600); }
h1 span { font-weight: inherit; }
.hero-tagline {
  margin: 0 0 22px;
  font-size: clamp(25px, 2.8vw, 44px);
  line-height: 1.35;
  font-weight: 650;
  letter-spacing: -1px;
}
.hero-description {
  margin: 0;
  font-size: clamp(18px, 1.7vw, 26px);
  line-height: 1.65;
  color: var(--gray-700);
}
.start-button {
  margin-top: 24px;
  padding: 14px 32px;
  border: 1px solid var(--main-color);
  border-radius: 28px;
  background: var(--main-color);
  color: var(--brand-on-primary);
  gap: 12px;
  font-size: 18px;
  font-weight: 550;
  box-shadow: 0 8px 24px var(--shadow-2);
  cursor: pointer;
  transition: background 0.18s ease, box-shadow 0.18s ease;
}
.start-button:hover { background: var(--main-700); box-shadow: 0 10px 28px var(--shadow-3); }
.start-button:focus-visible { outline: 3px solid var(--main-200); outline-offset: 4px; }
.features {
  position: absolute;
  z-index: 1;
  left: 6vw;
  bottom: 36px;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 44px;
  width: min(900px, 74%);
  color: var(--brand-on-primary);
  text-shadow: 0 1px 8px var(--main-900);
}
.features h2 { margin: 0 0 8px; font-size: clamp(20px, 2.4vw, 36px); font-weight: 650; }
.features p { margin: 0; font-size: clamp(14px, 1.6vw, 23px); line-height: 1.5; }
:global(.dark .home-container .features) {
  color: var(--gray-1000);
  text-shadow: 0 1px 8px var(--gray-0);
}
.loading-container, .error-container {
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
  .home-container { min-height: max(820px, 100svh); }
  .site-header { padding: 22px; }
  .hero-section { padding: 130px 24px 300px; }
  h1 { font-size: clamp(60px, 13vw, 88px); letter-spacing: -3px; }
  .hero-tagline { font-size: clamp(23px, 4.8vw, 32px); letter-spacing: -0.5px; }
  .hero-description { font-size: 18px; }
  .start-button { font-size: 16px; }
  .features { left: 24px; right: 24px; width: auto; bottom: 32px; gap: 14px; }
  .features h2 { font-size: clamp(17px, 4.3vw, 24px); }
  .features p { font-size: clamp(12px, 3vw, 16px); }
}
@media (prefers-reduced-motion: reduce) {
  .start-button { transition: none; }
}
</style>
