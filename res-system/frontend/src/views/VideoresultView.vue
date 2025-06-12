<template>
  <div class="result-root">
    <!-- 상단 블록(하늘 배경) -->
    <section class="top-block">
      <div class="top-left">
        <h2 class="result-heading">
          분류 결과: {{ result }}
          <img
            v-if="resultImage"
            :src="resultImage"
            class="badge-img"
            alt="result badge"
          />
        </h2>

        <!-- 중앙-정렬 둥근 버튼 -->
        <button
          class="u-btn u-btn-flag round-btn"
          @click="goBack"
        >
          다시 업로드하러 가기
        </button>
      </div>

      <!-- 비디오도 카드 중앙에 -->
      <video
        v-if="skeletonVideoUrl"
        ref="videoRef"
        controls
        class="result-video"
        @timeupdate="onTimeUpdate"
      >
        <source :src="skeletonVideoUrl" type="video/mp4" />
        브라우저가 비디오를 지원하지 않습니다.
      </video>
    </section>

    <!-- Landmark 분석 -->
    <LandmarkView
      v-if="jointData.length"
      :jointData="jointData"
      :currentJointData="currentJointData"
      v-model:selectedJoint="selectedJoint"
      :koreanJointNameMap="koreanJointNameMap"
      :comStabilityScores="comStabilityScores"
      class="u-card landmark-block"
    />

    <!-- Comments -->
    <CommentsView
      :currentJointData="currentJointData"
      :analysis_id="analysis_id"
      class="u-card comments-block"
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
import goodImg from '@/assets/최고.png'
import badImg from '@/assets/당황_놀람.png'

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

const resultImage = computed(() =>
  result.value === 'Good' ? goodImg : result.value === 'Bad' ? badImg : ''
)

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
watch(() => currentFrameIndex.value, n => {
  if (!jointData.value.length) return
  currentJointData.value = jointData.value.find(d => d.frame === n) || jointData.value[0]
})

const svu = ref('')
const analysis_id = computed(() => `${store.state.store_userid1}_${svu.value}`)

onMounted(async() => {
  result.value = route.query.result || ''
  svu.value = route.query.skeletonVideo || ''

  if (svu.value) {
    skeletonVideoUrl.value = `/images/search_video?filename=${encodeURIComponent(svu.value)}`
    const jsonUrl = `/images/search_json?filename=${encodeURIComponent(svu.value.replace('.mp4','.json'))}`
    try {
      const { data } = await axios.get(jsonUrl)
      if (data.fps) {
        VIDEO_FPS.value = data.fps
        const stabilityMap = new Map((data.com_stability_scores||[]).map(d=>[d.frame,d.score]))
        jointData.value = (data.angles||[]).map(f=>({ ...f, com_stability_score: stabilityMap.get(f.frame) ?? null }))
        comStabilityScores.value = data.com_stability_scores || []
      }
      currentJointData.value = jointData.value[0] || null
    } catch (e) { console.error(e) }
  }
})

function onTimeUpdate() {
  const t = videoRef.value?.currentTime || 0
  currentFrameIndex.value = Math.floor(t * VIDEO_FPS.value)
}
function goBack() {
  router.push({ name: 'main', query:{ view:'menu3' }})
}
</script>

<style scoped>
.result-root {
  min-height: 100vh;
  padding: 24px 16px 48px;
  display: flex;
  flex-direction: column;
  gap: 24px;
  background: linear-gradient(
    to bottom,
    var(--sky-color) 0% 45%,
    var(--field-color) 45% 100%
  );
}

/* 상단 블록: 세로 + 중앙 정렬 */
.top-block {
  display: flex;
  flex-direction: column;   /* ✅ 세로 스택 */
  align-items: center;      /* ✅ 가로 중앙 */
  gap: 24px;
  padding: 24px;
  background: var(--sky-color);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
}

.top-left {
  display: flex;
  flex-direction: column;
  align-items: center;      /* ✅ 텍스트·버튼 중앙 */
  gap: 12px;
}

.result-heading {
  margin: 0;
  font-size: 24px;
  font-weight: 700;
  color: #000;
  display: flex;
  align-items: center;
  gap: 8px;
  background-color: #fff;
  border-radius: 10px;
  padding: 12px 28px;
}

.badge-img {
  width: 100px;
  height: auto;
}

/* 둥근 버튼 공통(로그인·메인 동일) */
.round-btn {
  border-radius: 10px;
  padding: 12px 28px;
  font-size: 16px;
  box-shadow: var(--shadow-md);
}
.round-btn:hover { filter: brightness(0.95); }

/* 비디오 */
.result-video {
  max-width: 640px;
  width: 100%;
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);
  margin: 0 auto;          /* ✅ 남는 공간일 때도 가운데 */
}

/* 아래 카드들 */
.landmark-block,
.comments-block {
  box-shadow: var(--shadow-md);
}
</style>