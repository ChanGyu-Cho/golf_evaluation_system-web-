<template><div class="modal-overlay g-section" @click.self="closePopup">
    <div class="modal-content">
      <h3>사용자 상세 정보</h3>
      <div v-if="props.user">
        <label>
          <strong>ID:</strong>
          <input type="text" :value="props.user.userid" disabled />
        </label>
        <label>
          <strong>비밀번호:</strong>
          <input type="text" v-model="editableUser.userpass" @input="checkModified" />
        </label>
        <label>
          <strong>이름:</strong>
          <input type="text" v-model="editableUser.username" @input="checkModified" />
        </label>
        <label>
          <strong>이메일:</strong>
          <input type="email" v-model="editableUser.usermail" @input="checkModified" />
        </label>
      </div>
      <button :disabled="!isModified" @click="handleEdit" class="edit-button">수정</button>
      <button @click="closePopup" class="close-button">닫기</button>
    </div>
  </div>
</template>

<script setup>
import { reactive, toRaw } from 'vue'
import { defineProps, defineEmits } from 'vue'
import { ref } from 'vue'
import axios from 'axios'

const props = defineProps({
  user: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['close', 'updated'])

const editableUser = reactive({
  userpass: props.user.userpass,
  username: props.user.username,
  usermail: props.user.usermail
})

let originalUser = { ...props.user }

const isModified = ref(false)

const checkModified = () => {
  isModified.value =
    editableUser.userpass !== originalUser.userpass ||
    editableUser.username !== originalUser.username ||
    editableUser.usermail !== originalUser.usermail
}

const handleEdit = async () => {
  try {
    const editForm = {
      s_userid: props.user.userid,
      s_userpass: editableUser.userpass,
      s_username: editableUser.username,
      s_usermail: editableUser.usermail
    }
    const response = await axios.post('/api/user_edit', editForm)
    alert(response.data)
    // 수정 성공시 원본 값 업데이트 및 버튼 비활성화
    originalUser = { ...toRaw(editableUser), userid: props.user.userid }
    isModified.value = false
    emit('updated') // 부모 컴포넌트에게 업데이트 알림
  } catch (error) {
    console.error('Error editing user:', error)
    alert('사용자 수정 실패')
  }
}

const closePopup = () => {
  emit('close')
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 999;
}

.modal-content {
  background: white;
  padding: 20px 30px;
  border-radius: 8px;
  width: 320px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.3);
  display: flex;
  flex-direction: column;
  gap: 10px;
}

label {
  display: flex;
  flex-direction: column;
  font-weight: 600;
}

input {
  margin-top: 5px;
  padding: 6px;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 14px;
}

.edit-button {
  margin-top: 10px;
  padding: 10px 15px;
  background-color: #28a745;
  border: none;
  border-radius: 5px;
  color: white;
  cursor: pointer;
  font-weight: bold;
}

.edit-button:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}

.close-button {
  margin-top: 10px;
  padding: 10px 15px;
  background-color: #007bff;
  border: none;
  border-radius: 5px;
  color: white;
  cursor: pointer;
  font-weight: bold;
}

.close-button:hover {
  background-color: #0056b3;
}
</style>
