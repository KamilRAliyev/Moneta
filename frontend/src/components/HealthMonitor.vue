<script setup>
import { computed } from 'vue'
import { useHealth } from '@/services/health'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import { CheckCircle2, WifiOff, AlertTriangle, Activity } from 'lucide-vue-next'

const props = defineProps({ 
  isCollapsed: { 
    type: Boolean, 
    default: false 
  } 
})

const { status, latency, lastChecked } = useHealth()

const icon = computed(() => {
  switch (status.value) {
    case 'online': return CheckCircle2
    case 'degraded': return AlertTriangle
    case 'offline': return WifiOff
    default: return Activity
  }
})

const color = computed(() => {
  switch (status.value) {
    case 'online': return 'text-green-600 dark:text-green-400'
    case 'degraded': return 'text-yellow-600 dark:text-yellow-300'
    case 'offline': return 'text-destructive'
    default: return 'text-muted-foreground'
  }
})

const label = computed(() => status.value.charAt(0).toUpperCase() + status.value.slice(1))
</script>

<template>
  <Tooltip>
    <TooltipTrigger as-child>
      <div 
        :class="[
          'flex items-center gap-2 cursor-pointer transition-colors hover:bg-accent rounded-md',
          props.isCollapsed ? 'px-2 py-2' : 'px-3 py-2'
        ]"
      >
        <component :is="icon" :class="['size-4', color]" />
        <span v-if="!props.isCollapsed" class="text-sm text-muted-foreground">{{ label }}</span>
      </div>
    </TooltipTrigger>
    <TooltipContent side="bottom" align="end">
      <div class="text-xs">
        <div>Status: {{ label }}</div>
        <div v-if="latency != null">Latency: {{ latency }} ms</div>
        <div v-if="lastChecked">Checked: {{ new Date(lastChecked).toLocaleTimeString() }}</div>
      </div>
    </TooltipContent>
  </Tooltip>
</template>
