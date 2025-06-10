<template>
  <div class="user-edit-container" v-if="user">
    <h2>내 정보 편집</h2>

    <div class="form-group">
      <label>ID</label>
      <input type="text" :value="user.userid" disabled />
    </div>

    <div class="form-group">
      <label>비밀번호</label>
      <input type="password" v-model="editableUser.userpass" @input="checkModified" />
    </div>

    <div class="form-group">
      <label>이름</label>
      <input type="text" v-model="editableUser.username" @input="checkModified" />
    </div>

    <div class="form-group">
      <label>이메일</label>
      <input type="email" v-model="editableUser.usermail" @input="checkModified" />
    </div>

    <div class="buttons">
      <button :disabled="!isModified" @click="handleEdit" class="btn-save">수정</button>
      <button @click="cancelEdit" class="btn-cancel">취소</button>
    </div>
  </div>

  <div v-else class="loading-message">
    로그인된 사용자 정보를 불러오는 중입니다...
  </div>
</template>

<script setup>
import { reactive, ref, onMounted, toRaw, computed } from 'vue'
import { useStore } from 'vuex'
import axios from 'axios'

const store = useStore()
const store_userid1 = computed(() => store.state.store_userid1)

const user = ref(null)  // 현재 보여줄 사용자 정보
const editableUser = reactive({
  userpass: '',
  username: '',
  usermail: ''
})
const isModified = ref(false)
const rowData = ref([]) // 사용자 검색 결과 저장 (필요하면)

const checkModified = () => {
  if (!user.value) return
  isModified.value =
    editableUser.userpass !== user.value.userpass ||
    editableUser.username !== user.value.username ||
    editableUser.usermail !== user.value.usermail
}

// 백엔드에서 로그인된 사용자 id로 사용자 정보 검색하는 함수
const handleSearch = () => {
  const userId = store_userid1.value
  if (!userId) {
    alert('로그인 정보가 없습니다.')
    return
  }

  axios.post('/api/id_search', { s_userid: userId })
    .then(response => {
      if (Array.isArray(response.data) && response.data.length > 0) {
        // 결과가 배열이라면 첫 번째 사용자 정보만 보여주도록 처리
        const foundUser = response.data[0]

        // rowData 업데이트 (필요하면)
        rowData.value = response.data

        // user와 editableUser에 세팅
        user.value = foundUser
        editableUser.userpass = foundUser.userpass
        editableUser.username = foundUser.username
        editableUser.usermail = foundUser.usermail

        isModified.value = false
      } else if (response.data.status === 'NOT' || response.data.length === 0) {
        alert('검색된 데이터가 없습니다.')
        rowData.value = []
        user.value = null
      } else {
        alert('알 수 없는 응답입니다.')
      }
    })
    .catch(error => {
      console.error('Error fetching data:', error)
      alert('사용자 정보를 불러오는 중 오류가 발생했습니다.')
    })
}

// handleSearch를 기존 fetchUserInfo 대신 호출
onMounted(() => {
  handleSearch()
})

const handleEdit = async () => {
  try {
    const editForm = {
      s_userid: user.value.userid,
      s_userpass: editableUser.userpass,
      s_username: editableUser.username,
      s_usermail: editableUser.usermail
    }
    const response = await axios.post('/api/user_edit', editForm)
    alert(response.data)
    user.value = { ...toRaw(editableUser), userid: user.value.userid }
    isModified.value = false
  } catch (error) {
    console.error(error)
    alert('수정 실패')
  }
}

const cancelEdit = () => {
  if (!user.value) return
  editableUser.userpass = user.value.userpass
  editableUser.username = user.value.username
  editableUser.usermail = user.value.usermail
  isModified.value = false
}
</script>

<style scoped>
.user-edit-container {
  max-width: 600px;
  margin: 20px auto;
  padding: 20px;
  border-radius: 8px;
  background-color: #f9fafb;
  box-shadow: 0 0 8px rgba(0,0,0,0.1);
  display: flex;
  flex-direction: column;
  gap: 15px;
}

h2 {
  text-align: center;
  margin-bottom: 20px;
  font-weight: 700;
}

.form-group {
  display: flex;
  flex-direction: column;
}

label {
  font-weight: 600;
  margin-bottom: 6px;
}

input[type="text"],
input[type="password"],
input[type="email"] {
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 5px;
  font-size: 16px;
}

input[disabled] {
  background-color: #e9ecef;
  color: #6c757d;
  cursor: not-allowed;
}

.buttons {
  display: flex;
  justify-content: center;
  gap: 15px;
  margin-top: 15px;
}

.btn-save {
  background-color: #28a745;
  color: white;
  border: none;
  border-radius: 6px;
  padding: 10px 20px;
  cursor: pointer;
  font-weight: 700;
  transition: background-color 0.3s ease;
}

.btn-save:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

.btn-save:hover:not(:disabled) {
  background-color: #218838;
}

.btn-cancel {
  background-color: #6c757d;
  color: white;
  border: none;
  border-radius: 6px;
  padding: 10px 20px;
  cursor: pointer;
  font-weight: 700;
}

.btn-cancel:hover {
  background-color: #5a6268;
}

.loading-message {
  text-align: center;
  color: #666;
  font-size: 16px;
  margin-top: 30px;
}
</style>
