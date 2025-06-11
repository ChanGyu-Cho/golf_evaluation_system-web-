<template><div class="g-card">
    <input type="file" @change="onFileChange" accept="video/*" />
    <button @click="uploadVideo" :disabled="!selectedFile || loading">업로드</button>
    <div v-if="loading">처리중...</div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const selectedFile = ref(null)
const loading = ref(false)
const router = useRouter()

function onFileChange(event) {
  selectedFile.value = event.target.files[0]
}

async function uploadVideo() {
  if (!selectedFile.value) return

  loading.value = true  // 업로드 시작 시 로딩 상태 설정

  const formData = new FormData()
  formData.append('file', selectedFile.value)
  formData.append('userid', localStorage.getItem('userid1') || sessionStorage.getItem('userid2'))

  try {
    const response = await axios.post('/images/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    console.log('업로드 성공:', response.data)

    // 성공 시 받은 결과를 쿼리 파라미터 또는 state로 전달하여 결과 페이지 이동
    router.push({
      name: 'VideoresultView',
      query: {
        result: response.data.result,
        skeletonVideo: response.data.skeletonVideo
      },
    })
  } catch (error) {
    alert('업로드 중 오류 발생')
  } finally {
    loading.value = false
  }
}
</script>
