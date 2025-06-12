<template>
  <div class="landmark-wrapper g-section">
    <!-- 관절 선택 -->
    <div v-if="jointKeys.length" class="selector-container">
      <label for="joint">관절 선택:</label>
      <select id="joint" v-model="selectedJointLocal">
        <option value="">전체 보기</option>
        <option v-for="k in jointKeys" :key="k" :value="k">
          {{ koreanJointNameMap[k] || k }}
        </option>
      </select>
    </div>

    <!-- 프레임 정보 -->
    <div v-if="currentJointData">
      <div v-if="!selectedJointLocal" class="joint-list scroll-area">
        <div
          v-for="[k, v] in filteredJointData"
          :key="k"
          class="joint-badge"
          :style="{ borderLeftColor: paletteMap[k] }"
        >
          <span>{{ koreanJointNameMap[k] || k }}</span>
          <strong>{{ isNum(v) ? v.toFixed(1) : '-' }}</strong>
        </div>
      </div>

      <!-- 단일 -->
      <div
        v-else
        class="joint-highlight"
        :style="{ background: highlightBg, borderColor: highlightColor }"
      >
        <span class="frame-info">Frame: {{ currentJointData.frame }}</span>
        <span class="joint-name">
          {{ koreanJointNameMap[selectedJointLocal] || selectedJointLocal }}
        </span>
        <span class="joint-value">
          {{
            isNum(currentJointData[selectedJointLocal])
              ? currentJointData[selectedJointLocal].toFixed(2)
              : '-'
          }}
        </span>
      </div>
    </div>

    <!-- 차트 -->
    <div v-if="jointData.length" class="chart-container u-card">
      <canvas ref="chartRef"></canvas>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { defineProps, defineEmits } from 'vue'
import Chart from 'chart.js/auto'

/* ---------- Props & Emits ---------- */
const props = defineProps({
  jointData: { type: Array, required: true },
  currentJointData: { type: Object, required: false },
  koreanJointNameMap: { type: Object, required: true },
  comStabilityScores: { type: Array, default: () => [] },
  modelValue: { type: String, default: '' },
})
const emit = defineEmits(['update:modelValue'])

/* ---------- Reactive State ---------- */
const selectedJointLocal = ref(props.modelValue)
watch(() => props.modelValue, v => (selectedJointLocal.value = v))
watch(selectedJointLocal, v => emit('update:modelValue', v))

const jointData = computed(() => props.jointData || [])
const jointKeys = computed(() =>
  jointData.value.length ? Object.keys(jointData.value[0]).filter(k => k !== 'frame') : []
)
const filteredJointData = computed(() =>
  props.currentJointData
    ? Object.entries(props.currentJointData).filter(([k]) => k !== 'frame')
    : []
)

/* ---------- Palette (정적) ---------- */
const palette = i => `hsl(${i * 45 % 360} 70% 55%)`
const paletteMap = Object.fromEntries(jointKeys.value.map((k, i) => [k, palette(i)]))
paletteMap['com_stability_score'] = '#ffa500'

/* ---------- Highlight Color ---------- */
const highlightColor = computed(() => paletteMap[selectedJointLocal.value] || '#888')
const highlightBg = computed(() => highlightColor.value + '22')
const isNum = v => typeof v === 'number' && !isNaN(v)

/* ---------- Chart ---------- */
let chartInstance = null
const chartRef = ref(null)
let needsUpdate = false

function buildDatasets() {
  const ds = []
  const rows = jointData.value
  const labels = rows.map(r => r.frame)

  if (!labels.length) return { ds, labels }

  if (selectedJointLocal.value === 'com_stability_score') {
    ds.push({
      label: 'COM 안정성',
      data: props.comStabilityScores.map(d => d.score),
      borderColor: paletteMap['com_stability_score'],
      backgroundColor: '#ffa50033',
      tension: 0.4,
      pointRadius: 0,
      borderWidth: 2,
      fill: true,
      spanGaps: true,
    })
  } else if (selectedJointLocal.value) {
    const k = selectedJointLocal.value
    ds.push({
      label: props.koreanJointNameMap[k] || k,
      data: rows.map(r => r[k]),
      borderColor: paletteMap[k],
      backgroundColor: paletteMap[k] + '33',
      tension: 0.4,
      pointRadius: 0,
      borderWidth: 2,
      spanGaps: true,
    })
  } else {
    jointKeys.value.forEach(k => {
      ds.push({
        label: props.koreanJointNameMap[k] || k,
        data: rows.map(r => r[k]),
        borderColor: paletteMap[k],
        tension: 0.35,
        pointRadius: 0,
        spanGaps: true,
        fill: false,
      })
    })
  }
  return { ds, labels }
}

function updateChart() {
  if (!chartRef.value) return
  const { ds, labels } = buildDatasets()
  if (!chartInstance) {
    chartInstance = new Chart(chartRef.value, {
      type: 'line',
      data: { labels, datasets: ds },
      options: {
        responsive: true,
        animation: false,
        scales: {
          x: { grid: { color: 'rgba(0,0,0,0.05)' }, title: { display: true, text: 'Frame' } },
          y: { grid: { color: 'rgba(0,0,0,0.05)' } },
        },
        plugins: {
          legend: { position: 'bottom', labels: { padding: 12 } },
          tooltip: { mode: 'index', intersect: false },
        }
      }
    })
  } else {
    chartInstance.data.labels = labels
    chartInstance.data.datasets = ds
    chartInstance.update('none')
  }
}

/* ---------- RAF Batching ---------- */
function scheduleUpdate() {
  if (needsUpdate) return
  needsUpdate = true
  requestAnimationFrame(() => {
    needsUpdate = false
    updateChart()
  })
}

watch([jointData, selectedJointLocal], scheduleUpdate)
onMounted(updateChart)
</script>

<style scoped>
/* ---- 기존 스타일(단일 카드 사이즈·팔레트 라벨 등) 그대로 유지 ---- */
.scroll-area { max-height: 260px; overflow-y: auto; }

.selector-container {
  display: flex; justify-content: center; gap: 8px;
  background: var(--panel-bg); padding: 12px 16px;
  border-radius: var(--radius-md); backdrop-filter: blur(4px);
  margin: 0 auto 12px;
}
.selector-container select { padding: 6px 10px; border: 1px solid #ccc; border-radius: var(--radius-md); }

/* 카드형 */
.joint-list { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 8px; }
.joint-badge {
  background: var(--panel-bg); padding: 6px 10px; border-radius: var(--radius-md);
  box-shadow: var(--shadow-md); display: flex; justify-content: space-between; font-size: 0.9rem;
  border-left: 6px solid transparent;
}

/* 하이라이트 */
.joint-highlight {
  border: 2px solid; border-radius: var(--radius-lg);
  padding: 14px 20px; text-align: center; box-shadow: var(--shadow-md); font-size: 1rem;
  display: flex; flex-direction: column; gap: 4px;
}
.frame-info { font-size: 0.8rem; opacity: 0.8; }
.joint-name { font-weight: 700; }
.joint-value { font-size: 1.4rem; letter-spacing: 0.5px; }

/* 차트 */
.chart-container {
  width: min(90%, 900px);
  margin: 0 auto;
  height: 380px;                 /* ▶︎ 약 80 px 더 높게 */
  background: var(--panel-bg);
  padding: 12px 16px; border-radius: var(--radius-lg); box-shadow: var(--shadow-md);
}
.chart-container canvas { width: 100% !important; }
</style>
