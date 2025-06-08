<template>
  <div class="video-container">
    <h2>비디오 재생</h2>
    <video
      v-if="videoSrc"
      controls
      autoplay
      class="video-player"
    >
      <source :src="videoSrc" type="video/mp4" />
      브라우저가 비디오를 지원하지 않습니다.
    </video>
    <div v-else>비디오를 불러오는 중...</div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const videoSrc = ref(null)

onMounted(() => {
  const filename = route.query.filename
  if (filename) {
    videoSrc.value = `http://localhost:8000/images/search_video?filename=${encodeURIComponent(filename)}`
  }
})
</script>

<style>
.video-container {
  padding: 2rem;
  text-align: center;
}

/* 최대 크기 지정 */
.video-player {
  max-width: 800px;    /* 최대 가로 크기 */
  max-height: 450px;   /* 최대 세로 크기 */
  width: 100%;         /* 부모 컨테이너 너비 내에서 최대한 늘림 */
  height: auto;        /* 높이는 자동 비율 유지 */
  border: 1px solid #ccc;
  border-radius: 8px;
  background-color: black;
}

.video-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  background: #f9f9f9;
  min-height: 100vh;
  box-sizing: border-box;
}

.video-container h2 {
  font-size: 1.8rem;
  color: #333;
  margin-bottom: 1.5rem;
  font-weight: 600;
}

.video-player {
  max-width: 100%;
  width: 100%;
  max-height: 480px;
  border: none;
  border-radius: 12px;
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
  background-color: #000;
  transition: all 0.3s ease;
}

.video-player:hover {
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25);
}

div[role="alert"] {
  font-size: 1rem;
  color: #888;
  margin-top: 2rem;
}
</style>
