<template>
  <div style="background-color: gainsboro; padding: 20px; text-align: center; display: flex; justify-content: space-between; align-items: center;">
    <h1>안녕하세요 {{store_local_name}}님!(id={{store.state.store_userid1}})</h1>
    <!-- 로그아웃 버튼을 오른쪽에 배치 -->
    <button @click="Logout">로그아웃</button>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router';
import { computed } from 'vue'
import { useStore } from 'vuex'
const store = useStore()
const router = useRouter(); // vue-router에서 useRouter를 import합니다.

// store.state에서 값을 computed로 가져옵니다.
const store_local_name = computed(() => store.state.store_local_name)

const Logout = () => {
  // 로그아웃 처리 로직 (예: API 호출)
  try{
    alert("로그아웃 되었습니다.")
    localStorage.removeItem('store_local_name'); // 로컬 스토리지에서 이름 삭제
    sessionStorage.removeItem('store_session_name'); // 세션 스토리지에서 이름 삭제
    store.commit('setLocalName', null); // Vuex 스토어에서 이름 삭제
  }catch(e){
    console.log("로그아웃 실패", e)
  }

  // 로그아웃 후 메인 페이지로 이동
  router.push({ path: '/' });
};
</script>


<style scoped>
button {
  padding: 8px 15px;
  border: none;
  border-radius: 5px;
  background-color: #f44336;
  color: white;
  cursor: pointer;
  font-size: 1rem;
}

/* 버튼에 마우스 오버 시 색상 변경 */
button:hover {
  background-color: #d32f2f;
}

/* 헤더 내에서 로그아웃 버튼을 오른쪽으로 배치 */
div {
  display: flex;
  justify-content: space-between;
  align-items: center;
  text-align: center;
}

button {
  margin-left: auto; /* 로그아웃 버튼을 오른쪽 끝으로 이동 */
}
</style>
