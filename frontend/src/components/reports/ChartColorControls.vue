<template>
  <div class="space-y-4">
    <div class="text-sm font-semibold text-foreground mb-2">Colors & Styling</div>
    
    <!-- Color Scheme Selector -->
    <div>
      <label class="text-xs font-medium text-muted-foreground mb-2 block">Color Palette</label>
      <div class="grid grid-cols-2 gap-2">
        <button
          v-for="scheme in colorSchemes"
          :key="scheme.value"
          @click="selectScheme(scheme.value)"
          class="relative p-3 rounded-lg border-2 transition-all hover:border-primary/50"
          :class="localConfig.colorScheme === scheme.value ? 'border-primary bg-primary/5' : 'border-border'"
        >
          <div class="flex items-center gap-2 mb-1">
            <div class="flex gap-1">
              <div
                v-for="(color, idx) in scheme.preview"
                :key="idx"
                class="w-3 h-3 rounded"
                :style="{ backgroundColor: color }"
              ></div>
            </div>
          </div>
          <div class="text-xs font-medium text-foreground text-left">{{ scheme.label }}</div>
        </button>
      </div>
    </div>

    <!-- Conditional Colors -->
    <div class="space-y-2 pt-2 border-t border-border">
      <div class="flex items-center justify-between">
        <label class="text-xs font-medium text-muted-foreground">Financial Colors</label>
        <input
          type="checkbox"
          v-model="localConfig.useConditionalColors"
          @change="emit('update')"
          class="w-4 h-4 rounded border-border text-primary focus:ring-primary"
        />
      </div>
      <div v-if="localConfig.useConditionalColors" class="text-xs text-muted-foreground ml-1">
        Positive values = green, negative = red
      </div>
    </div>

    <!-- Heatmap Specific -->
    <div v-if="showHeatmapOptions" class="space-y-2 pt-2 border-t border-border">
      <label class="text-xs font-medium text-muted-foreground mb-2 block">Heatmap Colors</label>
      <Select v-model="localConfig.heatmapColorScheme" @update:modelValue="emit('update')">
        <SelectTrigger>
          <SelectValue placeholder="Blue to Red" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="blue-red">Blue to Red (Default)</SelectItem>
          <SelectItem value="green-red">Green to Red (Financial)</SelectItem>
          <SelectItem value="blues">Blues</SelectItem>
          <SelectItem value="greens">Greens</SelectItem>
          <SelectItem value="reds">Reds</SelectItem>
          <SelectItem value="purples">Purples</SelectItem>
          <SelectItem value="viridis">Viridis</SelectItem>
          <SelectItem value="plasma">Plasma</SelectItem>
          <SelectItem value="diverging">Diverging (Red-Yellow-Green)</SelectItem>
        </SelectContent>
      </Select>
    </div>
  </div>
</template>

<script setup>
import { reactive, watch } from 'vue'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

const props = defineProps({
  config: {
    type: Object,
    default: () => ({})
  },
  showHeatmapOptions: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update'])

const colorSchemes = [
  {
    value: 'revolut',
    label: 'Revolut',
    preview: ['#4F46E5', '#EC4899', '#10B981', '#F59E0B']
  },
  {
    value: 'financial',
    label: 'Financial',
    preview: ['#10B981', '#EF4444', '#6B7280', '#9CA3AF']
  },
  {
    value: 'sequential-blues',
    label: 'Blues',
    preview: ['#EFF6FF', '#93C5FD', '#3B82F6', '#1E40AF']
  },
  {
    value: 'sequential-greens',
    label: 'Greens',
    preview: ['#F0FDF4', '#86EFAC', '#22C55E', '#166534']
  },
  {
    value: 'sequential-reds',
    label: 'Reds',
    preview: ['#FEF2F2', '#FCA5A5', '#EF4444', '#991B1B']
  },
  {
    value: 'sequential-purples',
    label: 'Purples',
    preview: ['#FAF5FF', '#D8B4FE', '#A855F7', '#6B21A8']
  }
]

const localConfig = reactive({
  colorScheme: props.config.colorScheme || 'revolut',
  useConditionalColors: props.config.useConditionalColors || false,
  heatmapColorScheme: props.config.heatmapColorScheme || 'blue-red'
})

const selectScheme = (scheme) => {
  localConfig.colorScheme = scheme
  emit('update')
}

// Watch for external config changes
watch(() => props.config, (newConfig) => {
  Object.assign(localConfig, {
    colorScheme: newConfig.colorScheme || 'revolut',
    useConditionalColors: newConfig.useConditionalColors || false,
    heatmapColorScheme: newConfig.heatmapColorScheme || 'blue-red'
  })
}, { deep: true })

// Expose config for parent
defineExpose({ config: localConfig })
</script>

