<template>
  <div 
    class="h-full flex flex-col p-4 bg-gradient-to-br from-indigo-50/50 to-purple-50/50 dark:from-indigo-950/20 dark:to-purple-950/20 rounded-lg"
    :class="{ 'cursor-pointer hover:shadow-lg transition-all': isEditMode }"
    @click="isEditMode ? $emit('configure') : undefined"
  >
    <!-- Widget Header -->
    <div class="flex items-center justify-between mb-4 flex-shrink-0" @click.stop>
      <div class="flex items-center space-x-2">
        <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
          <Info class="w-5 h-5 text-white" />
        </div>
        <h3 class="text-base font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
          Report Summary
        </h3>
      </div>
      <Button
        v-if="isEditMode"
        @click.stop="$emit('remove')"
        variant="ghost"
        size="sm"
        class="text-destructive hover:text-destructive h-7 w-7 p-0"
        title="Remove widget"
      >
        <X class="w-4 h-4" />
      </Button>
    </div>

    <!-- Info Display - Revolut Style -->
    <div class="flex-1 space-y-2.5 overflow-auto">
      <!-- Date Range -->
      <div class="bg-white/80 dark:bg-gray-900/40 backdrop-blur-sm rounded-xl p-3 border border-indigo-200/50 dark:border-indigo-800/30 shadow-sm">
        <div class="flex items-center justify-between">
          <div class="flex items-center space-x-2">
            <Calendar class="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
            <span class="text-xs font-medium text-muted-foreground">Date Range</span>
          </div>
          <div class="text-sm font-bold text-foreground">
            {{ formatDateRange() }}
          </div>
        </div>
      </div>

      <!-- Fields Used -->
      <div class="bg-white/80 dark:bg-gray-900/40 backdrop-blur-sm rounded-xl p-3 border border-purple-200/50 dark:border-purple-800/30 shadow-sm">
        <div class="flex items-center space-x-2 mb-2">
          <Layers class="w-4 h-4 text-purple-600 dark:text-purple-400" />
          <span class="text-xs font-medium text-muted-foreground">Fields Used</span>
        </div>
        <div class="flex flex-wrap gap-1">
          <!-- Computed fields (green pills) -->
          <span 
            v-for="field in computedFields" 
            :key="field"
            class="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800"
          >
            {{ field }}
          </span>
          <!-- Ingested fields (yellow pills) -->
          <span 
            v-for="field in ingestedFields" 
            :key="field"
            class="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-800"
          >
            {{ field }}
          </span>
        </div>
      </div>

      <!-- Performance Metrics -->
      <div class="bg-white/80 dark:bg-gray-900/40 backdrop-blur-sm rounded-xl p-3 border border-blue-200/50 dark:border-blue-800/30 shadow-sm">
        <div class="space-y-1.5">
          <div class="flex items-center justify-between text-xs">
            <span class="text-muted-foreground">Report Generated</span>
            <span class="font-bold text-foreground">{{ formatFullTimestamp(Date.now()) }}</span>
          </div>
          <div class="flex items-center justify-between text-xs">
            <span class="text-muted-foreground">Load Time</span>
            <span class="font-bold text-foreground">{{ formatDuration(reportMetrics.loadTime) }}</span>
          </div>
          <div class="flex items-center justify-between text-xs">
            <span class="text-muted-foreground">Last Data Refresh</span>
            <span class="font-bold text-foreground">
              {{ reportMetrics.lastRefresh ? formatTimestamp(reportMetrics.lastRefresh) : 'Not refreshed yet' }}
            </span>
          </div>
          <div class="flex items-center justify-between text-xs">
            <span class="text-muted-foreground">API Calls</span>
            <span class="font-bold text-foreground">{{ reportMetrics.apiCallCount }}</span>
          </div>
          <div class="flex items-center justify-between text-xs">
            <span class="text-muted-foreground">Widgets</span>
            <span class="font-bold text-foreground">{{ widgetCount }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { X, Info, Calendar, Database, Layers } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'

const props = defineProps({
  isEditMode: {
    type: Boolean,
    default: false
  },
  reportMetrics: {
    type: Object,
    default: () => ({
      loadTime: 0,
      lastRefresh: null,
      apiCallCount: 0
    })
  },
  widgetCount: {
    type: Number,
    default: 0
  },
  dateRange: {
    type: Object,
    default: () => ({ from: null, to: null, dateField: 'date' })
  },
  transactionCount: {
    type: Number,
    default: null
  },
  metadata: {
    type: Object,
    default: () => ({ ingested_columns: {}, computed_columns: {} })
  }
})

defineEmits(['remove', 'configure'])

// Extract computed fields (green pills)
const computedFields = computed(() => {
  if (!props.metadata.computed_columns) return []
  return Object.keys(props.metadata.computed_columns)
})

// Extract ingested fields (yellow pills)
const ingestedFields = computed(() => {
  if (!props.metadata.ingested_columns) return []
  return Object.keys(props.metadata.ingested_columns)
})

const formatDateRange = () => {
  if (!props.dateRange.from || !props.dateRange.to) {
    return 'All time'
  }
  // Parse date strings manually to avoid timezone issues
  // Date strings are in format "YYYY-MM-DD"
  const parseLocalDate = (dateStr) => {
    const [year, month, day] = dateStr.split('-').map(Number)
    return new Date(year, month - 1, day) // month is 0-indexed
  }
  
  const from = parseLocalDate(props.dateRange.from).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
  const to = parseLocalDate(props.dateRange.to).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
  return `${from} - ${to}`
}

const formatDuration = (ms) => {
  if (!ms || ms === 0) return '0ms'
  if (ms < 1000) return `${Math.round(ms)}ms`
  return `${(ms / 1000).toFixed(2)}s`
}

const formatTimestamp = (timestamp) => {
  if (!timestamp) return 'Never'
  const date = new Date(timestamp)
  const now = new Date()
  const diffMs = now - date
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins} min${diffMins > 1 ? 's' : ''} ago`
  if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`
  if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`
  
  return date.toLocaleDateString() + ' ' + date.toLocaleTimeString()
}

const formatFullTimestamp = (timestamp) => {
  const date = new Date(timestamp)
  return date.toLocaleString('en-US', { 
    month: 'short', 
    day: 'numeric', 
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    hour12: true 
  })
}
</script>

