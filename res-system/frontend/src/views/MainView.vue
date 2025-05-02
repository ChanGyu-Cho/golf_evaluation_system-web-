<template>
  <div style="display: flex; flex-direction: column; height: 100vh;">
    <div style="height: 20%;">
      <header-view />
    </div>
    <div style="display: flex; flex-grow: 1;">
      <div style="width: 20%;">
        <left-view @change-view="updateMainView" />
      </div>
      <div style="flex-grow: 1; background-color: white; height: 100%;"> <!-- ✅ height 추가 -->
        <component :is="currentComponent" />
      </div>

    </div>
  </div>
</template>



<script>
import headerView from '@/components/headerView.vue';
import leftView from '@/components/leftView.vue';
import uniqView from '@/components/uniqView.vue';
import { defineAsyncComponent } from 'vue';

export default {
  components: {
    headerView,
    leftView,
  },
  data() {
    return {
      currentComponent: uniqView,
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
      // ✅ 여기로 진입해야 함
      this.currentComponent = defineAsyncComponent(route.components.default);
    } else {
      console.warn('컴포넌트 정보가 없습니다:', route);
    }
  }
}
};
</script>