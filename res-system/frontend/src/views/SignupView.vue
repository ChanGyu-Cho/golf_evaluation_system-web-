<template>
  <div class="modal-overlay">
    <div class="modal-content">
      <h2 class="modal-title">회원가입</h2>
      <input v-model="form.id" type="text" placeholder="아이디" class="modal-input" />
      <input v-model="form.password" type="password" placeholder="비밀번호" class="modal-input" />
      <input v-model="form.name" type="text" placeholder="이름" class="modal-input" />
      <input v-model="form.mail" type="email" placeholder="이메일" class="modal-input" />
      <div class="modal-actions">
        <button class="insert-button" @click="handleSubmit">등록</button>
        <button class="action-button reset" @click="$emit('close')">닫기</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, defineEmits } from 'vue'
import axios from 'axios'

const emit = defineEmits(['close'])
const form = ref({
  id: '',
  password: '',
  name: '',
  mail: ''
})

const handleSubmit = async () => {
  const insertForm = {
    s_userid: form.value.id,
    s_userpass: form.value.password,
    s_username: form.value.name,
    s_usermail: form.value.mail
  };

  if (!insertForm.s_userid || !insertForm.s_userpass || !insertForm.s_username || !insertForm.s_usermail) {
    alert('모든 필드를 입력해주세요.');
    return;
  }

  try {
    const response = await axios.post('/api/user_insert', insertForm);
    alert(response.data);
    emit('close');
  } catch (error) {
    console.error('Error adding user:', error);
    alert('사용자 추가 실패');
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 9999;
}

.modal-content {
  background-color: #fff;
  padding: 30px;
  border-radius: 10px;
  width: 400px;
  max-width: 90%;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.modal-title {
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 10px;
  text-align: center;
}

.modal-input {
  padding: 10px;
  font-size: 16px;
  border-radius: 5px;
  border: 1px solid #ccc;
  width: 100%;
  box-sizing: border-box;
}

.modal-actions {
  display: flex;
  justify-content: space-between;
  margin-top: 10px;
}

.insert-button {
  padding: 10px 20px;
  min-width: 70px;
  background-color: #28a745;
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-size: 16px;
}

.insert-button:hover {
  background-color: #218838;
}

.action-button.reset {
  background-color: #00746e;
  padding: 10px 20px;
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-size: 16px;
}

.action-button.reset:hover {
  background-color: #004547;
}
</style>