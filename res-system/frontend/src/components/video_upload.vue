<template>
  <div class="upload-card g-card">
    <!-- 드래그&드롭 영역 -->
    <label
      class="drop-zone"
      @dragover.prevent
      @drop.prevent="handleDrop"
    >
      <input
        type="file"
        accept="video/*"
        class="file-input"
        @change="onFileChange"
      />

      <!-- 기본 메시지 / 썸네일 전환 -->
      <div v-if="!selectedFile" class="placeholder">
        <span class="icon">📂</span>
        <p>여기에 비디오 파일을 끌어놓거나<br />클릭해서 선택하세요</p>
      </div>

      <div v-else class="preview">
        <video
          v-if="videoURL"
          :src="videoURL"
          muted
          preload="metadata"
          class="thumbnail"
        />
        <div class="file-info">
          <strong>{{ selectedFile.name }}</strong>
          <span>{{ (selectedFile.size / 1024 / 1024).toFixed(2) }} MB</span>
        </div>
      </div>
    </label>

    <!-- 업로드 버튼 + 진행률 -->
    <button
      class="upload-btn"
      @click="uploadVideo"
      :disabled="!selectedFile || loading"
    >
      {{ loading ? '업로드 중...' : '업로드' }}
    </button>

  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const selectedFile = ref(null)
const videoURL = ref('')
const loading = ref(false)
const uploadPercent = ref(0)
const router = useRouter()

function onFileChange(e) {
  const file = e.target.files[0]
  setFile(file)
}

function handleDrop(e) {
  const file = e.dataTransfer.files[0]
  setFile(file)
}

function setFile(file) {
  if (!file) return
  selectedFile.value = file
  // 썸네일 URL (브라우저 Blob URL)
  videoURL.value = URL.createObjectURL(file)
  uploadPercent.value = 0
}

async function uploadVideo() {
  if (!selectedFile.value) return

  loading.value = true
  uploadPercent.value = 0

  const formData = new FormData()
  formData.append('file', selectedFile.value)
  formData.append(
    'userid',
    localStorage.getItem('userid1') || sessionStorage.getItem('userid2')
  )

  try {
    const res = await axios.post('/images/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: ({ loaded, total }) => {
        if (total) uploadPercent.value = (loaded / total) * 100
      }
    })

    router.push({
      name: 'VideoresultView',
      query: {
        result: res.data.result,
        skeletonVideo: res.data.skeletonVideo
      }
    })
  } catch (err) {
    console.error(err)
    alert('업로드 중 오류 발생')
  } finally {
    loading.value = false
    uploadPercent.value = 0
  }
}

watch(selectedFile, (newVal) => {
  if (!newVal && videoURL.value) {
    URL.revokeObjectURL(videoURL.value)
    videoURL.value = ''
  }
})
</script>

<style scoped>
:root {
  --sky-color:   #87ceeb;
  --field-color: #3cb043;
  --flag-color:  #ff3b30;
}

/* 카드 전체 */
.upload-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}

/* 드래그&드롭 존 */
.drop-zone {
  width: 100%;
  max-width: 480px;
  height: 260px;
  border: 3px dashed var(--field-color);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(4px);
  display: flex;
  justify-content: center;
  align-items: center;
  text-align: center;
  color: var(--field-color);
  cursor: pointer;
  position: relative;
  transition: background 0.2s, border-color 0.2s;
}
.drop-zone:hover {
  background: rgba(255, 255, 255, 0.85);
  border-color: var(--flag-color);
}

.file-input {
  display: none;
}

.placeholder .icon {
  font-size: 48px;
}

.preview {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

.thumbnail {
  width: 160px;
  height: 90px;
  object-fit: cover;
  border-radius: 8px;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.file-info {
  font-size: 0.9rem;
  color: #333;
}

/* 업로드 버튼 */
.upload-btn {
  padding: 12px 32px;
  border: none;
  border-radius: 10px;
  background: var(--flag-color);
  color: #fff;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}
.upload-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.upload-btn:not(:disabled):hover {
  background: #d93127;
}

/* 진행률 바 */
.progress-wrapper {
  position: relative;
  width: 100%;
  max-width: 480px;
  height: 14px;
  background: #e9ecef;
  border-radius: 7px;
  overflow: hidden;
  margin-top: -10px;
}

.progress-bar {
  height: 100%;
  background: linear-gradient(
    135deg,
    var(--sky-color) 0%,
    var(--field-color) 100%
  );
  transition: width 0.2s ease;
}

.percent {
  position: absolute;
  top: -24px;
  right: 0;
  font-size: 0.85rem;
  color: #333;
}
</style>
