<template>
  <div class="container">
    <div class="search-container">
      <input
        v-model="username"
        type="text"
        placeholder="이름을 입력하세요"
        class="search-input"
      />
      <button @click="handleSearch" class="search-button">검색</button>
    </div>

    <ag-grid-vue
      class="ag-theme-alpine"
      style="width: 100%; height: 400px;"
      :rowData="rowData"
      :columnDefs="columnDefs"
      :modules="modules"
      :animateRows="true"
      :domLayout="'autoHeight'"
      @grid-ready="onGridReady"
    />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'
import { AgGridVue } from 'ag-grid-vue3'
import 'ag-grid-community/styles/ag-grid.css'
import 'ag-grid-community/styles/ag-theme-alpine.css'
import { ClientSideRowModelModule } from 'ag-grid-community'

const modules = [ClientSideRowModelModule]

const username = ref('')
const rowData = ref([])

const columnDefs = [
  { field: 'userid', headerName: 'ID' },
  { field: 'userpass', headerName: '비밀번호' },
  { field: 'username', headerName: '이름' },
  { field: 'usermail', headerName: '이메일' },
]

const handleSearch = () => {
  axios.post('/api/user_search', {
    s_username: username.value,
  })
    .then(response => {
      if (Array.isArray(response.data)) {
        rowData.value = response.data
      } else if (response.data.status === 'NOT') {
        alert('검색된 데이터가 없습니다.')
        rowData.value = []
      }
    })
    .catch(error => {
      console.error('Error fetching data:', error)
    })
}
</script>

<style scoped>
.container {
  width: 100%;
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.search-container {
  width: 25%;
  display: flex;
  align-items: center;
  margin-bottom: 20px;
}

.search-input {
  flex-grow: 1;
  padding: 10px;
  margin-right: 20px;
  border-radius: 5px;
  border: 1px solid #ccc;
  font-size: 16px;
}

.search-button {
  padding: 10px 20px;
  width: auto; /* width를 auto로 변경하여 텍스트에 맞게 확장되도록 */
  min-width: 70px; /* 최소 너비를 지정하여 버튼 크기를 설정 */
  height: 40px;
  background-color: #28a745;
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-size: 16px; /* 글자 크기를 16px로 변경 */
  text-align: center; /* 텍스트 가운데 정렬 */
  display: flex; /* 플렉스 박스로 변경하여 텍스트 세로 정렬 방지 */
  justify-content: center; /* 가로 중앙 정렬 */
  align-items: center; /* 세로 중앙 정렬 */
  white-space: nowrap; /* 글자가 자동으로 줄 바꿈되지 않도록 */
}


.search-button:hover {
  background-color: #218838;
}

.ag-theme-alpine {
  border-radius: 5px;
  overflow: hidden;
}
</style>
