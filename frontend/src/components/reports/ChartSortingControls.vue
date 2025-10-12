<template>
  <div class="space-y-4">
    <div class="text-sm font-semibold text-foreground mb-2">Sorting & Filtering</div>
    
    <!-- Sort Mode -->
    <div>
      <label class="text-xs font-medium text-muted-foreground mb-1 block">Sort By</label>
      <Select v-model="localConfig.sortMode" @update:modelValue="emit('update')">
        <SelectTrigger>
          <SelectValue placeholder="No sorting" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="none">No Sorting</SelectItem>
          <SelectItem value="value">Value</SelectItem>
          <SelectItem value="label">Label</SelectItem>
        </SelectContent>
      </Select>
    </div>

    <!-- Sort Direction (only show if sorting enabled) -->
    <div v-if="localConfig.sortMode && localConfig.sortMode !== 'none'">
      <label class="text-xs font-medium text-muted-foreground mb-1 block">Direction</label>
      <Select v-model="localConfig.sortDirection" @update:modelValue="emit('update')">
        <SelectTrigger>
          <SelectValue placeholder="Descending" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="desc">Descending (High to Low)</SelectItem>
          <SelectItem value="asc">Ascending (Low to High)</SelectItem>
        </SelectContent>
      </Select>
    </div>

    <!-- Top N Filter -->
    <div>
      <div class="flex items-center justify-between mb-1">
        <label class="text-xs font-medium text-muted-foreground">Show Top N</label>
        <span v-if="localConfig.topN" class="text-xs font-semibold text-foreground">{{ localConfig.topN }}</span>
      </div>
      <div class="flex items-center gap-2">
        <input
          type="range"
          v-model.number="localConfig.topN"
          min="0"
          max="50"
          step="1"
          @input="emit('update')"
          class="flex-1 h-2 bg-muted rounded-lg appearance-none cursor-pointer accent-primary"
        />
        <Button
          v-if="localConfig.topN > 0"
          @click="localConfig.topN = 0; emit('update')"
          variant="ghost"
          size="sm"
          class="h-6 px-2"
        >
          Clear
        </Button>
      </div>
      <div class="text-xs text-muted-foreground mt-1">
        {{ localConfig.topN > 0 ? `Showing ${localConfig.topN} items` : 'Show all items' }}
      </div>
    </div>

    <!-- Filter Options -->
    <div class="space-y-2 pt-2 border-t border-border">
      <div class="flex items-center justify-between">
        <label class="text-xs font-medium text-muted-foreground">Hide Zero Values</label>
        <input
          type="checkbox"
          v-model="localConfig.hideZeros"
          @change="emit('update')"
          class="w-4 h-4 rounded border-border text-primary focus:ring-primary"
        />
      </div>
      
      <div class="flex items-center justify-between">
        <label class="text-xs font-medium text-muted-foreground">Hide Negative Values</label>
        <input
          type="checkbox"
          v-model="localConfig.hideNegatives"
          @change="emit('update')"
          class="w-4 h-4 rounded border-border text-primary focus:ring-primary"
        />
      </div>
      
      <div class="flex items-center justify-between">
        <label class="text-xs font-medium text-muted-foreground">Hide Outliers</label>
        <input
          type="checkbox"
          v-model="localConfig.hideOutliers"
          @change="emit('update')"
          class="w-4 h-4 rounded border-border text-primary focus:ring-primary"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, watch } from 'vue'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Button } from '@/components/ui/button'

const props = defineProps({
  config: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update'])

const localConfig = reactive({
  sortMode: props.config.sortMode || 'none',
  sortDirection: props.config.sortDirection || 'desc',
  topN: props.config.topN || 0,
  hideZeros: props.config.hideZeros || false,
  hideNegatives: props.config.hideNegatives || false,
  hideOutliers: props.config.hideOutliers || false
})

// Watch for external config changes
watch(() => props.config, (newConfig) => {
  Object.assign(localConfig, {
    sortMode: newConfig.sortMode || 'none',
    sortDirection: newConfig.sortDirection || 'desc',
    topN: newConfig.topN || 0,
    hideZeros: newConfig.hideZeros || false,
    hideNegatives: newConfig.hideNegatives || false,
    hideOutliers: newConfig.hideOutliers || false
  })
}, { deep: true })

// Expose config for parent
defineExpose({ config: localConfig })
</script>

