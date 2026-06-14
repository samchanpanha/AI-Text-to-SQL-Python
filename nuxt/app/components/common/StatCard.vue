<template>
  <div class="stat-card-inner">
    <div class="stat-card-icon" :style="{ background: color + '15', color }">
      <component :is="iconComponent" />
    </div>
    <div class="stat-card-body">
      <div class="stat-card-label">{{ title }}</div>
      <div class="stat-card-value" :style="{ color }">{{ value }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  TeamOutlined, ScheduleOutlined, ApiOutlined, ThunderboltOutlined,
  CloseCircleOutlined, ClockCircleOutlined,
} from '@ant-design/icons-vue'

const props = defineProps<{
  title: string
  value: string | number
  color: string
  icon: string
}>()

const iconMap: Record<string, any> = {
  TeamOutlined, ScheduleOutlined, ApiOutlined,
  ThunderboltOutlined, CloseCircleOutlined, ClockCircleOutlined,
}

const iconComponent = computed(() => iconMap[props.icon])
</script>

<style scoped>
.stat-card-inner {
  display: flex;
  align-items: center;
  gap: 16px;
}
.stat-card-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  flex-shrink: 0;
}
.stat-card-body {
  flex: 1;
  min-width: 0;
}
.stat-card-label {
  font-size: 13px;
  color: #999;
  margin-bottom: 4px;
}
.stat-card-value {
  font-size: 22px;
  font-weight: 600;
  line-height: 1.2;
}
</style>
