<script setup lang="ts">
import { ref, computed } from "vue";

type ButtonProps = {
  icon?: string;
  color: string;
};
type UploadProps = ButtonProps & {
  text?: string;
  url: string;
};
type SubmitResponse = {
  message?: string;
  href?: string;
};

const props = defineProps<UploadProps>();
const filePickerRef = ref<HTMLInputElement | null>(null);
const displayText = computed<string>((): string =>
  props.text && props.text.length > 0 ? props.text : "Click Me",
);
const buttonProps = computed<ButtonProps>((): ButtonProps => {
  let propsCopy: UploadProps = { ...props };

  delete propsCopy.text;
  if (propsCopy.icon == null) delete propsCopy.icon;

  return propsCopy as ButtonProps;
});
const handleButtonClick = (): void => filePickerRef.value?.click();
const handleFilePickerChange = (event: Event): void => {
  const target = event.target as HTMLInputElement;

  if (target.type !== "file") return;
  if (
    target.files == null ||
    target.files.length === 0 ||
    target.files.length > 1
  )
    return;

  const formData = new FormData();

  formData.append("file", target.files[0] as File);
  (async (): Promise<void> => {
    try {
      const response: Response = await fetch(props.url, {
        method: "POST",
        body: formData,
      });
      const respData = (await response.json()) as SubmitResponse;

      if (response.status !== 200) throw respData;

      window.location.href = respData.href as string;
    } catch (err: any) {
      console.error(err);
    }
  })();
};
</script>
<template>
  <q-btn v-bind="buttonProps" @click="handleButtonClick">
    <span class="ml-1">{{ displayText }}</span>
    <input
      type="file"
      ref="filePickerRef"
      class="hidden"
      @change="handleFilePickerChange"
    />
  </q-btn>
</template>
