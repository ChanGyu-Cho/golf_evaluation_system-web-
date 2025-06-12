<!-- src/components/LandmarkView.vue -->
<template>
  <div class="landmark-wrapper g-section">
    <!-- ── 관절 선택 ───────────────────────────── -->
    <div class="selector-container" v-if="jointKeys.length">
      <label for="jointSelect">관절 선택:</label>
      <select id="jointSelect" v-model="selectedJointLocal">
        <option value="">전체 보기</option>
        <option v-for="key in jointKeys" :key="key" :value="key">
          {{ koreanJointNameMap[key] || key }}
        </option>
      </select>
    </div>

    <!-- ── 현재 프레임 각도 / COM ──────────────── -->
    <div v-if="currentJointData">
      <!-- 전체 보기 -->
      <div v-if="!selectedJointLocal" class="joint-list scroll-area">
        <div
          v-for="[key, value] in filteredJointData"
          :key="key"
          class="joint-badge"
        >
          <span>{{ koreanJointNameMap[key] || key }}</span>
          <strong>
            {{ (typeof value === 'number' && !isNaN(value)) ? value.toFixed(1) : '-' }}
          </strong>
        </div>
      </div>

      <!-- 단일 관절 -->
      <div v-else class="joint-highlight">
        <span class="frame-info">Frame: {{ currentJointData.frame }}</span>
        <span class="joint-name">
          {{ koreanJointNameMap[selectedJointLocal] || selectedJointLocal }}
        </span>
        <span class="joint-value">
          {{
            (typeof currentJointData[selectedJointLocal] === 'number' &&
              !isNaN(currentJointData[selectedJointLocal]))
              ? currentJointData[selectedJointLocal].toFixed(2)
              : '-'
          }}
        </span>
      </div>
    </div>

    <!-- ── 차트 ────────────────────────────────── -->
    <div
      v-if="jointData && jointData.length"
      class="chart-container u-card"
    >
      <canvas ref="chartRef" height="160"></canvas>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { defineProps, defineEmits } from 'vue'
import Chart from 'chart.js/auto'

/* ===== Props & v-model ===== */
const props = defineProps({
  jointData: { type: Array, required: true },
  currentJointData: { type: Object, required: false },
  koreanJointNameMap: { type: Object, required: true },
  comStabilityScores: { type: Array, default: () => [] },
  modelValue: { type: String, default: '' },
})
const emit = defineEmits(['update:modelValue'])

/* ===== 상태 ===== */
const selectedJointLocal = ref(props.modelValue)
watch(() => props.modelValue, v => (selectedJointLocal.value = v))
watch(selectedJointLocal, v => emit('update:modelValue', v))

const combinedData = computed(() => props.jointData || [])
const jointData = combinedData          // 템플릿 호환

const jointKeys = computed(() =>
  combinedData.value.length
    ? Object.keys(combinedData.value[0]).filter(k => k !== 'frame')
    : []
)

const filteredJointData = computed(() =>
  props.currentJointData
    ? Object.entries(props.currentJointData).filter(([k]) => k !== 'frame')
    : []
)

/* ===== Chart ===== */
const chartRef = ref(null)
let chartInstance = null

const palette = i => `hsl(${i * 45 % 360} 70% 55%)`

function drawChart () {
  if (!chartRef.value || !combinedData.value.length) return

  const labels = combinedData.value.map(d => d.frame)
  const ds = []

  /* COM 안정성 */
  if (selectedJointLocal.value === 'com_stability_score') {
    ds.push({
      label: 'COM 안정성',
      data: props.comStabilityScores.map(d => d.score),
      borderColor: palette(3),
      backgroundColor: 'rgba(255,165,0,0.25)',
      tension: 0.4,
      pointRadius: 0,
      borderWidth: 2,
      fill: true,
      spanGaps: true,
    })
  }
  /* 단일 관절 */
  else if (selectedJointLocal.value) {
    const k = selectedJointLocal.value
    ds.push({
      label: props.koreanJointNameMap[k] || k,
      data: combinedData.value.map(d => d[k]),
      borderColor: palette(1),
      backgroundColor: 'rgba(72,149,239,0.25)',
      tension: 0.4,
      pointRadius: 0,
      borderWidth: 2,
      spanGaps: true,
    })
  }
  /* 전체 */
  else {
    jointKeys.value.forEach((k, i) => {
      ds.push({
        label: props.koreanJointNameMap[k] || k,
        data: combinedData.value.map(d => d[k]),
        borderColor: palette(i),
        tension: 0.35,
        pointRadius: 0,
        spanGaps: true,
        fill: false,
      })
    })
  }

  chartInstance?.destroy()
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
}

/* ===== Watchers ===== */
watch([combinedData, selectedJointLocal], drawChart, { immediate: true })
watch(() => props.currentJointData, () => chartInstance?.update('none'))
onMounted(drawChart)
</script>

<style scoped>
/* 공통 스크롤 제한 */
.scroll-area { max-height: 260px; overflow-y: auto; }

/* 선택 박스 */
.selector-container {
  display: flex;
  justify-content: center;
  gap: 8px;
  background: var(--panel-bg);
  padding: 12px 16px;
  border-radius: var(--radius-md);
  backdrop-filter: blur(4px);
  margin: 0 auto 12px;
}
.selector-container select {
  padding: 6px 10px;
  border: 1px solid #ccc;
  border-radius: var(--radius-md);
}

/* 전체 보기 카드형 */
.joint-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 8px;
}
.joint-badge {
  background: var(--panel-bg);
  padding: 6px 10px;
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-md);
  display: flex;
  justify-content: space-between;
  font-size: 0.9rem;
}

/* 단일 관절 하이라이트 */
.joint-highlight {
  background: var(--field-color);
  color: #fff;
  border-radius: var(--radius-lg);
  padding: 18px 24px;
  text-align: center;
  box-shadow: var(--shadow-md);
  font-size: 1.2rem;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.joint-name   { font-weight: 700; }
.joint-value  { font-size: 1.6rem; }

/* 차트 컨테이너: 90%/900px & 중앙 */
.chart-container {
  width: min(90%, 900px);
  margin: 0 auto;
  padding: 12px 16px;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
}
/* Canvas 폭 100% */
.chart-container canvas { width: 100% !important; }
</style>
