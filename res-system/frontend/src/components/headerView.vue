<template>
  <header class="header-bar">
    <div class="left">
      <span class="app-title">⛳ SwingMate</span>
    </div>
    <div class="right">
      <span class="welcome">안녕하세요 {{ store_local_name }}님! (id={{ store.state.store_userid1 }})</span>
      <button class="logout-btn" @click="Logout">로그아웃</button>
    </div>
  </header>
</template>

<script setup>
import { useRouter } from 'vue-router';
import { computed } from 'vue';
import { useStore } from 'vuex';

const store = useStore();
const store_local_name = computed(() => store.state.store_local_name);
const router = useRouter();

const Logout = () => {
  try {
    alert('로그아웃 되었습니다.');
    localStorage.removeItem('store_local_name');
    // 필요시 추가 상태 초기화
    router.push({ path: '/' });
  } catch (err) {
    console.error(err);
  }
};
</script>

<style scoped>
:root {
  --sky-color: #87ceeb;
  --flag-color: #ff3b30;
}

.header-bar {
  height: 64px;
  width: 100%;
  background: var(--sky-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
  box-sizing: border-box;
  box-shadow: 0 2px 6px rgba(0,0,0,0.15);
  color: #ffffff;
}

.app-title {
  font-size: 24px;
  font-weight: 700;
}

.welcome {
  margin-right: 16px;
  font-weight: 500;
}

.logout-btn {
  padding: 8px 16px;
  background: #ffffff;
  color: var(--flag-color);
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  transition: background 0.2s, color 0.2s;
}

.logout-btn:hover {
  background: var(--flag-color);
  color: #ffffff;
}
</style>
