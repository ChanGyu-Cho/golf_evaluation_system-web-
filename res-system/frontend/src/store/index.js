import { createStore } from 'vuex'

export default createStore({
  state: {
    store_user_name :''
  },
  getters: {
  },
  mutations: {
    setName(state, payload) { // store_user_name에 setName으로 값을 넣어줌
      state.store_user_name = payload
    },
  },
  actions: {
  },
  modules: {
  }
})
