<!-- src/views/VideoplayView.vue -->
<template>
  <div class="result-root">
    <!-- ── 상단 블록(하늘 배경) ───────────────────────── -->
    <section class="top-block">
      <!-- 제목 -->
      <h2 class="result-heading">원본 영상</h2>

      <!-- 뒤로가기(오른쪽 위) -->
      <button class="u-btn u-btn-flag round-btn back-btn" @click="goBack">
        뒤로가기
      </button>

      <!-- 비디오 -->
      <video
        v-if="videoSrc"
        controls
        autoplay
        class="result-video"
      >
        <source :src="videoSrc" type="video/mp4" />
        브라우저가 비디오를 지원하지 않습니다.
      </video>

      <div v-else role="alert">비디오를 불러오는 중…</div>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const router   = useRouter()
const route    = useRoute()
const videoSrc = ref(null)

onMounted(() => {
  const filename = route.query.filename
  if (filename) {
    videoSrc.value = `/images/search_video?filename=${encodeURIComponent(filename)}`
  }
})

function goBack() {
  router.push({ name: 'main', query: { view: 'menu3' } })
}
</script>

<style scoped>
/* ── Page 배경 ───────────────────────────── */
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

/* ── 상단 카드 ───────────────────────────── */
.top-block {
  position: relative;                 /* back-btn 고정용 */
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24px;
  padding: 32px 24px;
  background: var(--sky-color);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
}

.result-heading {
  margin: 0;
  font-size: 24px;
  font-weight: 700;
  color: #000;
  background: #fff;
  padding: 12px 28px;
  border-radius: 10px;
  box-shadow: var(--shadow-sm);
}

/* ── 뒤로가기 버튼 ───────────────────────── */
.round-btn      { border-radius: 999px; padding: 10px 26px; box-shadow: var(--shadow-md); }
.round-btn:hover{ filter: brightness(0.95); }
.back-btn {
  position: absolute;
  top: 20px;
  right: 24px;
}

/* ── 비디오 ──────────────────────────────── */
.result-video {
  max-width: 640px;
  width: 100%;
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);
  background: #000;
}

[role="alert"] {
  font-size: 1rem;
  color: #555;
}
</style>
