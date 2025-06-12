<template>
  <div class="result-page-container g-section">
    <button @click="goBack">다시 업로드하러 가기</button>

    <!-- ✅ 결과 + 배지 이미지 -->
    <h2 class="result-title">
      분류 결과: {{ result }}
      <img
        v-if="resultImage"
        :src="resultImage"
        class="result-badge"
        alt="분류 결과 배지"
      />
    </h2>

    <div style="position: relative; display: inline-block;">
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
    </div>

    <LandmarkView
      v-if="jointData.length"
      :jointData="jointData"
      :currentJointData="currentJointData"
      v-model:selectedJoint="selectedJoint"
      :koreanJointNameMap="koreanJointNameMap"
      :comStabilityScores="comStabilityScores"
    />

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

/* ✅ 결과 배지 이미지 */
import goodImg from '@/assets/최고.png'
import badImg  from '@/assets/당황_놀람.png'

const store = useStore()
const route = useRoute()
const router = useRouter()

const result = ref('')
const skeletonVideoUrl = ref(null)
const videoRef = ref(null)

const jointData = ref([])
const currentJointData = ref(null)
const comStabilityScores = ref([])

const selectedJoint = ref('')
const VIDEO_FPS = ref(30)



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
  com_stability_score: 'COM 안정성 지표',
}

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

const svu = ref('')
const analysisId = computed(() => `${store.state.store_userid1}_${svu.value}`)

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

        const processedAngles = (jsonData.angles || []).map(frame => ({ ...frame }))

        const stabilityScoreMap = new Map(
          (jsonData.com_stability_scores || []).map(d => [d.frame, d.score])
        )
        processedAngles.forEach(d => {
          d.com_stability_score = stabilityScoreMap.get(d.frame) ?? null
        })

        jointData.value = processedAngles
        comStabilityScores.value = jsonData.com_stability_scores || []
      }

      currentFrameIndex.value = 0
      currentJointData.value = jointData.value[0] || null
    } catch (e) {
      console.error('JSON 불러오기 실패:', e)
    }
  }
})

/* ✅ 결과에 따른 이미지 선택 */
const resultImage = computed(() =>
  result.value === 'Good'
    ? goodImg
    : result.value === 'Bad'
    ? badImg
    : ''
)

function onTimeUpdate() {
  const currentTime = videoRef.value?.currentTime || 0
  currentFrameIndex.value = Math.floor(currentTime * VIDEO_FPS.value)
}

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

/* ✅ 결과 제목 + 이미지 배치 */
.result-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 0;          /* 필요 시 조정 */
}

.result-badge {
  width: 48px;            /* 필요 시 크기 조정 */
  height: auto;
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
