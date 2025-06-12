<template>
  <div class="comments-wrapper g-section">
    <!-- ── 입력 ───────────────────────────── -->
    <div v-if="currentJointData" class="comment-form u-card">
      <h4 class="form-title">
        현재 프레임&nbsp;<strong>{{ currentJointData.frame }}</strong>
      </h4>

      <input v-model.trim="commentTag" class="comment-input" placeholder="태그" />
      <textarea v-model.trim="commentText" rows="3" class="comment-textarea" placeholder="메모" />

      <button
        class="u-btn u-btn-field round-btn"
        @click="submitComment"
        :disabled="loadingSave"
      >
        {{ loadingSave ? '저장 중…' : '저장' }}
      </button>
    </div>

    <!-- ── 목록 ───────────────────────────── -->
    <div v-if="comments.length" class="comment-list u-card">
      <div class="list-header">
        <h3>메모 목록 ({{ comments.length }})</h3>

        <!-- ⭐ 전체 삭제 버튼 -->
        <button
          class="u-btn u-btn-flag round-btn btn-sm"
          @click="deleteAll"
          :disabled="loadingDelAll"
        >
          {{ loadingDelAll ? '삭제 중…' : '전체 삭제' }}
        </button>
      </div>

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
          @click.stop="deleteSingle(c.analysis_id)"
          :disabled="loadingDelSingle === c.analysis_id || loadingDelAll"
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
const commentText   = ref('')
const commentTag    = ref('')
const comments      = ref([])
const nextIdx       = ref(0)
const loadingSave   = ref(false)
const loadingDelSingle = ref('')   // 개별
const loadingDelAll    = ref(false)

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
      const mm = id.match(/_(\d+)$/)
      return mm ? Math.max(m, +mm[1]) : m
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
    userId:      store.state.store_userid1,
    analysis_id: fullId,
    frame_index: props.currentJointData.frame,
    tag:         commentTag.value,
    memo:        commentText.value,
  }

  try {
    await axios.post('/comments/add', payload)
    commentText.value = ''; commentTag.value = ''
    nextIdx.value++
    await fetchComments()
  } catch (e) { alert('저장 실패: '+e.message) }
  finally     { loadingSave.value = false }
}

/* ── 개별 삭제 ── */
async function deleteSingle(fullId) {
  if (!confirm('이 메모를 삭제하시겠습니까?')) return
  loadingDelSingle.value = fullId
  try {
    await axios.delete(`/comments/delete/${fullId}`)
    await fetchComments()
    alert('메모가 삭제되었습니다.')
  } catch (e) { alert('삭제 실패: '+e.message) }
  finally     { loadingDelSingle.value = '' }
}

/* ── 전체 삭제 ── */
async function deleteAll() {
  if (!confirm('이 영상의 모든 메모를 삭제하시겠습니까?')) return
  loadingDelAll.value = true
  try {
    await axios.delete(`/comments/allDelete/${props.analysis_id}`)
    await fetchComments()
    alert('모든 메모가 삭제되었습니다.')
  } catch (e) { alert('삭제 실패: '+e.message) }
  finally     { loadingDelAll.value = false }
}

/* ── Watch & Mount ── */
watch(
  () => [props.analysis_id],
  fetchComments
)
onMounted(fetchComments)
</script>

<style scoped>
/* 스타일 동일 + 목록 헤더 레이아웃 */
.comments-wrapper{display:flex;flex-direction:column;gap:20px;align-items:center}
.comment-form{width:min(90%,600px)}
.comment-input,.comment-textarea{width:100%;box-sizing:border-box;padding:8px 10px;margin-bottom:8px;border:1px solid #ccc;border-radius:var(--radius-md);font-size:0.95rem}
.comment-textarea{resize:vertical}
.round-btn{border-radius:999px;padding:10px 26px}
.comment-list{width:min(90%,600px);max-height:380px;overflow-y:auto;display:flex;flex-direction:column;gap:12px}
.list-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px}
.comment-item{padding:10px 14px;background:var(--panel-bg);border-left:6px solid;border-radius:var(--radius-md);box-shadow:var(--shadow-md);cursor:pointer;transition:background 0.15s}
.comment-item:hover{background:var(--panel-bg,#fff)ee}
.comment-header{display:flex;gap:6px;align-items:baseline;margin-bottom:4px}
.timestamp{font-size:0.8rem;color:var(--sky-color);font-weight:600}
.comment-body{margin:0 0 8px;white-space:pre-line;word-break:break-word}
.btn-sm{padding:4px 12px;font-size:0.8rem;border-radius:var(--radius-md)}
</style>
