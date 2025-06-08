<template>
  <div>
    <h2>분류 결과: {{ result }}</h2>

    <video
      v-if="skeletonVideoUrl"
      controls
      autoplay
      class="responsive-video"
    >
      <source :src="skeletonVideoUrl" type="video/mp4" />
      브라우저가 비디오를 지원하지 않습니다.
    </video>

    <div v-if="skeletonJsonUrl" class="json-viewer">
      JSON 데이터: <a :href="skeletonJsonUrl" target="_blank">{{ skeletonJsonUrl }}</a>
    </div>

    <button @click="goBack">다시 업로드하러 가기</button> 
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const result = ref('')
const skeletonVideoUrl = ref(null)
const skeletonJsonUrl = ref(null)

onMounted(() => {
  result.value = route.query.result || ''
  const svu = route.query.skeletonVideo || ''  // 업로드된 비디오 URL

  if (svu) { // URL이 존재할 때만 설정
    const sju = svu.replace('.mp4', '.json') // .mp4를 제거하고 .json으로 변경
    skeletonVideoUrl.value = `http://localhost:8000/images/search_video?filename=${encodeURIComponent(svu)}`
    skeletonJsonUrl.value = `http://localhost:8000/images/search_json?filename=${encodeURIComponent(sju)}`
  }
  console.log(skeletonVideoUrl.value)
})

function goBack() {
  router.push({ name: 'main' })  // 메인 페이지로 이동
}
</script>

<style>
.responsive-video {
  max-width: 800px;
  width: 100%;
  max-height: 480px;
  height: auto;
  border-radius: 8px;
  background-color: black;
  display: block;
  margin: 1rem auto;
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
}

.json-viewer {
  margin-top: 1rem;
  font-family: monospace;
  color: #555;
  word-break: break-word;
  text-align: center;
}
</style>
