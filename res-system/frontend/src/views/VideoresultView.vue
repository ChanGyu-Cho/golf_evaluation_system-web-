<template>
  <div class="result-page-container">
    <button @click="goBack">다시 업로드하러 가기</button>
    <h2>분류 결과: {{ result }}</h2>

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

    <!-- 선택박스 -->
    <div class="selector-container" v-if="jointKeys.length">
      <label for="jointSelect">관절 선택:</label>
      <select id="jointSelect" v-model="selectedJoint">
        <option value="">전체 보기</option>
        <option v-for="key in jointKeys" :key="key" :value="key">
          {{ koreanJointNameMap[key] || key }}
        </option>
      </select>
    </div>

    <!-- 현재 프레임의 관절 각도 및 COM -->
    <div v-if="currentJointData" class="joint-data-viewer">
      <h3>프레임: {{ currentJointData.frame }}</h3>
      <div v-if="!selectedJoint">
        <div
          v-for="[key, value] in filteredJointData"
          :key="key"
          class="joint-item"
        >
          {{ koreanJointNameMap[key] || key }}: {{ value !== null ? value.toFixed(2) : '-' }}
        </div>
      </div>
      <div v-else>
        <div class="joint-item">
          {{ koreanJointNameMap[selectedJoint] || selectedJoint }}:
          {{ currentJointData[selectedJoint] !== null && currentJointData[selectedJoint] !== undefined 
            ? currentJointData[selectedJoint].toFixed(2) 
            : '-' }}
        </div>
      </div>
    </div>

    <!-- 차트 -->
    <div v-if="jointData.length" class="chart-container">
      <canvas ref="chartRef" width="800" height="200"></canvas>
    </div>

    <!-- 메모 입력 -->
    <div class="comment-form" v-if="currentJointData">
      <h4>현재 프레임 {{ currentJointData.frame }}에 메모 남기기</h4>
      <input v-model="commentTag" placeholder="태그 (예: 백스윙)" />
      <textarea v-model="commentText" placeholder="메모 내용 입력"></textarea>
      <button @click="submitComment">저장</button>
    </div>

    <!-- 메모 목록 -->
    <div class="comment-list" v-if="comments.length">
      <h3>메모 목록</h3>
      <div v-for="c in comments" :key="c.id" class="comment-item">
        <strong>[프레임 {{ c.frameIndex }}] {{ c.tag }}</strong><br />
        {{ c.memo }}<br />
        <button @click="deleteComment(c.id)">삭제</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Chart from 'chart.js/auto'
import axios from 'axios'
import { useStore } from 'vuex'

const store = useStore()
const store_userid1 = computed(() => store.state.store_userid1)

const route = useRoute()
const router = useRouter()

const result = ref('')
const skeletonVideoUrl = ref(null)
const videoRef = ref(null)
const chartRef = ref(null)
const svu = ref('')

const jointData = ref([])  // 관절 각도 데이터 배열 [{frame:0, left_elbow_flexion:..., ...}, ...]
const comData = ref([])    // COM 데이터 배열 [{frame:0, x:..., y:..., z:...}, ...]
const currentJointData = ref(null)

// 선택한 관절명 (빈 문자열이면 전체보기)
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
// 관절 데이터와 COM 데이터를 합쳐서 하나의 배열로 만듦
const combinedData = computed(() => {
  return jointData.value
})


// 한 프레임 데이터에서 frame 제외한 모든 키 목록 (관절명 + com_x,y,z)
const jointKeys = computed(() => {
  if (!combinedData.value.length) return []
  return Object.keys(combinedData.value[0]).filter(k => k !== 'frame')
})

const currentFrameIndex = ref(0)

watch(
  () => currentFrameIndex.value,
  (newFrame) => {
    if (!combinedData.value.length) return
    currentJointData.value = combinedData.value.find(d => d.frame === newFrame) || combinedData.value[0]
  },
  { immediate: true }
)


// 현재 프레임 데이터에서 frame 제외한 (key,value) 배열
const filteredJointData = computed(() => {
  if (!currentJointData.value) return []
  return Object.entries(currentJointData.value).filter(([key]) => key !== 'frame')
})

// --- 태그+메모 기능 관련 ---
const commentText = ref('')
const commentTag = ref('')
const comments = ref([])

const analysisId = computed(() => {
  return `${store_userid1.value}_${svu.value}`
})

async function submitComment() {
  if (!currentJointData.value || !commentText.value.trim()) return
  const payload = {
    userId: store_userid1.value,
    analysisId: analysisId.value,
    frameIndex: currentJointData.value.frame,
    tag: commentTag.value.trim(),
    memo: commentText.value.trim(),
  }

  try {
    const res = await axios.post('/comments/add', payload)
    comments.value.push(res.data)
    commentText.value = ''
    commentTag.value = ''
    alert('메모가 저장되었습니다.')
  } catch (err) {
    alert('메모 저장 실패: ' + err.message)
  }
  commentsUpdate()
}

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
        comData.value = []  // 더이상 별도 사용 안함
      } else {
        jointData.value = jsonData
        comData.value = []
      }


      currentFrameIndex.value = 0
      currentJointData.value = combinedData.value[0] || null

      await nextTick()
      initChart()
    } catch (e) {
      console.error('JSON 불러오기 실패:', e)
    }
  }
  commentsUpdate()
})

async function commentsUpdate() {
  if (analysisId.value) {
    try {
      const res = await axios.get(`/comments/${encodeURIComponent(analysisId.value)}`)
      comments.value = res.data
      console.log('불러온 메모:', comments.value)
    } catch (e) {
      console.error('메모 불러오기 실패:', e)
    }
  }
}

async function deleteComment(commentId) {
  if (!confirm('정말로 이 메모를 삭제하시겠습니까?')) return

  try {
    await axios.delete(`/comments/delete/${commentId}`)
    alert('메모가 삭제되었습니다.')
    commentsUpdate()
  } catch (e) {
    alert('삭제 실패: ' + e.message)
  }
}

// onTimeUpdate에서 currentFrameIndex 설정
function onTimeUpdate() {
  const currentTime = videoRef.value?.currentTime || 0
  const currentFrame = Math.floor(currentTime * VIDEO_FPS.value)
  currentFrameIndex.value = currentFrame
  updateChartHighlight()
}

function goBack() {
  router.push({ name: 'main', query: { view: 'menu3' } })
}

// --- Chart.js 관련 코드 ---
let chartInstance = null

function initChart() {
  if (!chartRef.value || !combinedData.value.length) return

  const labels = combinedData.value.map(d => d.frame)

  const datasets = selectedJoint.value
    ? [{
        label: koreanJointNameMap[selectedJoint.value] || selectedJoint.value,
        data: combinedData.value.map(d => d[selectedJoint.value] ?? null),
        borderColor: 'blue',
        backgroundColor: 'rgba(0,0,255,0.2)',
        fill: true,
        pointRadius: 0,
        borderWidth: 2,
      }]
    : []

  if (chartInstance) {
    chartInstance.destroy()
  }

  chartInstance = new Chart(chartRef.value.getContext('2d'), {
    type: 'line',
    data: {
      labels,
      datasets
    },
    options: {
      responsive: true,
      animation: false,
      scales: {
        x: {
          title: {
            display: true,
            text: '프레임',
          }
        },
        y: {
          title: {
            display: true,
            text: selectedJoint.value && selectedJoint.value.startsWith('com_') ? '좌표 값' : '각도',
          }
        }
      },
      plugins: {
        legend: {
          display: true
        },
        tooltip: {
          mode: 'index',
          intersect: false,
        },
        annotation: {
          annotations: {}
        }
      }
    },
    plugins: [chartHighlightPlugin]
  })
}

// 선택 관절 바뀔 때 차트 다시 그림
watch(selectedJoint, () => {
  initChart()
})

// 비디오 현재 프레임 하이라이트 표시 플러그인
const chartHighlightPlugin = {
  id: 'chartHighlightPlugin',
  afterDraw(chart) {
    if (!chartInstance) return
    if (!currentJointData.value) return

    const ctx = chart.ctx
    const xScale = chart.scales.x
    const frame = currentJointData.value.frame

    const x = xScale.getPixelForValue(frame)

    ctx.save()
    ctx.beginPath()
    ctx.strokeStyle = 'red'
    ctx.lineWidth = 2
    ctx.moveTo(x, chart.chartArea.top)
    ctx.lineTo(x, chart.chartArea.bottom)
    ctx.stroke()
    ctx.restore()
  }
}

// 차트 하이라이트 업데이트
function updateChartHighlight() {
  if (chartInstance) {
    chartInstance.update('none')
  }
}
</script>

<style>
/* 전체 페이지 스크롤 가능하게 */
.result-page-container {
  min-height: 100vh;
  padding: 2rem 1rem;
  overflow-y: auto;
  background-color: #fff;
}

/* 비디오 */
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

/* 관절 정보 */
.joint-data-viewer {
  margin-top: 1rem;
  padding: 1rem;
  background: #f9f9f9;
  border-radius: 8px;
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
  font-family: monospace;
}

.joint-item {
  margin-bottom: 0.3rem;
}

/* 관절 선택 드롭다운 */
.selector-container {
  max-width: 600px;
  margin: 1rem auto;
  text-align: center;
}

/* 차트 */
.chart-container {
  max-width: 800px;
  margin: 1rem auto;
}

/* 메모 작성 폼 */
.comment-form {
  margin: 1rem auto;
  padding: 1rem;
  max-width: 600px;
  border: 1px solid #ddd;
  border-radius: 8px;
  background-color: #fefefe;
}

.comment-form input,
.comment-form textarea {
  display: block;
  width: 100%;
  margin: 0.5rem 0;
  padding: 0.5rem;
  border-radius: 4px;
  border: 1px solid #ccc;
}

/* 메모 목록 */
.comment-list {
  max-width: 600px;
  margin: 1rem auto;
  overflow: auto;
  word-break: break-word;
}

.comment-item {
  margin-bottom: 1rem;
  padding: 0.5rem;
  background-color: #eef;
  border-radius: 4px;
}
</style>
