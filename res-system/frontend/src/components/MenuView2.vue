<template>
  <div class="container">
    <!-- 이름 검색 -->
    <div class="search-container">
      <input
        v-model="username"
        type="text"
        placeholder="이름을 입력하세요"
        class="search-input"
      />
      <button @click="handleSearch" class="search-button">검색</button>
    </div>

    <!-- 사용자 정보 입력 -->
    <div class="insert-container">
      <input v-model="newUser.id" type="text" placeholder="아이디" class="insert-input" />
      <input v-model="newUser.password" type="password" placeholder="비밀번호" class="insert-input" />
      <input v-model="newUser.name" type="text" placeholder="이름" class="insert-input" />
      <input v-model="newUser.mail" type="mail" placeholder="이메일" class="insert-input" />
      <button @click="handleAdd" class="insert-button">추가</button>
    </div>

    <!-- 하단 버튼 -->
    <div class="action-buttons">
      <button @click="handleEdit" class="action-button edit">수정</button>
      <button @click="handleDelete" class="action-button delete">삭제</button>
      <button @click="handleReset" class="action-button reset">초기화</button>
    </div>

    <!-- 그리드 -->
    <ag-grid-vue
      class="ag-theme-alpine"
      style="width: 100%; height: 400px;"
      :rowData="rowData"
      :columnDefs="columnDefs"
      :modules="modules"
      :animateRows="true"
      :domLayout="'autoHeight'"
      @grid-ready="onGridReady"
      rowSelection="multiple" 
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

const newUser = ref({
  id: '',
  password: '',
  name: '',
  mail: ''
})

const columnDefs = [
{
    headerName: '',
    field: 'checkbox',
    checkboxSelection: true,
    headerCheckboxSelection: true,
    width: 50,
    suppressMenu: true,
    pinned: 'left', // 선택사항: 항상 왼쪽에 고정
  },
  { field: 'userid', headerName: 'ID' },
  { field: 'userpass', headerName: '비밀번호' },
  { field: 'username', headerName: '이름' },
  { field: 'usermail', headerName: '이메일' },
]

const handleSearch = () => {
  // 만약 username이 비어 있으면 null을 보내도록 처리
  const searchTerm = username.value.trim() === '' ? null : username.value;

  axios.post('/api/user_search', {
    s_username: searchTerm,
  })
    .then(response => {
      if (Array.isArray(response.data)) {
        rowData.value = response.data;
      } else if (response.data.status === 'NOT') {
        alert('검색된 데이터가 없습니다.');
        rowData.value = [];
      }
    })
    .catch(error => {
      console.error('Error fetching data:', error);
    });
}

const handleAdd = async() => {
  // newUser 값을 insertForm으로 설정하여 서버로 전달
  const insertForm = {
    s_userid: newUser.value.id,
    s_userpass: newUser.value.password,
    s_username: newUser.value.name,
    s_usermail: newUser.value.mail
  }

  axios.post('/api/user_insert', insertForm)
    .then(response => {
      alert(response.data)
      // 사용자 추가 후 입력 필드 초기화
      newUser.value.id = ''
      newUser.value.password = ''
      newUser.value.name = ''
      newUser.value.mail = ''

      handleSearch() // 검색 결과를 새로고침하여 추가된 사용자 확인
    })
    .catch(error => {
      console.error('Error adding user:', error)
      alert('사용자 추가 실패')
    })
}

const handleEdit = () => {
  alert('수정 기능은 아직 구현되지 않았습니다.')
}

const handleDelete = () => {

}

const handleReset = () => {
  alert('초기화 기능은 아직 구현되지 않았습니다.')
}
</script>

<style scoped>
.container {
  width: 100%;
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
  
}

.search-container,
.insert-container {
  width: 25%;
  display: flex;
  align-items: center;
  margin-bottom: 20px;
  gap: 10px;
  
}

.search-input,
.insert-input {
  width: 120px;
  flex-grow: 1;
  padding: 10px;
  border-radius: 5px;
  border: 1px solid #ccc;
  font-size: 16px;
}

.search-button,
.insert-button {
  padding: 10px 20px;
  min-width: 70px;
  height: 40px;
  background-color: #28a745;
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-size: 16px;
  display: flex;
  justify-content: center;
  align-items: center;
  white-space: nowrap;
}

.search-button:hover,
.insert-button:hover {
  background-color: #218838;
}

.action-buttons {
  width: 30%;
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.action-button {
  flex: 1;
  padding: 10px;
  font-size: 16px;
  border: none;
  border-radius: 5px;
  color: white;
  cursor: pointer;
}

.action-button.edit {
  background-color: #007bff;
}

.action-button.delete {
  background-color: #dc3545;
}

.action-button.reset {
  background-color: #6c757d;
}

.action-button:hover {
  opacity: 0.9;
}

.ag-theme-alpine {
  border-radius: 5px;
  overflow: hidden;
}
</style>
