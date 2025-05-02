<template>
  <div style="background-color: gainsboro; padding: 20px; height: 100%;">
    <button @click="selectMenu('menu1')">메뉴 1</button>
    <button @click="selectMenu('menu2')">메뉴 2</button>
    <button @click="selectMenu('menu3')">메뉴 3</button>
  </div>
</template>

<script>
export default {
  methods: {
    selectMenu(menuName) {
      this.$emit('change-view', menuName);
    },
  },
};
</script>

<style scoped>
button {
  display: block;
  width: 100%;
  margin-top: 15px;
  padding: 5px 10px;
  font-size: 18px;
  font-weight: bold;
  cursor: pointer;
  border: none;
  border-radius: 8px;
  background-color: #ffffff;
  transition: background-color 0.3s;
}
button:hover {
  background-color: #e6ffe6;
}
</style>
