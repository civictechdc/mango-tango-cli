<script lang="ts">
import { defineComponent } from 'vue';

export default defineComponent({
  props: {
    text: String
  },
  methods: {
    handleButtonClick(): void {
      this.$refs.filePicker.click();
    }
  },
});
</script>
<template>
  <div class="flex flex-col justify-center items-center">
    <button type="button" @click="handleButtonClick">{{ text }}</button>
    <input type="file" ref="filePicker" class="hidden" />
  </div>
</template>
