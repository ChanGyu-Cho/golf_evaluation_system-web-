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
            <div class="chart-canvas-wrap" style="position:relative">
              <canvas ref="chartRef"></canvas>
              <div ref="overlayRef" class="red-line-overlay" aria-hidden="true"></div>
            </div>
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
const overlayRef = ref(null)

function computeOverlayPosition() {
  try {
    if (!chartInstance || !chartInstance.chartArea) return
    const left = chartInstance.chartArea.left
    const right = chartInstance.chartArea.right
    // determine numeric x-range from datasets
    let xs = []
    for (const ds of (chartInstance.data && chartInstance.data.datasets) || []) {
      for (const p of ds.data || []) {
        if (p && typeof p.x === 'number' && !isNaN(p.x)) xs.push(p.x)
      }
    }
    if (!xs.length) return
    const minX = Math.min(...xs)
    const maxX = Math.max(...xs)
    const f = Number(pluginCurrentFrame)
    const ratio = maxX === minX ? 0 : (f - minX) / (maxX - minX)
    const clamped = Math.max(0, Math.min(1, ratio || 0))
    const xPx = left + clamped * (right - left)
    if (overlayRef.value && overlayRef.value.style) {
      overlayRef.value.style.left = `${Math.round(xPx)}px`
      overlayRef.value.style.height = `${chartInstance.chartArea.bottom - chartInstance.chartArea.top}px`
      overlayRef.value.style.top = `${chartInstance.chartArea.top}px`
      overlayRef.value.style.display = 'block'
    }
  } catch (e) {
    // eslint-disable-next-line no-console
    console.debug('[LandmarkView] computeOverlayPosition failed', e && e.message)
  }
}

// Chart.js plugin: draws a vertical red line at the provided frame index
// redLinePlugin intentionally left as a no-op for canvas drawing.
// We use the DOM overlay (.red-line-overlay) as the single source of truth
// for the vertical red time marker to avoid duplicate/ghost lines.
const redLinePlugin = {
  id: 'redLinePlugin',
  afterDraw(/* chart */) {
    // no-op: canvas-based drawing disabled in favor of DOM overlay
    return
  }
}
Chart.register(redLinePlugin)

function buildDatasets() {
  const ds = []
  // sanitize rows: ensure each entry is an object and has a frame
  const rows = (jointData.value || []).filter(r => r && typeof r === 'object')
  // labels kept for debugging but we will use numeric x values in datasets
  const labels = rows.map(r => Number(r && (r.frame ?? null)))

  if (!rows.length) return { ds, labels }

    if (selectedJointLocal.value === 'com_stability_score') {
    ds.push({
      label: 'COM 안정성',
      data: (props.comStabilityScores || []).map(d => ({ x: Number(d && d.frame) || 0, y: (d && d.score) || 0 })),
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
      data: rows.map(r => ({ x: Number(r.frame), y: (r && r[k] !== undefined ? r[k] : null) })),
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
        data: rows.map(r => ({ x: Number(r.frame), y: (r && r[k] !== undefined ? r[k] : null) })),
        borderColor: color,
        tension: 0.35,
        pointRadius: 0,
        spanGaps: true,
        fill: false,
      })
    })
  }
  return { ds }
}

function updateChart() {
  if (!chartRef.value) return
  const { ds } = buildDatasets()
    if (!chartInstance) {
    chartInstance = new Chart(chartRef.value, {
      type: 'line',
      data: { datasets: ds },
      options: {
        _drawRedLine: true,
        responsive: true,
        animation: false,
        parsing: false, // we provide {x,y} points
        normalized: true,
        scales: {
          x: { type: 'linear', grid: { color: 'rgba(0,0,0,0.05)' }, title: { display: true, text: 'Frame' } },
          y: { grid: { color: 'rgba(0,0,0,0.05)' } },
        },
        plugins: {
          legend: { position: 'bottom', labels: { padding: 12 } },
          tooltip: {
            mode: 'nearest',
            intersect: false,
            // filter out items with null/undefined y to avoid internal Chart.js tooltip errors
            filter: function(item) {
              try {
                return item && item.parsed && item.parsed.y !== null && item.parsed.y !== undefined
              } catch (e) { return false }
            }
          },
        }
      }
    })
  } else {
    // replace datasets while keeping existing chart options
    // temporarily disable tooltip while swapping datasets to avoid tooltip trying to reference
    // dataset/element indices that may be in-flight during the update (prevents getLabelAndValue null errors)
    try {
      if (!chartInstance.options) chartInstance.options = {}
      if (!chartInstance.options.plugins) chartInstance.options.plugins = {}
      if (!chartInstance.options.plugins.tooltip) chartInstance.options.plugins.tooltip = {}
      chartInstance.options.plugins.tooltip.enabled = false
    } catch (e) {
      // ignore
    }
    chartInstance.data.datasets = ds
    safeUpdate()
    // re-enable tooltip after a short delay once the update has settled
    setTimeout(() => {
      try {
        if (chartInstance && chartInstance.options && chartInstance.options.plugins && chartInstance.options.plugins.tooltip) {
          chartInstance.options.plugins.tooltip.enabled = true
          safeUpdate()
        }
      } catch (err) {
        console.debug('[LandmarkView] re-enable tooltip failed', err && err.message)
      }
    }, 100)
  }
  try { computeOverlayPosition() } catch(e) { console.debug('[LandmarkView] computeOverlayPosition error', e && e.message) }
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
  try { computeOverlayPosition() } catch(e){ console.debug('[LandmarkView] computeOverlayPosition error', e && e.message) }
  }, 0)
}

// Update plugin frame and redraw chart when currentFrameIndex prop changes
watch(() => props.currentFrameIndex, (nf) => {
  try {
    pluginCurrentFrame = Number(nf) || 0
  // eslint-disable-next-line no-console
  console.debug('[LandmarkView] watcher currentFrameIndex ->', pluginCurrentFrame)
  if (chartInstance) safeUpdate()
    } catch (e) {
      // non-fatal
      console.debug('[LandmarkView] watcher currentFrameIndex error', e && e.message)
    }
})

// Also watch the provided currentJointData object (parent passes this per-frame object).
// When available, prefer its `frame` value for the red-line to match what the comment view shows.
watch(() => props.currentJointData, (nj) => {
  try {
    if (nj && typeof nj === 'object' && nj.frame !== undefined && nj.frame !== null) {
      pluginCurrentFrame = Number(nj.frame) || 0
    } else {
      pluginCurrentFrame = Number(props.currentFrameIndex) || 0
    }
  // eslint-disable-next-line no-console
  console.debug('[LandmarkView] watcher currentJointData ->', pluginCurrentFrame, nj && nj.frame)
  if (chartInstance) safeUpdate()
  } catch (e) {
    // ignore
    console.debug('[LandmarkView] watcher currentJointData error', e && e.message)
  }
}, { deep: false })

// initialize pluginCurrentFrame on mount to prefer currentJointData.frame when available
onMounted(() => {
  try {
    const cj = props.currentJointData
    if (cj && typeof cj === 'object' && cj.frame !== undefined && cj.frame !== null) {
      pluginCurrentFrame = Number(cj.frame) || 0
    } else {
      pluginCurrentFrame = Number(props.currentFrameIndex) || 0
    }
    // ensure chart is drawn with initial plugin frame
  if (chartInstance) safeUpdate()
  // position overlay after mount
  setTimeout(() => { try { computeOverlayPosition() } catch(e){ console.debug('[LandmarkView] computeOverlayPosition timeout error', e && e.message) } }, 50)
  } catch (e) {
    // non-fatal
    console.debug('[LandmarkView] onMounted init error', e && e.message)
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
/* overlay red-line */
.red-line-overlay {
  position: absolute;
  width: 2px;
  background: rgba(255,0,0,0.95);
  top: 0;
  left: 0;
  display: none;
  pointer-events: none;
  z-index: 5;
}
</style>
