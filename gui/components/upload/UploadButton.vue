<script setup lang="ts">
import { ref, computed } from 'vue';

type ButtonProps = {
  icon?: string;
  color: string;
};
type UploadProps = ButtonProps & {
  text?: string;
};
const props = defineProps<UploadProps>();
const filePickerRef = ref<HTMLInputElement | null>(null);
const displayText = computed<string>((): string => props.text && props.text.length > 0 ? props.text : 'Click Me');
const buttonProps = computed<ButtonProps>((): ButtonProps => {
  let propsCopy: UploadProps = { ...props };

  delete propsCopy.text;
  if (propsCopy.icon == null) delete propsCopy.icon;

  return propsCopy as ButtonProps;
});

function handleButtonClick(): void {
  filePickerRef.value?.click();
}
</script>
<template>
  <div class="flex flex-col justify-center items-center">
    <q-btn v-bind="buttonProps" @click="handleButtonClick">
      <span class="ml-1">{{ displayText }}</span>
    </q-btn>
    <input type="file" ref="filePickerRef" class="hidden" />
  </div>
</template>
