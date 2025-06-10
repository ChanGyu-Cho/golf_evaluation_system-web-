<!-- src/components/LandmarkInfo.vue -->
<template>
  <div>
    <!-- 선택박스 -->
    <div class="selector-container" v-if="jointKeys.length">
      <label for="jointSelect">관절 선택:</label>
      <select id="jointSelect" v-model="selectedJointLocal">
        <option value="">전체 보기</option>
        <option v-for="key in jointKeys" :key="key" :value="key">
          {{ koreanJointNameMap[key] || key }}
        </option>
      </select>
    </div>

    <!-- 현재 프레임의 관절 각도 및 COM -->
    <div v-if="currentJointData" class="joint-data-viewer">
      <h3>프레임: {{ currentJointData.frame }}</h3>
      <div v-if="!selectedJointLocal">
        <div
          v-for="[key, value] in filteredJointData"
          :key="key"
          class="joint-item"
        >
          {{ koreanJointNameMap[key] || key }}:
          {{ (typeof value === 'number' && !isNaN(value)) ? value.toFixed(2) : '-' }}
        </div>
      </div>
      <div v-else>
        <div class="joint-item">
          {{ koreanJointNameMap[selectedJointLocal] || selectedJointLocal }}:
          {{
            (typeof currentJointData[selectedJointLocal] === 'number' && !isNaN(currentJointData[selectedJointLocal]))
              ? currentJointData[selectedJointLocal].toFixed(2)
              : '-'
          }}
        </div>
      </div>
    </div>

    <!-- 차트 -->
    <div v-if="jointData.length" class="chart-container">
      <canvas ref="chartRef" width="800" height="200"></canvas>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { defineProps, defineEmits } from 'vue'
import Chart from 'chart.js/auto'

// Props: jointData, currentJointData, koreanJointNameMap, modelValue for selectedJoint
const props = defineProps({
  jointData: { type: Array, required: true },
  currentJointData: { type: Object, required: false },
  koreanJointNameMap: { type: Object, required: true },
  comStabilityScores: { type: Array, default: () => [] }, // 추가
  modelValue: { type: String, default: '' },
})

const emit = defineEmits(['update:modelValue'])

// local selectedJoint to sync with parent via v-model:selectedJoint
const selectedJointLocal = ref(props.modelValue)
watch(() => props.modelValue, v => {
  selectedJointLocal.value = v
})
watch(selectedJointLocal, v => {
  emit('update:modelValue', v)
})

// computed: combinedData is just jointData here
const combinedData = computed(() => props.jointData || [])

// jointKeys: 첫 프레임 키 목록 (frame 제외)
const jointKeys = computed(() => {
  if (!combinedData.value.length) return []
  return Object.keys(combinedData.value[0]).filter(k => k !== 'frame')
})

// filteredJointData: 현재 프레임 데이터의 [key,value] 쌍 (frame 제외)
const filteredJointData = computed(() => {
  if (!props.currentJointData) return []
  return Object.entries(props.currentJointData).filter(([key]) => key !== 'frame')
})


// 차트 관련
const chartRef = ref(null)
let chartInstance = null

function initChart() {
  if (!chartRef.value || !combinedData.value.length) return

  const labels = combinedData.value.map(d => d.frame)
  let datasets = []

  if (selectedJointLocal.value === 'com_stability_score') {
    // ✅ COM 안정성 지표 차트
    const stabilityLabels = props.comStabilityScores.map(d => d.frame)
    const stabilityData = props.comStabilityScores.map(d => d.score)

    datasets.push({
      label: 'COM 안정성 지표',
      data: stabilityData,
      borderColor: 'orange',
      backgroundColor: 'rgba(255,165,0,0.2)',
      fill: true,
      pointRadius: 0,
      borderWidth: 2,
      spanGaps: true,
    })

    chartInstance?.destroy()
    chartInstance = new Chart(chartRef.value.getContext('2d'), {
      type: 'line',
      data: { labels: stabilityLabels, datasets },
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
              text: 'COM 안정성 score (0에 가까울수록 안정)',
            }
          }
        },
        plugins: {
          legend: { display: true },
          tooltip: { mode: 'index', intersect: false },
        }
      },
      plugins: [highlightPlugin()]
    })
    return
  }

  // ✅ 기존 joint chart 로직
  if (selectedJointLocal.value) {
    const data = combinedData.value.map(d => {
      const v = d[selectedJointLocal.value]
      return (typeof v === 'number' ? v : null)
    })
    datasets.push({
      label: props.koreanJointNameMap[selectedJointLocal.value] || selectedJointLocal.value,
      data,
      borderColor: 'blue',
      backgroundColor: 'rgba(0,0,255,0.2)',
      fill: true,
      pointRadius: 0,
      borderWidth: 2,
      spanGaps: true,
    })
  } else {
    jointKeys.value.forEach((key, idx) => {
      const data = combinedData.value.map(d => {
        const v = d[key]
        return (typeof v === 'number' ? v : null)
      })
      datasets.push({
        label: props.koreanJointNameMap[key] || key,
        data,
        borderColor: `hsl(${(idx * 50) % 360}, 70%, 50%)`,
        fill: false,
        pointRadius: 0,
        spanGaps: true,
      })
    })
  }

  chartInstance?.destroy()
  chartInstance = new Chart(chartRef.value.getContext('2d'), {
    type: 'line',
    data: { labels, datasets },
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
            text: selectedJointLocal.value && selectedJointLocal.value.startsWith('com_')
              ? '무게중심 좌표 값 (0~1)'
              : '각도 (도)',
          }
        }
      },
      plugins: {
        legend: { display: true },
        tooltip: { mode: 'index', intersect: false },
      }
    },
    plugins: [highlightPlugin()]
  })
}

// 하이라이트 플러그인 재사용
function highlightPlugin() {
  return {
    id: 'chartHighlightPlugin',
    afterDraw(chart) {
      if (!chartInstance) return
      if (!props.currentJointData) return
      const ctx = chart.ctx
      const xScale = chart.scales.x
      const frame = props.currentJointData.frame
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
}


// jointData 또는 selectedJoint 변경 시 차트 업데이트
watch([() => combinedData.value, selectedJointLocal], () => {
  initChart()
}, { immediate: true })

// currentJointData 변경 시 차트 리프레시 (highlight 이동)
watch(() => props.currentJointData, () => {
  if (chartInstance) {
    chartInstance.update('none')
  }
})

onMounted(() => {
  initChart()
})
</script>

<style scoped>
.selector-container {
  max-width: 600px;
  margin: 1rem auto;
  text-align: center;
}
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
.chart-container {
  max-width: 800px;
  margin: 1rem auto;
}
</style>
