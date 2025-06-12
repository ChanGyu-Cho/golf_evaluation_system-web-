<template>
  <div class="comments-wrapper g-section">
    <!-- 입력 -->
    <div v-if="currentJointData" class="comment-form u-card">
      <h4 class="form-title">
        현재 프레임&nbsp;<strong>{{ currentJointData.frame }}</strong>
      </h4>

      <input v-model.trim="commentTag" class="comment-input" placeholder="태그" />
      <textarea v-model.trim="commentText" rows="3" class="comment-textarea" placeholder="메모" />

      <button class="u-btn u-btn-field round-btn" @click="submitComment" :disabled="loadingSave">
        {{ loadingSave ? '저장 중…' : '저장' }}
      </button>
    </div>

    <!-- 목록 -->
    <div v-if="comments.length" class="comment-list u-card">
      <h3>메모 목록 ({{ comments.length }})</h3>

      <div
        v-for="c in comments"
        :key="c.analysis_id"
        class="comment-item"
        :style="{ borderLeftColor: palette(c.tag) }"
      >
        <div class="comment-header">
          <span class="timestamp">Frame {{ c.frame_index }}</span>
          <strong>{{ c.tag || '태그 없음' }}</strong>
        </div>
        <p class="comment-body">{{ c.memo }}</p>

        <button
          class="u-btn u-btn-field btn-sm"
          @click.stop="deleteComment(c.analysis_id)" 
          :disabled="loadingDel === c.analysis_id"
        >
          삭제
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { defineProps } from 'vue'
import axios from 'axios'
import { useStore } from 'vuex'
const store = useStore()

/* ── Props ── */
const props = defineProps({
  currentJointData: { type: Object },
  analysis_id:      { type: String, required: true }, // userId_videoName
})

/* ── 상태 ── */
const commentText = ref('')
const commentTag  = ref('')
const comments    = ref([])
const nextIdx     = ref(0)
const loadingSave = ref(false)
const loadingDel  = ref('')

/* ── 팔레트 ── */
const palette = t => `hsl(${[...t].reduce((a,c)=>(a+c.charCodeAt(0))%360,0)} 70% 75%)`

/* ── 목록 + idx 계산 ── */
async function fetchComments() {
  if (!props.analysis_id) return
  try {
    const { data } = await axios.get(`/comments/${encodeURIComponent(props.analysis_id)}`)
    comments.value = Array.isArray(data) ? data : []

    const max = comments.value.reduce((m, c) => {
      const id = c.analysis_id ?? ''
      const m2 = id.match(/_(\d+)$/)
      return m2 ? Math.max(m, +m2[1]) : m
    }, -1)
    nextIdx.value = max + 1
  } catch (e) {
    console.error('메모 불러오기 실패:', e)
    comments.value = []; nextIdx.value = 0
  }
}

/* ── 저장 ── */
async function submitComment() {
  if (!props.currentJointData || !commentText.value.trim()) return
  loadingSave.value = true

  const fullId = `${props.analysis_id}_${nextIdx.value}`

  const payload = {
    userId:       store.state.store_userid1,
    analysis_id:  fullId,
    frame_index:  props.currentJointData.frame,
    tag:          commentTag.value,
    memo:         commentText.value,
  }

  try {
    await axios.post('/comments/add', payload)
    commentText.value = ''; commentTag.value = ''
    nextIdx.value++
    await fetchComments()           // ← 다시 목록
  } catch (e) { alert('저장 실패: ' + e.message) }
  finally   { loadingSave.value = false }
}

/* ── 개별 삭제 ── */
async function deleteComment(fullId) {
  if (!confirm('이 메모를 삭제하시겠습니까?')) return
  loadingDel.value = fullId
  try {
    await axios.delete(`/comments/delete/${fullId}`)
    await fetchComments()           // ← 삭제 후 목록
  } catch (e) { alert('삭제 실패: ' + e.message) }
  finally   { loadingDel.value = '' }
}

/* ── 워치 & 마운트 ── */
watch(
  () => [props.analysis_id, props.currentJointData?.frame],
  fetchComments
)
onMounted(fetchComments)
</script>

<style scoped>
/* (스타일 동일) */
.comments-wrapper{display:flex;flex-direction:column;gap:20px;align-items:center}
.comment-form{width:min(90%,600px)}
.comment-input,.comment-textarea{width:100%;box-sizing:border-box;padding:8px 10px;margin-bottom:8px;border:1px solid #ccc;border-radius:var(--radius-md);font-size:0.95rem}
.comment-textarea{resize:vertical}
.round-btn{border-radius:999px;padding:10px 26px}
.comment-list{width:min(90%,600px);max-height:380px;overflow-y:auto;display:flex;flex-direction:column;gap:12px}
.comment-item{padding:10px 14px;background:var(--panel-bg);border-left:6px solid;border-radius:var(--radius-md);box-shadow:var(--shadow-md);cursor:pointer;transition:background 0.15s}
.comment-item:hover{background:var(--panel-bg,#fff)ee}
.comment-header{display:flex;gap:6px;align-items:baseline;margin-bottom:4px}
.timestamp{font-size:0.8rem;color:var(--sky-color);font-weight:600}
.comment-body{margin:0 0 8px;white-space:pre-line;word-break:break-word}
.btn-sm{padding:4px 12px;font-size:0.8rem;border-radius:var(--radius-md)}
</style>
