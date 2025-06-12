<template>
  <div class="main-section">
    <!-- Header -->
    <header-view class="header"/>
    <!-- Body -->
    <div class="body">
      <!-- Sidebar -->
      <left-view class="sidebar" @change-view="updateMainView"/>
      <!-- Dynamic main content -->
      <main class="content-area">
        <component :is="currentComponent" class="content-box"/>
      </main>
    </div>
  </div>
</template>

<script>
import headerView from '@/components/headerView.vue';
import leftView from '@/components/leftView.vue';
import lobbyView from '@/components/lobbyView.vue';
import { defineAsyncComponent } from 'vue';

export default {
  components: {
    headerView,
    leftView,
  },
  data() {
    return {
      currentComponent: lobbyView,
    };
  },
  methods: {
    updateMainView(viewName) {
      const route = this.$router.getRoutes().find(r => r.name === viewName);

      if (!route) {
        console.warn('해당 라우트를 찾을 수 없습니다:', viewName);
        return;
      }

      // 동적 import & lazy loading
      if (route.components?.default && typeof route.components.default === 'function') {
        this.currentComponent = defineAsyncComponent(route.components.default);
      } else {
        console.warn('컴포넌트 정보가 없습니다:', route);
      }
    },
    // URL 쿼리로 직접 접근 시 동기화
    initViewFromQuery() {
      const { view } = this.$route.query;
      if (view) {
        this.updateMainView(view);
      }
    }
  },
  mounted() {
    this.initViewFromQuery();
  },
  watch: {
    '$route.query.view'(newVal) {
      if (newVal) {
        this.updateMainView(newVal);
      }
    }
  }
};
</script>

<style scoped>
.main-section {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  margin: 0;
  background: linear-gradient(to bottom, var(--sky-color) 0% 45%, var(--field-color) 45% 100%);
  color: var(--text-color);
}

/* Header 영역 */
.header {
  flex: 0 0 64px;
}

/* Body(사이드바 + 콘텐츠) */
.body {
  display: flex;
  flex: 1;
}

/* Sidebar */
.sidebar {
  flex: 0 0 240px;
}

/* 중앙 콘텐츠 영역 */
.content-area {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
}

/* 각 콘텐츠 뷰 box 공통 스타일 */
.content-box {
  background: rgba(255,255,255,0.85);
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
  border-radius: 16px;
  padding: 24px;
  min-height: calc(100% - 48px); /* 여백 고려 */
  box-shadow: 0 8px 20px rgba(0,0,0,0.15);
}
</style>
