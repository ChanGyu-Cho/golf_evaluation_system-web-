
<template><div class="container g-card">
    <div class="search-container">
      <input v-model="username" type="text" placeholder="이름을 입력하세요" class="search-input" />
      <button @click="handleSearch" class="search-button">검색</button>
    </div>

    <div class="insert-container">
      <input v-model="newUser.id" type="text" placeholder="아이디" class="insert-input" />
      <input v-model="newUser.password" type="password" placeholder="비밀번호" class="insert-input" />
      <input v-model="newUser.name" type="text" placeholder="이름" class="insert-input" />
      <input v-model="newUser.mail" type="mail" placeholder="이메일" class="insert-input" />
      <button @click="handleAdd" class="insert-button">추가</button>
    </div>

    <div class="action-buttons">
      <button @click="handleDelete" class="action-button delete" :disabled="selectedUsers.length === 0">삭제</button>
      <button @click="handleReset" class="action-button reset">초기화</button>
    </div>

    <ag-grid-vue
      class="ag-theme-alpine"
      style="width: 100%; height: 400px;"
      :rowData="rowData"
      :columnDefs="columnDefs"
      :defaultColDef="defaultColDef"
      rowSelection="multiple"
      :rowMultiSelectWithClick="true"
      :suppressRowClickSelection="true"
      @grid-ready="onGridReady"
      @selection-changed="onSelectionChanged"
      @row-clicked="onRowClicked"  
    />

    <!-- ★ 추가: 상세 팝업 컴포넌트, v-if로 조건부 표시 -->
    <DetailUserView
      v-if="isDetailPopupOpen"
      :user="selectedUserForDetail"
      @close="onDetailClose"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { AgGridVue } from 'ag-grid-vue3'
import 'ag-grid-community/dist/styles/ag-grid.css'
import 'ag-grid-community/dist/styles/ag-theme-alpine.css'
import router from '@/router'

import DetailUserView from './detailUserView.vue'  // 팝업 컴포넌트 임포트

const username = ref('')
const rowData = ref([])
const gridApi = ref(null)
const newUser = ref({
  id: '',
  password: '',
  name: '',
  mail: ''
})
const selectedUsers = ref([])

// 팝업 상태 및 선택된 사용자 정보
const isDetailPopupOpen = ref(false)
const selectedUserForDetail = ref(null)

const checkAccess = () => {
  const store_userid1 = localStorage.getItem('userid1') || null;

  if (store_userid1 !== 'admin') {
    alert('접근 권한이 없습니다.');
    if (router) {
      router.replace('/main');
    } else {
      window.location.href = '/main';
    }
  }
}

onMounted(() => {
  checkAccess();
  handleSearch();
})

const onSelectionChanged = () => {
  if (gridApi.value) {
    const selectedNodes = gridApi.value.getSelectedNodes();
    selectedUsers.value = selectedNodes.map(node => node.data);

    if (selectedUsers.value.length === 1) {
      const user = selectedUsers.value[0];
      newUser.value = {
        id: user.userid,
        password: user.userpass,
        name: user.username,
        mail: user.usermail
      };
    } else {
      newUser.value = { id: '', password: '', name: '', mail: '' };
    }
  }
};

// 행 클릭 시 상세 팝업 띄우기
const onRowClicked = (event) => {
  selectedUserForDetail.value = event.data;
  isDetailPopupOpen.value = true;
};

const defaultColDef = {
  flex: 1,
  minWidth: 100,
  resizable: true,
  sortable: true
}

const columnDefs = ref([
  {
    headerCheckboxSelection: true,
    checkboxSelection: true,
    width: 50,
    pinned: 'left'
  },
  { field: 'userid', headerName: 'ID' },
  { field: 'userpass', headerName: '비밀번호' },
  { field: 'username', headerName: '이름' },
  { field: 'usermail', headerName: '이메일' },
])

const handleSearch = () => {
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
      username.value = '';
    })
    .catch(error => {
      console.error('Error fetching data:', error);
    });
}

const handleAdd = async () => {
  const insertForm = {
    s_userid: newUser.value.id,
    s_userpass: newUser.value.password,
    s_username: newUser.value.name,
    s_usermail: newUser.value.mail
  };

  if (!insertForm.s_userid || !insertForm.s_userpass || !insertForm.s_username || !insertForm.s_usermail) {
    alert('모든 필드를 입력해주세요.');
    return;
  }

  try {
    const response = await axios.post('/api/user_insert', insertForm);
    alert(response.data);

    newUser.value = { id: '', password: '', name: '', mail: '' };
    selectedUsers.value = [];
    handleSearch();
  } catch (error) {
    console.error('Error adding user:', error);
    alert('사용자 추가 실패');
  }
};

const handleDelete = async () => {
  if (!selectedUsers.value || selectedUsers.value.length === 0) {
    alert('삭제할 사용자를 선택해주세요.');
    return;
  }

  const adminIncluded = selectedUsers.value.some(user => user.userid === 'admin');
  if (adminIncluded) {
    alert('admin 계정은 삭제할 수 없습니다.');
    return;
  }

  const confirmDelete = confirm(`${selectedUsers.value.length}명의 사용자를 삭제하시겠습니까?`);
  if (!confirmDelete) return;

  try {
    const userIds = selectedUsers.value.map(user => user.userid);
    const response = await axios.post('/api/user_delete', { s_userids: userIds });
    alert(response.data);
    newUser.value = { id: '', password: '', name: '', mail: '' };
    selectedUsers.value = [];
    handleSearch();
  } catch (error) {
    console.error('Error deleting users:', error);
    alert('사용자 삭제 실패');
  }
};

const handleReset = () => {
  newUser.value = { id: '', password: '', name: '', mail: '' };
  selectedUsers.value = [];
  if (gridApi.value) {
    gridApi.value.deselectAll();
  }
  alert('입력 필드와 선택된 행이 초기화되었습니다.');
}

const onGridReady = (params) => {
  gridApi.value = params.api;
}

onMounted(() => {
  handleSearch();
});

const onDetailClose = () => {
  isDetailPopupOpen.value = false
  handleSearch()  // 팝업 닫히면 유저 검색 다시 실행
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
.insert-button:hover,
.action-button.reset:hover {
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
  background-color: #007bff;
  /* 기본 파란색 */
  transition: background-color 0.3s ease;
}

.action-button:hover:enabled {
  background-color: #0056b3;
  /* 진한 파란색 */
}

.action-button:disabled {
  background-color: #cccccc;
  /* 회색 */
  cursor: not-allowed;
  color: #666666;
  /* 비활성화 텍스트 색상도 약간 어둡게 */
}

/* 기존 색상 분리했던 부분 수정 */
.action-button.delete {
  background-color: #dc3545;
}

.action-button.delete:hover:enabled {
  background-color: #a71d2a;
}

.action-button.reset {
  background-color: #00746e;
}

.action-button.reset:hover:enabled {
  background-color: #004547;
}

.action-button:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}

.ag-theme-alpine {
  border-radius: 5px;
  overflow: hidden;
}
</style>
