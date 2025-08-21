import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '../views/LoginView.vue'

// Helper: wrap dynamic imports so we log when a module resolves to undefined/default missing
function safeImport(fn, name) {
  return async () => {
    try {
      const mod = await fn()
      const comp = mod && (mod.default || mod)
      if (!comp) {
        console.error(`[safeImport] component missing for ${name}`, mod)
        throw new Error(`Component ${name} resolved to undefined`)
      }
      return comp
    } catch (err) {
      console.error(`[safeImport] dynamic import failed for ${name}:`, err)
      throw err
    }
  }
}

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
  component: safeImport(() => import(/* webpackChunkName: "about" */ '../views/MainView.vue'), 'MainView')
  },
  {
    path: '/menu1',
    name: 'menu1',
  component: safeImport(() => import(/* webpackChunkName: "about" */ '@/components/id_manage.vue'), 'id_manage')
  },
  {
    path: '/menu2',
    name: 'menu2',
  component: safeImport(() => import(/* webpackChunkName: "about" */ '@/components/video_upload.vue'), 'video_upload')
  },
  {
    path: '/menu3',
    name: 'menu3',
  component: safeImport(() => import(/* webpackChunkName: "about" */ '@/components/upload_history.vue'), 'upload_history')
  },
  {
    path: '/menu4',
    name: 'menu4',
  component: safeImport(() => import(/* webpackChunkName: "about" */ '@/components/user_info.vue'), 'user_info')
  },
  {
    path: '/videoplay',
    name: 'VideoplayView',
  component: safeImport(() => import('@/views/VideoplayView.vue'), 'VideoplayView')
  },
  {
    path: '/videoresult',
    name: 'VideoresultView',
  component: safeImport(() => import('@/views/VideoresultView.vue'), 'VideoresultView')
  },
  {
    path: '/signup',
    name: 'SignupView',
  component: safeImport(() => import('@/views/SignupView.vue'), 'SignupView')
  }
  ]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
})

export default router
