<template><div class="container g-card">
    <div class="search-container">
      <button class="search-button delete-button" @click="handleDelete" :disabled="!hasSelectedRows">삭제</button>
    </div>

    <ag-grid-vue
      class="ag-theme-alpine"
      style="width: 100%; height: 600px;" 
      :rowData="rowData"
      :columnDefs="columnDefs"
      :animateRows="true"
      :domLayout="'autoHeight'"
      rowSelection="multiple"
      :suppressRowClickSelection="true"
      @grid-ready="onGridReady"
      @selection-changed="onSelectionChanged"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, computed, nextTick } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'
import { useStore } from 'vuex'
import 'ag-grid-community/dist/styles/ag-grid.css'
import 'ag-grid-community/dist/styles/ag-theme-alpine.css'
import { AgGridVue } from 'ag-grid-vue3'

const store = useStore()
const router = useRouter()
const userId = computed(() => store.state.store_userid1)
const rowData = ref([])

const playOriginalVideo = (vidName) => {
  router.push({ name: 'VideoplayView', query: { filename: vidName } })
}
const playSkeletonVideo = (vidName, evalResult) => {
  router.push({ name: 'VideoresultView',
  query: { skeletonVideo: `skeleton_${vidName}`,
    result: evalResult
  } })
}

const columnDefs = [
  { headerCheckboxSelection: true, checkboxSelection: true, width: 40, suppressSizeToFit: true },
  { field: 'userid', headerName: 'User ID' },
  { field: 'vid_name', headerName: '비디오 이름' },
  { field: 'eval', headerName: '평가' },
  { field: 'upload_date', headerName: '업로드 시간' },  // ✅ 추가됨
  {
    headerName: '업로드 영상',
    cellRenderer: () => {
      return `<button class="btn-play" data-type="original">▶</button>`
    },
    onCellClicked: (params) => {
      const type = params.event?.target?.dataset?.type
      if (type === 'original') {
        playOriginalVideo(params.data.vid_name)
      }
    }
  },
  {
    headerName: '분석 결과',
    cellRenderer: () => {
      return `<button class="btn-play" data-type="skeleton">▶</button>`
    },
    onCellClicked: (params) => {
      const type = params.event?.target?.dataset?.type
      if (type === 'skeleton') {
        playSkeletonVideo(params.data.vid_name, params.data.eval)
      }
    }
  }
]


const gridApi = ref(null)
const gridColumnApi = ref(null)
const hasSelectedRows = ref(false)

const handleSearch = () => {
  if (!userId.value) {
    rowData.value = []
    return
  }

  axios.post('/images/file_search', {
    userid: userId.value,
  })
    .then(async (response) => {
      if (Array.isArray(response.data)) {
        rowData.value = response.data.map(item => ({
          ...item,
          eval: item.eval === 0 ? 'Bad' : item.eval === 1 ? 'Good' : 'Unknown'
        }))
        await nextTick()
        autoSizeAll()
      } else if (response.data.status === 'NOT') {
        rowData.value = []
      }
    })
    .catch(error => {
      console.error('Error fetching data:', error)
    })
}

const onGridReady = (params) => {
  gridApi.value = params.api
  gridColumnApi.value = params.columnApi
  autoSizeAll()
}

const onSelectionChanged = () => {
  if (gridApi.value) {
    const selectedUsers = gridApi.value.getSelectedRows()
    hasSelectedRows.value = selectedUsers.length > 0
  }
}

const autoSizeAll = () => {
  if (gridColumnApi.value) {
    const allColumnIds = gridColumnApi.value.getAllColumns().map(col => col.getColId())
    gridColumnApi.value.autoSizeColumns(allColumnIds, false)
  }
}

const handleDelete = async () => {
  if (!gridApi.value) return
  const selectedRows = gridApi.value.getSelectedRows()
  if (selectedRows.length === 0) {
    alert('삭제할 항목을 선택하세요.')
    return
  }

  const confirmDelete = confirm(`${selectedRows.length}개의 파일을 삭제하시겠습니까?`)
  if (!confirmDelete) return

  try {
    const response = await axios.post('/images/file_delete', {
      list: selectedRows
    })

    alert(response.data.message || '삭제 성공')
    handleSearch()
  } catch (error) {
    console.error('삭제 실패:', error)
    alert('삭제에 실패했습니다.')
  }
}

onMounted(() => {
  handleSearch()
})
</script>

<style scoped>
.btn-play {
  background-color: #4caf50;
  color: white;
  border: none;
  padding: 4px 10px;
  border-radius: 4px;
  cursor: pointer;
}
.btn-play:hover {
  background-color: #388e3c;
}

/* 메인 컨테이너 */
.container {
  max-width: 1200px;
  margin: 0.1rem auto; /* 기존 2rem → 1rem */
  padding: 1rem;
  font-family: 'Segoe UI', sans-serif;
}

.search-container {
  display: flex;
  justify-content: flex-start; /* 왼쪽 정렬로 변경 */
  margin-bottom: 0.5rem;
}

/* 삭제 버튼 스타일 */
.search-button.delete-button {
  background-color: #dc3545;
  color: white;
  border: none;
  padding: 10px 18px;
  font-size: 1rem;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.search-button.delete-button:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

.search-button.delete-button:hover:not(:disabled) {
  background-color: #b02a37;
}

/* ▶ 재생 버튼 스타일 */
.btn-play {
  background-color: #007bff;
  color: white;
  border: none;
  padding: 6px 12px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: background-color 0.2s ease;
}

.btn-play:hover {
  background-color: #0056b3;
}

/* ag-grid override */
.ag-theme-alpine {
  border-radius: 8px;
  overflow: hidden;
  font-size: 14px;
  --ag-header-background-color: #f8f9fa;
  --ag-header-foreground-color: #212529;
  --ag-header-height: 42px;
  --ag-row-hover-color: #f1f1f1;
}

/* 데이터 없을 때 여백 정리 */
.ag-root-wrapper {
  min-height: 200px;
}

/* 행 간 구분선 추가 (선택 사항) */
.ag-row {
  border-bottom: 1px solid #e0e0e0;
}

</style>
