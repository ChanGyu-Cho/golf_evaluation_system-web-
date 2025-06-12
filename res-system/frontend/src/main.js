
import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import store from './store'
import './assets/theme.css';   //  ← 전역 테마 로드

createApp(App).use(store).use(router).mount('#app')
