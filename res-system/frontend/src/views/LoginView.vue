<template>
  <div class="g-section">
    <div class="form-container">
      <img src="../assets/골프_백경이.png" alt="로그인 이미지" class="login-image">
      <div class="title">SwingMate</div>
      <div class="subtitle">골프 스윙 평가&분석</div>

      <form @submit.prevent="loginAct" class="login-form">
        <div>
          <label for="userid">아이디</label>
          <input type="text" id="userid" name="userid" placeholder="아이디를 입력하세요" v-model="userId" />
        </div>
        <div style="margin-top: 10px;">
          <label for="userpass">비밀번호</label>
          <input type="password" id="userpass" name="userpass" placeholder="비밀번호를 입력하세요" v-model="userPassword" />
        </div>
        <button type="submit" class="login-button">로그인</button>
      </form>

      <button class="signup-button" @click="showSignup = true">회원가입</button>
      <SignupView v-if="showSignup" @close="showSignup = false" />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import axios from 'axios';
import SignupView from './SignupView.vue';
import { useRouter } from 'vue-router';
import { useStore } from 'vuex';

const router = useRouter();
const store = useStore();

const userId = ref('');
const userPassword = ref('');
const showSignup = ref(false);

const loginAct = () => {
  console.log('아이디:', userId.value);
  console.log('비밀번호:', userPassword.value);

  const loginForm = {
    s_userid: userId.value,
    s_userpass: userPassword.value
  };

  axios
    .post('/api/login5', loginForm)
    .then((res) => {
      console.log("postgood", res.data);
      if (res.data && res.data.username) {
        store.commit('setLocalName', res.data.username);
        store.commit('setSessionName', res.data.username);
        store.commit('setUserId1', res.data.userid);
        store.commit('setUserId2', res.data.userid);

        alert(`안녕하세요 ${res.data.username} 님!. userid1: ${res.data.userid} 님!. `);

        router.push({ path: "/main" });
      } else {
        alert("id, 비밀번호를 정확히 입력해주세요.");
      }
    })
    .catch((error) => {
      console.error('Error during login:', error);
    });
};
</script>

<style scoped>
.g-section {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-image: url('../assets/golf_background.png');
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  padding: 20px;
}

.form-container {
  background: rgba(255, 255, 255, 0.8); /* 반투명 흰색 */
  padding: 30px;
  border-radius: 12px;
  box-shadow: 0 8px 16px rgba(0,0,0,0.3);
  display: flex;
  flex-direction: column;
  align-items: center;
  backdrop-filter: blur(8px); /* 블러 효과 */
}

.login-image {
  margin-bottom: 10px;
  max-width: 300px;
}

.title {
  font-size: 28px;
  font-weight: bold;
  color: #222;
  margin-bottom: 20px;
}

.subtitle {
  font-size: 18px;
  color: #444;
  margin-bottom: 15px;
}

.login-form {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
}

label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
  color: #222;
}

input[type="text"],
input[type="password"] {
  padding: 10px;
  border: 1px solid #aaa;
  border-radius: 6px;
  width: 280px;
  box-sizing: border-box;
  margin-bottom: 10px;
}

.login-button {
  margin-top: 20px;
  padding: 12px 24px;
  background-color: #28a745; /* 골프 잔디 색 */
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 16px;
}

.login-button:hover {
  background-color: #218838;
}

.signup-button {
  margin-top: 12px;
  padding: 10px 24px;
  background-color: #ffc107; /* 옐로우 계열로 강조 */
  color: #222;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 16px;
}

.signup-button:hover {
  background-color: #e0a800;
}
</style>
