<template>
  <div style="display: flex; flex-direction: column; align-items: center;">
    <img src="../assets/자료조사.png" alt="로그인 이미지" style="margin-bottom: 20px; max-width: 150px;">
    <div>
      <label for="userid">아이디</label>
      <input type="text" id="userid" name="userid" placeholder="아이디를 입력하세요" v-model="userId">
    </div>
    <div style="margin-top: 10px;">
      <label for="userpass">비밀번호</label>
      <input type="password" id="userpass" name="userpass" placeholder="비밀번호를 입력하세요" v-model="userPassword">
    </div>
    <button style="margin-top: 20px; padding: 10px 20px;" @click="loginAct">로그인</button>
  </div>
</template>

 <!-- sertup을 script에 적었기에, return이 필요 없음-->
 <script setup>
 import { ref } from 'vue';
 import axios from 'axios'; // axios를 import합니다.

  import { useRouter } from 'vue-router'; // vue-router에서 useRouter를 import합니다.
  import { useStore } from 'vuex';  // script setup 구조에서는 store를 사용하기 위해 import합니다.

  const router = useRouter(); // useRouter를 사용하여 라우터 인스턴스를 가져옵니다.
  const store = useStore();
 
 const userId = ref('');
 const userPassword = ref('');
 
 const loginAct = () => {
   // 로그인 처리 로직 (예: API 호출)
   // 로그인 정보가 브라우저의 콘솔에 표시(f12 개발자 도구에서 확인 가능)
   console.log('아이디:', userId.value);
   console.log('비밀번호:', userPassword.value);

 
   // 폼 바구니 생성
   const loginForm={
     s_userid: userId.value,
     s_userpass: userPassword.value
   };
 
   axios
   .post('/api/login5', loginForm) // post로 바꿈
   .then((res) => {  // 서버에 가서 login5가 있어서 작업을 잘 하면 console에 찍힘
     console.log("postgood", res.data);
     if (res.data && res.data.username) {
     // 로그인 성공한 경우

     // store에 이름 저장
     store.commit('setName', res.data.username); // store.commit을 사용해 mutation 호출

     alert(`안녕하세요 ${res.data.username} 님!`);

     router.push({path : "/main"}); // 로그인 성공 후 메인 페이지로 이동
       
     }else{
       alert("post로그인 안된듯")
     }
   })
   .catch((error) => {
     console.error('Error during login:', error);
   });  
 };
 </script>

<style scoped>
label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
}

input[type="text"],
input[type="password"] {
  padding: 8px;
  border: 1px solid #ccc;
  border-radius: 4px;
  width: 300px;
  box-sizing: border-box;
}

button {
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
}

button:hover {
  background-color: #0056b3;
}
</style>