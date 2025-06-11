<!-- 사이드메뉴 컴포넌트 (SideMenu.vue) -->
<template><div class="g-section" style="background-color: gainsboro; padding: 20px; height: 100%;">
    <button v-if="userId === 'admin'" @click="selectMenu('menu1')">id 관리</button>
    <button @click="selectMenu('menu2')">업로드&분석</button>
    <button @click="selectMenu('menu3')">업로드 기록</button>
    <button @click="selectMenu('menu4')">유저 정보</button>
  </div>
</template>

<script setup>
import { computed ,defineEmits} from 'vue';
import { useStore } from 'vuex'

const store = useStore()
const userId = computed(() => store.state.store_userid1)

const emit = defineEmits(['change-view']);

function selectMenu(menuName) {
  emit('change-view', menuName);
}
</script>



<style scoped>
button {
  display: block;
  width: 100%;
  margin-top: 15px;
  padding: 5px 10px;
  font-size: 18px;
  font-weight: bold;
  cursor: pointer;
  border: none;
  border-radius: 8px;
  background-color: #ffffff;
  transition: background-color 0.3s;
}
button:hover {
  background-color: #e6ffe6;
}
</style>
