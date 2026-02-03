<script setup lang="ts">
import { ref, computed } from 'vue';

type ButtonProps = {
  icon?: string;
  color: string;
};
type UploadProps = ButtonProps & {
  text?: string;
};
type EmitProps = {
  click: [value: string];
  change: [path: string | null];
};

const props = defineProps<UploadProps>();
const filePickerRef = ref<HTMLInputElement | null>(null);
const emit = defineEmits<EmitProps>();
const displayText = computed<string>((): string => props.text && props.text.length > 0 ? props.text : 'Click Me');
const buttonProps = computed<ButtonProps>((): ButtonProps => {
  let propsCopy: UploadProps = { ...props };

  delete propsCopy.text;
  if (propsCopy.icon == null) delete propsCopy.icon;

  return propsCopy as ButtonProps;
});
const handleButtonClick = (): void => {
  filePickerRef.value?.click();
  emit('click', 'test...');
};
const handleFilePickerChange = (event: Event): void => {
  const target = event.target as HTMLInputElement;

  if (target.type !== 'file') return;
  if (target.files == null || target.files.length === 0) {
    emit('change', null);
    return;
  }
  if (target.files.length > 1) return;

  console.log(target.files[0]);
  emit('change', target.files[0]?.webkitRelativePath as string);
};
</script>
<template>
  <div class="flex flex-col justify-center items-center">
    <q-btn v-bind="buttonProps" @click="handleButtonClick">
      <span class="ml-1">{{ displayText }}</span>
    </q-btn>
    <input type="file" ref="filePickerRef" class="hidden" @change="handleFilePickerChange" />
  </div>
</template>
