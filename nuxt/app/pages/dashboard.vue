<template>
  <div class="dashboard">
    <div class="dashboard-stats">
      <a-row :gutter="[16, 16]">
        <a-col :xs="12" :sm="8" :lg="4">
          <a-card class="stat-card" :loading="loading">
            <stat-card title="Total Users" :value="stats?.users.total ?? 0" color="#1890ff" icon="TeamOutlined" />
          </a-card>
        </a-col>
        <a-col :xs="12" :sm="8" :lg="4">
          <a-card class="stat-card" :loading="loading">
            <stat-card title="Active Tasks" :value="stats?.tasks.active ?? 0" color="#52c41a" icon="ScheduleOutlined" />
          </a-card>
        </a-col>
        <a-col :xs="12" :sm="8" :lg="4">
          <a-card class="stat-card" :loading="loading">
            <stat-card title="API Requests" :value="stats?.api.requests ?? 0" color="#722ed1" icon="ApiOutlined" />
          </a-card>
        </a-col>
        <a-col :xs="12" :sm="8" :lg="4">
          <a-card class="stat-card" :loading="loading">
            <stat-card title="LLM Calls" :value="stats?.llm.total_calls ?? 0" color="#fa8c16" icon="ThunderboltOutlined" />
          </a-card>
        </a-col>
        <a-col :xs="12" :sm="8" :lg="4">
          <a-card class="stat-card" :loading="loading">
            <stat-card title="Errors" :value="stats?.api.errors_5xx ?? 0" color="#ff4d4f" icon="CloseCircleOutlined" />
          </a-card>
        </a-col>
        <a-col :xs="12" :sm="8" :lg="4">
          <a-card class="stat-card" :loading="loading">
            <stat-card title="Avg Duration" :value="`${(stats?.api.avg_duration_ms ?? 0).toFixed(0)}ms`" color="#13c2c2" icon="ClockCircleOutlined" />
          </a-card>
        </a-col>
      </a-row>
    </div>

    <a-row :gutter="[16, 16]" class="dashboard-charts">
      <a-col :span="24" :lg="12">
        <a-card title="LLM Usage (7 days)" :loading="loading">
          <div style="height: 300px">
            <v-chart v-if="llmStats" :option="chartOptions.llmUsage" autoresize />
          </div>
        </a-card>
      </a-col>
      <a-col :span="24" :lg="12">
        <a-card title="Top Paths" :loading="loading">
          <div style="height: 300px">
            <v-chart v-if="auditStats" :option="chartOptions.topPaths" autoresize />
          </div>
        </a-card>
      </a-col>
    </a-row>

    <a-row :gutter="[16, 16]" class="dashboard-errors">
      <a-col :span="24">
        <a-card title="Recent Errors" :loading="loading">
          <a-table
            :dataSource="recentErrors"
            :columns="errorColumns"
            :pagination="false"
            size="small"
            :locale="{ emptyText: 'No errors' }"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'status_code'">
                <a-tag :color="record.status_code >= 500 ? 'red' : 'orange'">{{ record.status_code }}</a-tag>
              </template>
            </template>
          </a-table>
        </a-card>
      </a-col>
    </a-row>
  </div>
</template>

<script setup lang="ts">
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart, LineChart, PieChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import { TeamOutlined, ScheduleOutlined, ApiOutlined, ThunderboltOutlined, CloseCircleOutlined, ClockCircleOutlined } from '@ant-design/icons-vue'
import type { DashboardStats, AuditStats, LlmStats, AuditLog } from '~/types/api'

use([CanvasRenderer, BarChart, LineChart, PieChart, GridComponent, TooltipComponent, LegendComponent])

definePageMeta({ middleware: 'auth' })

const config = useRuntimeConfig()
const apiBase = config.public.apiBaseUrl
const authStore = useAuthStore()
const headers = { Authorization: `Bearer ${authStore.token}` }

const loading = ref(true)
const stats = ref<DashboardStats | null>(null)
const auditStats = ref<AuditStats | null>(null)
const llmStats = ref<LlmStats | null>(null)
const recentErrors = ref<AuditLog[]>([])

const errorColumns = [
  { title: 'Time', dataIndex: 'timestamp', key: 'timestamp', width: 180 },
  { title: 'Method', dataIndex: 'method', key: 'method', width: 80 },
  { title: 'Path', dataIndex: 'path', key: 'path' },
  { title: 'Status', dataIndex: 'status_code', key: 'status_code', width: 80 },
  { title: 'Duration', dataIndex: 'duration_ms', key: 'duration_ms', width: 100 },
]

const chartOptions = computed(() => ({
  llmUsage: llmStats.value ? {
    tooltip: { trigger: 'axis' },
    legend: { data: ['Calls', 'Cost ($)'] },
    xAxis: { type: 'category', data: llmStats.value.models.map((m: any) => m.model) },
    yAxis: [{ type: 'value', name: 'Calls' }, { type: 'value', name: 'Cost ($)' }],
    series: [
      { name: 'Calls', type: 'bar', data: llmStats.value.models.map((m: any) => m.calls), itemStyle: { color: '#1890ff' } },
      { name: 'Cost ($)', type: 'line', yAxisIndex: 1, data: llmStats.value.models.map((m: any) => m.estimated_cost_usd), itemStyle: { color: '#52c41a' } },
    ],
  } : {},
  topPaths: auditStats.value ? {
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: auditStats.value.top_paths.map((p: any) => p.path) },
    yAxis: { type: 'value' },
    series: [{ type: 'bar', data: auditStats.value.top_paths.map((p: any) => p.count), itemStyle: { color: '#722ed1' } }],
  } : {},
}))

async function fetchAll() {
  loading.value = true
  try {
    const [s, ae, ll, errs] = await Promise.all([
      $fetch('/api/admin/dashboard?days=7', { baseURL: apiBase, headers }),
      $fetch('/api/logs/audit/stats?days=7', { baseURL: apiBase, headers }),
      $fetch('/api/logs/llm/stats?days=7', { baseURL: apiBase, headers }),
      $fetch('/api/admin/errors/recent?limit=10', { baseURL: apiBase, headers }),
    ])
    stats.value = s as DashboardStats
    auditStats.value = ae as AuditStats
    llmStats.value = ll as LlmStats
    recentErrors.value = errs as AuditLog[]
  } catch (e) {
    console.error('Failed to load dashboard data:', e)
  } finally {
    loading.value = false
  }
}

onMounted(fetchAll)
</script>

<style scoped>
.dashboard {
  max-width: 1400px;
}
.dashboard-stats {
  margin-bottom: 16px;
}
.stat-card {
  cursor: default;
}
.dashboard-charts {
  margin-bottom: 16px;
}
</style>
