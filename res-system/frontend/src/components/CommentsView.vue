<!-- src/components/CommentsBoard.vue -->
<template>
  <div>
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
      <div v-for="c in comments" :key="c.analysisId" class="comment-item">
        <strong>[프레임 {{ c.frameIndex }}] {{ c.tag }}</strong><br />
        {{ c.memo }}<br />
        <button @click="deleteComment(c.analysisId)">삭제</button>
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

// Props: currentJointData, analysisId / 부모에게 전달받는 데이터
const props = defineProps({
  currentJointData: { type: Object, required: false },
  analysisId: { type: String, required: true },
})

// 상태
const commentText = ref('')
const commentTag = ref('')
const comments = ref([])

// 프레임이 바뀌면 댓글 목록 갱신
watch(() => props.currentJointData, () => {
  fetchComments()
})

// analysisId가 바뀌어도 갱신
watch(() => props.analysisId, () => {
  fetchComments()
})

// 메모 저장
async function submitComment() {
  if (!props.currentJointData || !commentText.value.trim()) return
  const payload = {
    userId: store.state.store_userid1,
    analysisId: props.analysisId,
    frameIndex: props.currentJointData.frame,
    tag: commentTag.value.trim(),
    memo: commentText.value.trim(),
  }
  try {
    const res = await axios.post('/comments/add', payload)
    comments.value.push(res.data)
    commentText.value = ''
    commentTag.value = ''
    alert('메모가 저장되었습니다.')
    fetchComments()  // 저장 후 목록 갱신
  } catch (err) {
    alert('메모 저장 실패: ' + err.message)
  }
}

// 메모 목록 불러오기
async function fetchComments() {
  if (!props.analysisId) {
    comments.value = []
    return
  }
  try {
    const res = await axios.get(`/comments/${encodeURIComponent(props.analysisId)}`)  // URL 안전하게 인코딩
    comments.value = res.data
  } catch (e) {
    console.error('메모 불러오기 실패:', e)
  }
}

// 메모 삭제
async function deleteComment(analysisId) {
  if (!confirm('정말로 이 메모를 삭제하시겠습니까?')) return
  try {
    await axios.delete(`/comments/delete/${analysisId}`)  // 안전 인코딩 필요없음
    alert('메모가 삭제되었습니다.')
    fetchComments()
  } catch (e) {
    alert('삭제 실패: ' + e.message)
  }
}

onMounted(() => {
  fetchComments()
})
</script>

<style scoped>
.comment-form {
  margin-top: 1rem;
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
