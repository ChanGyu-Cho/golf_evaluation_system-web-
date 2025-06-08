import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '../views/LoginView.vue'

const routes = [
  {
    path: '/',
    name: 'login',
    component: LoginView  // 기본이 loginView
  },
  {
    path: '/main',
    name: 'main',
    // route level code-splitting
    // this generates a separate chunk (about.[hash].js) for this route
    // which is lazy-loaded when the route is visited.
    component: () => import(/* webpackChunkName: "about" */ '../views/MainView.vue')
  },
  {
    path: '/menu1',
    name: 'menu1',
    component: () => import(/* webpackChunkName: "about" */ '@/components/id_manage.vue')
  },
  {
    path: '/menu2',
    name: 'menu2',
    component: () => import(/* webpackChunkName: "about" */ '@/components/video_upload.vue')
  },
  {
    path: '/menu3',
    name: 'menu3',
    component: () => import(/* webpackChunkName: "about" */ '@/components/upload_history.vue')
  },
  {
    path: '/videoplay',
    name: 'VideoplayView',
    component: () => import('@/views/VideoplayView.vue')
  },
  {
    path: '/videoresult',
    name: 'VideoresultView',
    component: () => import('@/views/VideoresultView.vue')
  }
  ]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
})

export default router
