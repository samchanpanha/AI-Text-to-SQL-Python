<template>
  <div class="page-header">
    <div class="page-header-text">
      <h2>{{ title }}</h2>
      <p v-if="description">{{ description }}</p>
    </div>
    <div class="page-header-actions">
      <slot name="actions" />
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  title: string
  description?: string
}>()
</script>

<style scoped>
.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 16px;
  gap: 16px;
}
.page-header-text h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  line-height: 1.4;
}
.page-header-text p {
  margin: 4px 0 0;
  color: #999;
  font-size: 14px;
}
.page-header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
  margin-top: 4px;
}
</style>
