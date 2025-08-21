<template>
  <div class="landmark-wrapper g-section">
    <!-- 관절 선택 -->
    <div v-if="jointKeys.length" class="selector-container">
      <label for="joint">관절 선택:</label>
      <select id="joint" v-model="selectedJointLocal">
        <option value="">전체 보기</option>
        <option v-for="k in jointKeys" :key="k" :value="k">
          {{ (koreanJointNameMap && koreanJointNameMap[k]) || k }}
        </option>
      </select>
    </div>

    <!-- 프레임 정보 -->
  <div v-if="safeCurrent && typeof safeCurrent === 'object' && Object.keys(safeCurrent).length">
      <div v-if="!selectedJointLocal" class="joint-list scroll-area">
        <div
          v-for="item in filteredEntries"
          :key="item.k"
          class="joint-badge"
          :style="{ borderLeftColor: (paletteMap && paletteMap[item.k]) || '#ccc' }"
        >
          <span>{{ (koreanJointNameMap && koreanJointNameMap[item.k]) || item.k }}</span>
          <strong>{{ isNum(item.v) ? Number(item.v).toFixed(1) : '-' }}</strong>
        </div>
      </div>

      <!-- 단일 -->
      <div
        v-else
        class="joint-highlight"
    :style="{ background: highlightBg, borderColor: highlightColor }"
      >
  <span class="frame-info">Frame: {{ (safeCurrent && safeCurrent.frame) || '-' }}</span>
        <span class="joint-name">
          {{ (koreanJointNameMap && koreanJointNameMap[selectedJointLocal]) || selectedJointLocal }}
        </span>
        <span class="joint-value">
          {{ isNum(currentValue) ? Number(currentValue).toFixed(2) : '-' }}
        </span>
      </div>
    </div>

    <!-- 차트 -->
      <div v-if="jointData.length" class="chart-container u-card">
        <template v-if="hasNumericData">
          <canvas ref="chartRef"></canvas>
        </template>
        <template v-else>
          <div class="no-data" style="padding:24px; text-align:center; color:#666">
            차트에 표시할 각도/COM 데이터가 없습니다.
          </div>
        </template>
      </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { defineProps, defineEmits } from 'vue'
import Chart from 'chart.js/auto'

/* ---------- Props & Emits ---------- */
const props = defineProps({
  jointData: { type: Array, required: false, default: () => [] },
  currentJointData: { type: Object, required: false, default: () => ({}) },
  koreanJointNameMap: { type: Object, required: false, default: () => ({}) },
  comStabilityScores: { type: Array, default: () => [] },
  currentFrameIndex: { type: Number, required: false, default: 0 },
  videoFps: { type: [Number, String], required: false, default: 30 },
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
// safeCurrent ensures we never call Object.entries on undefined/null and
// provides a stable object reference for the template to read from.
const safeCurrent = computed(() =>
  props.currentJointData && typeof props.currentJointData === 'object' && Object.keys(props.currentJointData).length
    ? props.currentJointData
    : null
)

const filteredJointData = computed(() =>
  safeCurrent.value ? Object.entries(safeCurrent.value).filter(([k]) => k !== 'frame') : []
)

// Safer entries for template iteration: { k, v }
const filteredEntries = computed(() =>
  filteredJointData.value.map(([k, v]) => ({ k, v }))
)

// currentValue returns the selected joint value from currentJointData or null
const currentValue = computed(() => {
  if (!safeCurrent.value) return null
  const key = selectedJointLocal.value
  if (!key) return null
  const v = safeCurrent.value[key]
  return v === undefined ? null : v
})

/* ---------- Palette (정적) ---------- */
const palette = i => `hsl(${(i * 45) % 360} 70% 55%)`
const paletteMap = computed(() => {
  const map = Object.fromEntries(jointKeys.value.map((k, i) => [k, palette(i)]))
  map['com_stability_score'] = '#ffa500'
  return map
})

/* ---------- Highlight Color ---------- */
const highlightColor = computed(() => paletteMap.value[selectedJointLocal.value] || '#888')
const highlightBg = computed(() => highlightColor.value + '22')
const isNum = v => typeof v === 'number' && !isNaN(v)

// true when any numeric (non-null) value exists in the jointData rows
const hasNumericData = computed(() => {
  if (!jointData.value || !jointData.value.length) return false
  for (const r of jointData.value) {
    for (const k of Object.keys(r)) {
      if (k === 'frame') continue
      const v = r[k]
      if (typeof v === 'number' && !isNaN(v)) return true
    }
  }
  return false
})

/* ---------- Chart ---------- */
let chartInstance = null
const chartRef = ref(null)
let needsUpdate = false
// value used by Chart plugin to position the red-line (frame number)
let pluginCurrentFrame = 0

// Chart.js plugin: draws a vertical red line at the provided frame index
const redLinePlugin = {
  id: 'redLinePlugin',
  afterDraw(chart) {
    if (!chart.config || !chart.config.options || chart.config.options._drawRedLine !== true) return
    const ctx = chart.ctx
    const xScale = chart.scales['x']
    if (!xScale) return
  // Use the module-level pluginCurrentFrame to avoid touching chart.options (prevents scriptable recursion)
  const frame = typeof pluginCurrentFrame === 'number' ? pluginCurrentFrame : null
    if (frame === null) return
    // find pixel for frame on x-scale
    const labels = chart.data.labels || []
    let x = null
    // 1) Try directly asking the scale for the pixel (works for numeric/linear/time scales)
    try {
      const maybe = xScale.getPixelForValue(Number(frame))
      if (typeof maybe === 'number' && !isNaN(maybe)) x = maybe
    } catch (e) {
      // ignore and fall through to other strategies
    }

    // 2) If that didn't work, try matching labels exactly or numerically
    if (x === null) {
      let idx = labels.indexOf(frame)
      if (idx === -1) idx = labels.findIndex(l => Number(l) === Number(frame))
      if (idx !== -1) {
        try {
          const maybe2 = xScale.getPixelForValue(labels[idx])
          if (typeof maybe2 === 'number' && !isNaN(maybe2)) x = maybe2
        } catch (e) {
          // ignore
        }
      }
    }

    // 3) Fallback: numeric-interpolate across chart area using numeric label bounds
    if (x === null) {
      const numericLabels = labels.map(l => Number(l)).filter(n => !isNaN(n))
      if (numericLabels.length >= 2) {
        const min = Math.min(...numericLabels)
        const max = Math.max(...numericLabels)
        const ratio = max === min ? 0 : (Number(frame) - min) / (max - min)
        const left = chart.chartArea.left
        const right = chart.chartArea.right
        const clamped = Math.max(0, Math.min(1, ratio || 0))
        x = left + clamped * (right - left)
      }
    }
    if (x === null) return
    ctx.save()
    ctx.strokeStyle = 'rgba(255,0,0,0.9)'
    ctx.lineWidth = 2
    ctx.beginPath()
    ctx.moveTo(x, chart.chartArea.top)
    ctx.lineTo(x, chart.chartArea.bottom)
    ctx.stroke()
    ctx.restore()
  }
}
Chart.register(redLinePlugin)

function buildDatasets() {
  const ds = []
  // sanitize rows: ensure each entry is an object and has a frame
  const rows = (jointData.value || []).filter(r => r && typeof r === 'object')
  const labels = rows.map(r => (r && (r.frame ?? null)))

  if (!rows.length) return { ds, labels }

    if (selectedJointLocal.value === 'com_stability_score') {
    ds.push({
      label: 'COM 안정성',
      data: (props.comStabilityScores || []).map(d => (d && d.score) || 0),
      borderColor: paletteMap.value['com_stability_score'],
      backgroundColor: '#ffa50033',
      tension: 0.4,
      pointRadius: 0,
      borderWidth: 2,
      fill: true,
      spanGaps: true,
    })
    } else if (selectedJointLocal.value) {
    const k = selectedJointLocal.value
    const label = (props.koreanJointNameMap && props.koreanJointNameMap[k]) || k
    const color = paletteMap.value[k] || '#888'
    ds.push({
      label,
      data: rows.map(r => (r && r[k] !== undefined ? r[k] : null)),
      borderColor: color,
      backgroundColor: color + '33',
      tension: 0.4,
      pointRadius: 0,
      borderWidth: 2,
      spanGaps: true,
    })
  } else {
    jointKeys.value.forEach(k => {
      const label = (props.koreanJointNameMap && props.koreanJointNameMap[k]) || k
      const color = paletteMap.value[k] || '#888'
      ds.push({
        label,
        data: rows.map(r => (r && r[k] !== undefined ? r[k] : null)),
        borderColor: color,
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
        _drawRedLine: true,
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
    safeUpdate()
  }
}

// Safe update helper: perform chart update asynchronously and fall back to recreate on error
function safeUpdate() {
  if (!chartInstance) return
  // run async to avoid re-entrant scriptable resolution on the same call stack
  setTimeout(() => {
    try {
      chartInstance.update('none')
    } catch (err) {
      console.warn('[LandmarkView] chart update failed, attempting rebuild', err && err.message)
      try {
        const data = chartInstance.data
        const options = chartInstance.options
        chartInstance.destroy()
        chartInstance = new Chart(chartRef.value, { type: 'line', data, options })
      } catch (re) {
        console.error('[LandmarkView] chart rebuild failed', re && re.message)
      }
    }
  }, 0)
}

// Update plugin frame and redraw chart when currentFrameIndex prop changes
watch(() => props.currentFrameIndex, (nf) => {
  try {
    pluginCurrentFrame = Number(nf) || 0
    if (chartInstance) {
      // plugin reads pluginCurrentFrame directly; just trigger a redraw
      chartInstance.update('none')
    }
  } catch (e) {
    // non-fatal
  }
})

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
// Debug: surface safeCurrent & filteredEntries
onMounted(() => {
  try {
    console.debug('[DBG] LandmarkView safeCurrent', safeCurrent.value, 'filteredEntries', filteredEntries.value.slice(0,10))
  } catch (e) {
    console.debug('[DBG] LandmarkView debug failed', e && e.message)
  }
})
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
