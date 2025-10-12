<template>
  <div class="space-y-4">
    <div class="text-sm font-semibold text-foreground mb-2">Axis & Grid</div>
    
    <!-- Show/Hide Axes -->
    <div class="space-y-2">
      <div class="flex items-center justify-between">
        <label class="text-xs font-medium text-muted-foreground">Show X-Axis</label>
        <input
          type="checkbox"
          v-model="localConfig.showXAxis"
          @change="emit('update')"
          class="w-4 h-4 rounded border-border text-primary focus:ring-primary"
        />
      </div>
      
      <div class="flex items-center justify-between">
        <label class="text-xs font-medium text-muted-foreground">Show Y-Axis</label>
        <input
          type="checkbox"
          v-model="localConfig.showYAxis"
          @change="emit('update')"
          class="w-4 h-4 rounded border-border text-primary focus:ring-primary"
        />
      </div>
      
      <div class="flex items-center justify-between">
        <label class="text-xs font-medium text-muted-foreground">Show Zero Line</label>
        <input
          type="checkbox"
          v-model="localConfig.showZeroLine"
          @change="emit('update')"
          class="w-4 h-4 rounded border-border text-primary focus:ring-primary"
        />
      </div>
    </div>

    <!-- Grid Style -->
    <div class="pt-2 border-t border-border">
      <label class="text-xs font-medium text-muted-foreground mb-2 block">Grid Style</label>
      <div class="grid grid-cols-2 gap-2">
        <button
          v-for="style in gridStyles"
          :key="style.value"
          @click="selectGridStyle(style.value)"
          class="p-2 rounded-lg border-2 transition-all hover:border-primary/50 text-left"
          :class="localConfig.gridStyle === style.value ? 'border-primary bg-primary/5' : 'border-border'"
        >
          <div class="text-xs font-medium text-foreground">{{ style.label }}</div>
          <div class="text-[10px] text-muted-foreground mt-0.5">{{ style.desc }}</div>
        </button>
      </div>
    </div>

    <!-- Label Rotation -->
    <div class="pt-2 border-t border-border">
      <div class="flex items-center justify-between mb-1">
        <label class="text-xs font-medium text-muted-foreground">Label Rotation</label>
        <span class="text-xs font-semibold text-foreground">{{ localConfig.labelRotation }}°</span>
      </div>
      <input
        type="range"
        v-model.number="localConfig.labelRotation"
        min="-90"
        max="0"
        step="15"
        @input="emit('update')"
        class="w-full h-2 bg-muted rounded-lg appearance-none cursor-pointer accent-primary"
      />
      <div class="flex justify-between text-[10px] text-muted-foreground mt-1">
        <span>-90°</span>
        <span>-45°</span>
        <span>0°</span>
      </div>
    </div>

    <!-- Animation Controls -->
    <div class="space-y-2 pt-2 border-t border-border">
      <div class="flex items-center justify-between">
        <label class="text-xs font-medium text-muted-foreground">Enable Animations</label>
        <input
          type="checkbox"
          v-model="localConfig.enableAnimations"
          @change="emit('update')"
          class="w-4 h-4 rounded border-border text-primary focus:ring-primary"
        />
      </div>
      
      <div v-if="localConfig.enableAnimations">
        <div class="flex items-center justify-between mb-1">
          <label class="text-xs font-medium text-muted-foreground">Speed</label>
          <span class="text-xs font-semibold text-foreground">{{ localConfig.animationSpeed }}ms</span>
        </div>
        <input
          type="range"
          v-model.number="localConfig.animationSpeed"
          min="200"
          max="2000"
          step="100"
          @input="emit('update')"
          class="w-full h-2 bg-muted rounded-lg appearance-none cursor-pointer accent-primary"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, watch } from 'vue'

const props = defineProps({
  config: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update'])

const gridStyles = [
  { value: 'none', label: 'None', desc: 'No grid' },
  { value: 'dots', label: 'Dots', desc: 'Subtle dots' },
  { value: 'dashed', label: 'Dashed', desc: 'Dashed lines' },
  { value: 'solid', label: 'Solid', desc: 'Solid lines' }
]

const localConfig = reactive({
  showXAxis: props.config.axisConfig?.showXAxis !== false,
  showYAxis: props.config.axisConfig?.showYAxis !== false,
  showZeroLine: props.config.axisConfig?.showZeroLine !== false,
  gridStyle: props.config.axisConfig?.gridStyle || 'dashed',
  labelRotation: props.config.axisConfig?.labelRotation !== undefined ? props.config.axisConfig.labelRotation : -45,
  enableAnimations: props.config.enableAnimations !== false,
  animationSpeed: props.config.animationSpeed || 800
})

const selectGridStyle = (style) => {
  localConfig.gridStyle = style
  emit('update')
}

// Watch for external config changes
watch(() => props.config, (newConfig) => {
  Object.assign(localConfig, {
    showXAxis: newConfig.axisConfig?.showXAxis !== false,
    showYAxis: newConfig.axisConfig?.showYAxis !== false,
    showZeroLine: newConfig.axisConfig?.showZeroLine !== false,
    gridStyle: newConfig.axisConfig?.gridStyle || 'dashed',
    labelRotation: newConfig.axisConfig?.labelRotation !== undefined ? newConfig.axisConfig.labelRotation : -45,
    enableAnimations: newConfig.enableAnimations !== false,
    animationSpeed: newConfig.animationSpeed || 800
  })
}, { deep: true })

// Expose config for parent with proper structure
defineExpose({ 
  getConfig: () => ({
    axisConfig: {
      showXAxis: localConfig.showXAxis,
      showYAxis: localConfig.showYAxis,
      showZeroLine: localConfig.showZeroLine,
      gridStyle: localConfig.gridStyle,
      labelRotation: localConfig.labelRotation
    },
    enableAnimations: localConfig.enableAnimations,
    animationSpeed: localConfig.animationSpeed
  })
})
</script>

