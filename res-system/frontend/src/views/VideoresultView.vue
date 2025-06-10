<!-- src/views/VideoresultView.vue -->
<template>
  <div class="result-page-container">
    <button @click="goBack">다시 업로드하러 가기</button>
    <h2>분류 결과: {{ result }}</h2>

    <!-- 비디오 재생은 부모에서 그대로 -->
    <video
      v-if="skeletonVideoUrl"
      ref="videoRef"
      controls
      class="responsive-video"
      @timeupdate="onTimeUpdate"
    >
      <source :src="skeletonVideoUrl" type="video/mp4" />
      브라우저가 비디오를 지원하지 않습니다.
    </video>

    <!-- LandmarkView 컴포넌트: jointData, currentJointData, selectedJoint, koreanJointNameMap 전달-->
    <LandmarkView
      v-if="jointData.length"
      :jointData="jointData"
      :currentJointData="currentJointData"
      v-model:selectedJoint="selectedJoint"
      :koreanJointNameMap="koreanJointNameMap"
    />

    <!-- CommentsView 컴포넌트: currentJointData, analysisId 전달 -->
    <CommentsView
      :currentJointData="currentJointData"
      :analysisId="analysisId"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import LandmarkView from '@/components/LandmarkView.vue'
import CommentsView from '@/components/CommentsView.vue'
import { useStore } from 'vuex'
const store = useStore()

const route = useRoute()
const router = useRouter()

const result = ref('')
const skeletonVideoUrl = ref(null)
const videoRef = ref(null)
const svu = ref('')

const jointData = ref([])  // 관절 각도+com_x,y,z 배열
const currentJointData = ref(null)

// 선택한 관절명
const selectedJoint = ref('')

// FPS reactive
const VIDEO_FPS = ref(30)

// 영어 관절명 → 한글 매핑
const koreanJointNameMap = {
  left_elbow_flexion: '왼쪽 팔꿈치 각도',
  right_elbow_flexion: '오른쪽 팔꿈치 각도',
  left_knee_flexion: '왼쪽 무릎 각도',
  right_knee_flexion: '오른쪽 무릎 각도',
  left_hip_flexion: '왼쪽 엉덩이 각도',
  right_hip_flexion: '오른쪽 엉덩이 각도',
  left_shoulder_flexion: '왼쪽 어깨 각도',
  right_shoulder_flexion: '오른쪽 어깨 각도',
  pelvis_list: '골반 상승',
  pelvis_rotation: '골반 회전',
  com_x: '무게중심 X',
  com_y: '무게중심 Y',
  com_z: '무게중심 Z',
}

// currentFrameIndex 관리
const currentFrameIndex = ref(0)
watch(
  () => currentFrameIndex.value,
  (newFrame) => {
    if (!jointData.value.length) return
    const found = jointData.value.find(d => d.frame === newFrame)
    currentJointData.value = found || jointData.value[0]
  },
  { immediate: true }
)

// analysisId: userId + video 식별자
const analysisId = computed(() => `${store.state.store_userid1}_${svu.value}`)

// JSON 불러오기 및 jointData 처리
onMounted(async () => {
  result.value = route.query.result || ''
  svu.value = route.query.skeletonVideo || ''

  if (svu.value) {
    skeletonVideoUrl.value = `/images/search_video?filename=${encodeURIComponent(svu.value)}`

    const jsonFilename = svu.value.replace('.mp4', '.json')
    const jsonUrl = `/images/search_json?filename=${encodeURIComponent(jsonFilename)}`

    try {
      const res = await axios.get(jsonUrl)
      const jsonData = res.data

      if (jsonData.fps) {
        VIDEO_FPS.value = jsonData.fps

        // angles 배열 각 요소마다 com.x,y,z 를 분리해서 같은 객체 최상위 필드로 옮기기
        const processedAngles = (jsonData.angles || []).map(frame => {
          const { com, ...rest } = frame
          return {
            ...rest,
            com_x: com ? com.x : null,
            com_y: com ? com.y : null,
            com_z: com ? com.z : null,
          }
        })

        jointData.value = processedAngles
      } else {
        jointData.value = jsonData
      }

      currentFrameIndex.value = 0
      currentJointData.value = jointData.value[0] || null

    } catch (e) {
      console.error('JSON 불러오기 실패:', e)
    }
  }
})

// 비디오 시간 변화에 따른 currentFrameIndex 업데이트
function onTimeUpdate() {
  const currentTime = videoRef.value?.currentTime || 0
  const currentFrame = Math.floor(currentTime * VIDEO_FPS.value)
  currentFrameIndex.value = currentFrame
}

// 뒤로가기
function goBack() {
  router.push({ name: 'main', query: { view: 'menu3' } })
}
</script>

<style scoped>
.result-page-container {
  min-height: 100vh;
  padding: 2rem 1rem;
  overflow-y: auto;
  background-color: #fff;
}
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
</style>
