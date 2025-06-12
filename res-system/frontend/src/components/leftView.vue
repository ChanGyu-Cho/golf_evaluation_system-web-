<!-- Sidebar / LeftView -->
<template>
  <nav class="sidebar-wrapper">
    <h2 class="logo">🏌️‍♂️ SwingMate</h2>

    <button
      class="nav-btn"
      v-if="userId === 'admin'"
      :class="{ active: activeMenu === 'menu1' }"
      @click="selectMenu('menu1')"
    >
      ID 관리
    </button>

    <button
      class="nav-btn"
      :class="{ active: activeMenu === 'menu2' }"
      @click="selectMenu('menu2')"
    >
      업로드 & 분석
    </button>

    <button
      class="nav-btn"
      :class="{ active: activeMenu === 'menu3' }"
      @click="selectMenu('menu3')"
    >
      업로드 기록
    </button>

    <button
      class="nav-btn"
      :class="{ active: activeMenu === 'menu4' }"
      @click="selectMenu('menu4')"
    >
      유저 정보
    </button>
  </nav>
</template>

<script setup>
import { computed, ref, defineEmits } from 'vue';
import { useStore } from 'vuex';

const store = useStore();
const userId = computed(() => store.state.store_userid1);
const emit = defineEmits(['change-view']);

const activeMenu = ref('menu0');

function selectMenu(menuName) {
  activeMenu.value = menuName;
  emit('change-view', menuName);
}
</script>

<style scoped>
:root {
  --sky-color: #87ceeb;
  --field-color: #3cb043;
  --flag-color: #ff3b30;
}

.sidebar-wrapper {
  height: 100%;
  padding: 32px 16px;
  box-sizing: border-box;
  background: var(--field-color);
  display: flex;
  flex-direction: column;
  gap: 16px;
  color: #ffffff;
}

.logo {
  font-size: 22px;
  font-weight: bold;
  margin-bottom: 32px;
  text-align: center;
}

.nav-btn {
  width: 100%;
  padding: 12px 14px;
  border: none;
  border-radius: 10px;
  background: #ffffff;
  color: var(--field-color);
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s, color 0.2s;
}

.nav-btn:hover {
  background: var(--flag-color);
  color: #ffffff;
}

.nav-btn.active {
  background: var(--flag-color);
  color: #ffffff;
}
</style>
