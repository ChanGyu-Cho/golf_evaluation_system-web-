<template><div class="lobby" >
    <h3>SwingMate에 오신걸 환영합니다!</h3>
    <p>업로드&분석을 눌러 골프 스윙 영상을 업로드해 주세요!</p>
    <img alt="img" src="../assets/백경이(hi).png" style="width: 150px;" />
    </div>
</template>

<script>
export default {
  // 컴포넌트 로직
};
</script>

<style scoped>
.lobby {
  background-color: rgba(255, 255, 255, 0.8); /* 흰색 배경 */
  backdrop-filter: blur(8px); /* 블러 효과 */
}

.uniq-container {
  height: 100%; /* ✅ 필수 */
}

</style>