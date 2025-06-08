import { createStore } from 'vuex'

function safeParse(storage, key) {
  try {
    const value = storage.getItem(key)
    return value ? JSON.parse(value) : ''
  } catch (e) {
    storage.removeItem(key)
    return ''
  }
}

export default createStore({
  state: {
    store_local_name: safeParse(localStorage, 'store_local_name'),
    store_session_name: safeParse(sessionStorage, 'store_session_name'),
    store_userid1: localStorage.getItem('userid1') || null,
    store_userid2: sessionStorage.getItem('userid2') || null

  },
  mutations: {
    setLocalName(state, payload) {
      state.store_local_name = payload
      localStorage.setItem('store_local_name', JSON.stringify(payload))
    },
    setSessionName(state, payload) {
      state.store_session_name = payload
      sessionStorage.setItem('store_session_name', JSON.stringify(payload))
    },
    setUserId1(state, payload) {
      state.store_userid1 = payload
      localStorage.setItem('userid1', payload)
    },
    setUserId2(state, payload) {
      state.store_userid2 = payload
      sessionStorage.setItem('userid2', payload)
    }
  },
  getters: {
    // 기존 getter 있으면 유지
  },
  actions: {
    // 기존 action 있으면 유지
  },
  modules: {
    // 기존 modules 있으면 유지
  }
})
