<template>
  <div 
    class="h-full flex flex-col p-4 bg-gradient-to-br from-blue-50/50 to-cyan-50/50 dark:from-blue-950/20 dark:to-cyan-950/20 rounded-lg"
    :class="{ 'cursor-pointer hover:shadow-lg transition-all': isEditMode }"
    @click="isEditMode ? $emit('configure') : undefined"
  >
    <!-- Widget Header -->
    <div class="flex items-center justify-between mb-4 flex-shrink-0" @click.stop>
      <div class="flex items-center space-x-2">
        <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-cyan-600 flex items-center justify-center">
          <Gauge class="w-5 h-5 text-white" />
        </div>
        <h3 class="text-base font-bold bg-gradient-to-r from-blue-600 to-cyan-600 bg-clip-text text-transparent">
          Performance Monitor
        </h3>
      </div>
      <div class="flex items-center space-x-1">
        <Button
          @click="refreshMetrics"
          variant="ghost"
          size="sm"
          class="h-7 w-7 p-0"
          title="Refresh metrics"
        >
          <RefreshCw :class="['w-4 h-4', { 'animate-spin': refreshing }]" />
        </Button>
        <Button
          v-if="isEditMode"
          @click="$emit('remove')"
          variant="ghost"
          size="sm"
          class="text-destructive hover:text-destructive h-7 w-7 p-0"
          title="Remove widget"
        >
          <X class="w-4 h-4" />
        </Button>
      </div>
    </div>

    <!-- Performance Display -->
    <div v-if="!memoryMetrics.available" class="flex-1 flex items-center justify-center text-muted-foreground text-sm">
      Performance API not available in this browser
    </div>
    <div v-else class="flex-1 space-y-2.5 overflow-auto">
      <!-- Performance Status -->
      <div :class="['bg-white/80 dark:bg-gray-900/40 backdrop-blur-sm rounded-xl p-3 border shadow-sm', getPerformanceBackgroundColor(performanceLevel)]">
        <div class="flex items-center justify-between">
          <span class="text-xs font-medium text-muted-foreground">Overall Status</span>
          <div :class="['text-sm font-bold', getPerformanceColor(performanceLevel)]">
            {{ getPerformanceLabel(performanceLevel) }}
          </div>
        </div>
      </div>

      <!-- Memory Usage -->
      <div class="bg-white/80 dark:bg-gray-900/40 backdrop-blur-sm rounded-xl p-3 border border-blue-200/50 dark:border-blue-800/30 shadow-sm">
        <div class="flex items-center justify-between mb-2">
          <span class="text-xs font-medium text-muted-foreground">JS Heap Memory</span>
          <div :class="['text-xs font-bold', getPerformanceColor(performanceLevel)]">
            {{ memoryMetrics.usedPercentage.toFixed(1) }}%
          </div>
        </div>
        <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 mb-2">
          <div 
            :class="['h-2 rounded-full transition-all', getPerformanceBgBar(performanceLevel)]"
            :style="{ width: memoryMetrics.usedPercentage + '%' }"
          ></div>
        </div>
        <div class="text-xs text-muted-foreground font-mono">
          {{ memoryMetrics.usedJSHeapSize.toFixed(1) }} MB / {{ memoryMetrics.jsHeapSizeLimit.toFixed(1) }} MB
        </div>
      </div>

      <!-- DOM Complexity -->
      <div class="bg-white/80 dark:bg-gray-900/40 backdrop-blur-sm rounded-xl p-3 border border-purple-200/50 dark:border-purple-800/30 shadow-sm">
        <div class="flex items-center justify-between mb-1.5">
          <span class="text-xs font-medium text-muted-foreground">DOM Complexity</span>
          <span v-if="domMetrics.hasPerformanceIssue" class="text-xs text-amber-600 font-medium">
            ⚠️ High
          </span>
        </div>
        <div class="space-y-1">
          <div class="flex items-center justify-between text-xs">
            <span class="text-muted-foreground">Total Nodes:</span>
            <span class="font-mono font-semibold">{{ domMetrics.totalNodes.toLocaleString() }}</span>
          </div>
          <div class="flex items-center justify-between text-xs">
            <span class="text-muted-foreground">Tree Depth:</span>
            <span class="font-mono font-semibold">{{ domMetrics.depth }}</span>
          </div>
        </div>
      </div>

      <!-- Real Chrome Performance Metrics -->
      <div class="bg-white/80 dark:bg-gray-900/40 backdrop-blur-sm rounded-xl p-3 border border-emerald-200/50 dark:border-emerald-800/30 shadow-sm">
        <div class="text-xs font-medium text-muted-foreground mb-2">Chrome Web Vitals</div>
        <div class="space-y-1.5">
          <!-- LCP -->
          <div class="flex items-center justify-between text-xs">
            <span class="text-muted-foreground">LCP (Largest Paint)</span>
            <span class="font-mono font-semibold" :class="realPerfMetrics.lcp > 2500 ? 'text-red-600' : realPerfMetrics.lcp > 1200 ? 'text-amber-600' : 'text-emerald-600'">
              {{ realPerfMetrics.lcp ? realPerfMetrics.lcp + 'ms' : 'N/A' }}
            </span>
          </div>
          
          <!-- FCP -->
          <div class="flex items-center justify-between text-xs">
            <span class="text-muted-foreground">FCP (First Paint)</span>
            <span class="font-mono font-semibold" :class="realPerfMetrics.fcp > 3000 ? 'text-red-600' : realPerfMetrics.fcp > 1800 ? 'text-amber-600' : 'text-emerald-600'">
              {{ realPerfMetrics.fcp ? realPerfMetrics.fcp + 'ms' : 'N/A' }}
            </span>
          </div>
          
          <!-- CLS -->
          <div class="flex items-center justify-between text-xs">
            <span class="text-muted-foreground">CLS (Layout Shift)</span>
            <span class="font-mono font-semibold" :class="realPerfMetrics.cls > 0.25 ? 'text-red-600' : realPerfMetrics.cls > 0.1 ? 'text-amber-600' : 'text-emerald-600'">
              {{ realPerfMetrics.cls.toFixed(3) }}
            </span>
          </div>
          
          <!-- Long Tasks -->
          <div class="flex items-center justify-between text-xs">
            <span class="text-muted-foreground">Long Tasks</span>
            <span class="font-mono font-semibold" :class="realPerfMetrics.longTasks > 10 ? 'text-red-600' : realPerfMetrics.longTasks > 5 ? 'text-amber-600' : 'text-emerald-600'">
              {{ realPerfMetrics.longTasks }}
            </span>
          </div>
        </div>
      </div>

      <!-- Last Updated -->
      <div class="text-xs text-muted-foreground text-center pt-2 border-t">
        Last updated: {{ lastUpdated }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { X, RefreshCw, Gauge } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import {
  getMemoryMetrics,
  getDOMMetrics,
  getPerformanceMetrics,
  getPerformanceLevel,
  getPerformanceColor
} from '@/services/performanceTracker'

const props = defineProps({
  isEditMode: {
    type: Boolean,
    default: false
  }
})

defineEmits(['remove', 'configure'])

const memoryMetrics = ref({
  available: false,
  usedJSHeapSize: 0,
  totalJSHeapSize: 0,
  jsHeapSizeLimit: 0,
  usedPercentage: 0
})

const domMetrics = ref({
  totalNodes: 0,
  depth: 0,
  hasPerformanceIssue: false
})

const realPerfMetrics = ref({
  lcp: null,
  fcp: null,
  cls: 0,
  longTasks: 0
})

const lastUpdated = ref('')
const refreshing = ref(false)

const performanceLevel = computed(() => {
  return getPerformanceLevel(memoryMetrics.value.usedPercentage)
})

const refreshMetrics = () => {
  refreshing.value = true
  
  // Get memory metrics
  memoryMetrics.value = getMemoryMetrics()
  
  // Get DOM metrics
  domMetrics.value = getDOMMetrics()
  
  // Get real performance metrics
  realPerfMetrics.value = getPerformanceMetrics()
  
  // Update timestamp
  const now = new Date()
  lastUpdated.value = now.toLocaleTimeString()
  
  setTimeout(() => {
    refreshing.value = false
  }, 500)
}

const getPerformanceBackgroundColor = (level) => {
  switch (level) {
    case 'good':
      return 'bg-green-50 border-green-200'
    case 'warning':
      return 'bg-yellow-50 border-yellow-200'
    case 'critical':
      return 'bg-red-50 border-red-200'
    default:
      return 'bg-muted/50'
  }
}

const getPerformanceBgBar = (level) => {
  switch (level) {
    case 'good':
      return 'bg-green-500'
    case 'warning':
      return 'bg-yellow-500'
    case 'critical':
      return 'bg-red-500'
    default:
      return 'bg-gray-500'
  }
}

const getPerformanceLabel = (level) => {
  switch (level) {
    case 'good':
      return '✓ Good'
    case 'warning':
      return '⚠ Warning'
    case 'critical':
      return '✗ Critical'
    default:
      return 'Unknown'
  }
}

const getPerformanceMessage = (level) => {
  switch (level) {
    case 'good':
      return 'Report is performing well'
    case 'warning':
      return 'Consider reducing widget count'
    case 'critical':
      return 'Remove widgets to improve performance'
    default:
      return ''
  }
}

onMounted(() => {
  refreshMetrics()
})
</script>

