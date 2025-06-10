<template>
  <div style="display: flex; flex-direction: column; height: 100vh; margin: 0;">
    <!-- Header 영역 -->
    <div style="flex: 0 0 15%; padding: 0; margin: 0;">
      <header-view />
    </div>

    <!-- 나머지 화면 영역 -->
    <div style="display: flex; flex: 1 1 auto; padding: 0; margin: 0;">
      <!-- LeftView -->
      <div style="flex: 0 0 20%; padding: 0; margin: 0;">
        <left-view @change-view="updateMainView" />
      </div>

      <!-- 메인 컴포넌트 영역 -->
      <div style="flex: 1; background-color: white; padding: 0; margin: 0;">
        <component :is="currentComponent" />
      </div>
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

      if (route.components?.default && typeof route.components.default === 'function') {
        this.currentComponent = defineAsyncComponent(route.components.default);
      } else {
        console.warn('컴포넌트 정보가 없습니다:', route);
      }
    },
    initViewFromQuery() { // URL 쿼리에서 view 파라미터를 읽어와서 초기 컴포넌트 설정
      const viewName = this.$route.query.view;
      if (viewName) {
        this.updateMainView(viewName);
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