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
    <!-- Keep the component mounted (v-show) so it can receive data updates without remounting.
         Use a key tied to the upload id (svu) to force a full re-render when a new upload is loaded. -->
    <LandmarkView
      v-show="jointData.length > 0"
      :key="svu || 'landmark'"
      :jointData="jointData"
      :currentJointData="currentJointData"
      v-model="selectedJoint"
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
const errorMessage = ref('')
const videoRef = ref(null)
const jointData = ref([])
const currentJointData = ref(null)
const comStabilityScores = ref([])
const selectedJoint = ref('')
const VIDEO_FPS = ref(30)

// Normalize various incoming skeleton filename forms to the canonical
// `<base>_openpose_skeleton_h264.mp4` used by the server.
const normalizeSkeletonFilename = (raw) => {
  if (!raw) return ''
  // grab base filename only
  let name = String(raw).split(/[\\/]/).pop()
  // remove leading marker if present (e.g. skeleton_...)
  name = name.replace(/^skeleton_/, '')
  // strip existing openpose suffix and extension
  name = name.replace(/_openpose_skeleton_h264\.mp4$/i, '')
  name = name.replace(/\.mp4$/i, '')
  // final canonical name
  return `${name}_openpose_skeleton_h264.mp4`
}

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
  com_x: 'COM X',
  com_y: 'COM Y',
  com_z: 'COM Z',
}

const currentFrameIndex = ref(0)
watch(() => currentFrameIndex.value, n => {
  if (!jointData.value.length) return
  currentJointData.value = jointData.value.find(d => d.frame === n) || jointData.value[0]
})

const svu = ref('')
const analysis_id = computed(() => `${store.state.store_userid1}_${svu.value}`)

onMounted(async () => {
  // 1. result json 파일명 결정 (route.query.result 또는 서버에서 전달)
  let resultJsonFile = route.query.result || ''
  console.debug('[Debug] VideoresultView route.query.result =', route.query.result)
  if (!resultJsonFile.endsWith('.json')) {
    resultJsonFile = resultJsonFile + '.json'
  }
  resultJsonFile = resultJsonFile.split(/[\\/]/).pop();
  const resultJsonUrl = `/images/search_json?filename=${encodeURIComponent(resultJsonFile)}`

  // If the upload step passed a skeletonVideo filename in the query, use it as a fallback immediately
  const skeletonFromQuery = route.query.skeletonVideo || ''
  if (skeletonFromQuery) {
  const raw = String(skeletonFromQuery).split(/[\\/]/).pop();
  const skeletonFile = normalizeSkeletonFilename(raw)
  if (skeletonFile) skeletonVideoUrl.value = `/images/search_video?filename=${encodeURIComponent(skeletonFile)}`
  }
  // --- Ensure `svu` (video base id) is set so analysis_id is unique per upload.
  // Prefer base extracted from result filename (result_<base>), fall back to skeleton query (skeleton_<base>)
  try {
    if (resultJsonFile) {
      const base = resultJsonFile.replace(/\.json$/i, '').replace(/^result_/, '')
      if (base) svu.value = base
    }
    if (!svu.value && skeletonFromQuery) {
      const raw2 = String(skeletonFromQuery).split(/[\\/]/).pop()
      // remove leading 'skeleton_' and openpose suffixes/extensions
      let maybe = raw2.replace(/^skeleton_/, '').replace(/_openpose_skeleton_h264\.mp4$/i, '').replace(/\.mp4$/i, '')
      if (maybe) svu.value = maybe
    }
  } catch (_) { /* non-fatal: leave svu empty if parsing fails */ }

  try {
    // Only attempt to fetch result JSON if a filename was provided
    if (!resultJsonFile) throw new Error('결과 파일명이 전달되지 않았습니다.')
    // Polling: try to fetch result JSON with retries (max 20 attempts, 3s interval)
    let attempts = 0
    let resultData = null
    while (attempts < 20) {
      try {
        const resp = await axios.get(resultJsonUrl)
        resultData = resp.data
        break
      } catch (err) {
        attempts++
        await new Promise(r => setTimeout(r, 3000))
      }
    }
    if (!resultData) throw new Error('분석 결과를 찾을 수 없습니다(타임아웃).')
    // Set classification label so template displays Good/Bad
    if (resultData) {
      if (resultData.classifyResult) {
        result.value = resultData.classifyResult
      } else if (resultData.mlp_result && resultData.mlp_result.pred !== undefined) {
        const p = resultData.mlp_result.pred
        result.value = p === 1 ? 'Good' : p === 0 ? 'Bad' : 'unknown'
      }
    }
    // 2. skeleton video 파일명 추출 (result json에서)
    let skeletonVideoPath = resultData.openpose_skeleton_video_h264 || ''
    let skeletonVideoFile = skeletonVideoPath ? skeletonVideoPath.split(/[\\/]/).pop() : ''
    if (skeletonVideoFile) {
      // normalize to canonical openpose filename (handles legacy 'skeleton_...' or other forms)
      const normalized = normalizeSkeletonFilename(skeletonVideoFile)
      skeletonVideoUrl.value = `/images/search_video?filename=${encodeURIComponent(normalized)}`
    } else if (!skeletonVideoUrl.value) {
      // no skeleton in result and no fallback from query
      errorMessage.value = '스켈레톤 비디오를 찾을 수 없습니다.'
    }

    // 3. 분석 json 파일명 추출 (result json에서)
    // 예시: angle_json, crop_csv 등 필요한 경우 추가
    // 아래는 예시로 angle_json 사용 (실제 데이터에 맞게 조정)
    // let analysisJsonPath = resultData.angle_json || ''
    // let analysisJsonFile = analysisJsonPath.split(/[\\/]/).pop();
    // const analysisJsonUrl = analysisJsonFile ? `/images/search_json?filename=${encodeURIComponent(analysisJsonFile)}` : ''

    // 4. jointData 등 분석 결과 로딩 (기존과 동일)
    if (resultData.status && resultData.status === 'error') {
      errorMessage.value = '서버에서 분석 중 오류가 발생했습니다.'
      console.error('Analysis error JSON:', resultData)
      // show detailed traceback when available
      if (resultData.traceback) {
        // attach to errorMessage for UI
        errorMessage.value += '\n\n[TRACEBACK]\n' + resultData.traceback.slice(0, 2000)
      }
    }
    // Robust angle/COM loading: support inline angles or external angle_json file.
    const normalizeAndSetAngles = (src) => {
      if (!src) return false
      const fpsVal = src.fps || src.FPS || src.video_fps || null
      if (fpsVal) VIDEO_FPS.value = fpsVal

      const comScores = Array.isArray(src.com_stability_scores)
        ? src.com_stability_scores
        : Array.isArray(src.comScores)
        ? src.comScores
        : []

      comStabilityScores.value = comScores || []

      const stabilityMap = new Map(
        (comStabilityScores.value || []).map(d => [Number(d.frame), d.score])
      )

      const rawAngles = Array.isArray(src.angles)
        ? src.angles
        : Array.isArray(src.angle)
        ? src.angle
        : []

      const normalized = rawAngles.map((f, idx) => {
        const frameNum = Number(f.frame ?? f.idx ?? f.index ?? NaN)
        // if frame is missing or invalid, fall back to array index
        const frameVal = Number.isFinite(frameNum) ? frameNum : idx
        // copy known joint keys and coerce numeric values where possible
        const out = { frame: frameVal }
        for (const k of Object.keys(f)) {
          if (k === 'frame' || k === 'idx' || k === 'index') continue
          const v = f[k]
          // flatten nested COM object into com_x/com_y/com_z so charts can render numeric values
          if (k === 'com' && v && typeof v === 'object') {
            out.com_x = typeof v.x === 'number' ? v.x : v.x === null || v.x === undefined ? null : isNaN(Number(v.x)) ? v.x : Number(v.x)
            out.com_y = typeof v.y === 'number' ? v.y : v.y === null || v.y === undefined ? null : isNaN(Number(v.y)) ? v.y : Number(v.y)
            out.com_z = typeof v.z === 'number' ? v.z : v.z === null || v.z === undefined ? null : isNaN(Number(v.z)) ? v.z : Number(v.z)
            continue
          }
          out[k] = typeof v === 'number' ? v : v === null || v === undefined ? null : isNaN(Number(v)) ? v : Number(v)
        }
        out.com_stability_score = stabilityMap.get(out.frame) ?? null
        return out
      })

      jointData.value = normalized || []
      return true
    }

    // 1) try inline data first
    let loaded = false

    if (resultData && (Array.isArray(resultData.angles) || resultData.fps)) {
      loaded = normalizeAndSetAngles(resultData)
    }

    // 2) else try external angle json indicated by resultData.angle_json
    if (!loaded && resultData && resultData.angle_json) {
      try {
        const angleFile = String(resultData.angle_json).split(/[\\/]/).pop()
        if (angleFile) {
          const angleUrl = `/images/search_json?filename=${encodeURIComponent(angleFile)}`
          const aresp = await axios.get(angleUrl)
          const aj = aresp.data
          if (aj) {
            loaded = normalizeAndSetAngles(aj)
            // stash inline for future use if normalized succeeded
            if (loaded) {
              resultData.angles = aj.angles || aj.angle || []
              resultData.fps = aj.fps || resultData.fps
              resultData.com_stability_scores = aj.com_stability_scores || resultData.com_stability_scores
            }
          }
        }
      } catch (err) {
        console.warn('Failed to load angle_json:', err)
      }
    }
    currentJointData.value = jointData.value[0] || null
  } catch (e) {
    console.error('분석 JSON 파일을 찾을 수 없습니다:', resultJsonUrl, e)
    errorMessage.value = '분석 결과를 불러올 수 없습니다. 업로드 후 처리 중이거나 파일명이 올바르지 않습니다.'
    jointData.value = []
    currentJointData.value = null
  }
})

const onTimeUpdate = () => {
  const t = videoRef.value?.currentTime || 0
  currentFrameIndex.value = Math.floor(t * VIDEO_FPS.value)
}
const goBack = () => {
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
  /* 최대 높이를 설정해 세로로 긴 비디오가 화면을 과도하게 차지하지 않도록 함 */
  max-height: 70vh;
  height: auto;
  /* 화면에 맞춰 안 잘리게 표시 */
  object-fit: contain;
  display: block;
  background: #000; /* 검은 배경으로 비디오 주변 여백 보정 */
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