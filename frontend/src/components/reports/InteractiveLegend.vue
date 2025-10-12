<template>
  <div class="interactive-legend" :class="{ 'legend-vertical': orientation === 'vertical', 'legend-horizontal': orientation === 'horizontal' }">
    <div
      v-for="(item, index) in items"
      :key="index"
      class="legend-item"
      :class="{ 'legend-item-disabled': !item.visible }"
      @click="toggleSeries(index)"
      :title="item.visible ? 'Click to hide' : 'Click to show'"
    >
      <div class="legend-marker" :style="{ backgroundColor: item.color, opacity: item.visible ? 1 : 0.3 }"></div>
      <span class="legend-label" :style="{ opacity: item.visible ? 1 : 0.5 }">{{ item.name }}</span>
      <span v-if="showValues && item.value !== undefined" class="legend-value" :style="{ opacity: item.visible ? 1 : 0.5 }">
        {{ formatValue(item.value) }}
      </span>
    </div>
  </div>
</template>

<script setup>
import { formatCurrency } from '@/utils/currency'

const props = defineProps({
  items: {
    type: Array,
    required: true,
    // Array of { name, color, visible, value? }
  },
  orientation: {
    type: String,
    default: 'horizontal', // 'horizontal' | 'vertical'
  },
  showValues: {
    type: Boolean,
    default: false
  },
  currencyCode: {
    type: String,
    default: null
  }
})

const emit = defineEmits(['toggle-series'])

const toggleSeries = (index) => {
  emit('toggle-series', index)
}

const formatValue = (value) => {
  if (props.currencyCode) {
    return formatCurrency(value, props.currencyCode, { compact: true })
  }
  if (Math.abs(value) >= 1000) {
    return new Intl.NumberFormat('en-US', { notation: 'compact', maximumFractionDigits: 1 }).format(value)
  }
  return value.toLocaleString()
}
</script>

<style scoped>
.interactive-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  padding: 8px 0;
  user-select: none;
}

.legend-horizontal {
  flex-direction: row;
  align-items: center;
}

.legend-vertical {
  flex-direction: column;
  align-items: flex-start;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  padding: 4px 8px;
  border-radius: 4px;
}

.legend-item:hover {
  background-color: rgba(0, 0, 0, 0.05);
}

.legend-item-disabled {
  opacity: 0.6;
}

.legend-marker {
  width: 12px;
  height: 12px;
  border-radius: 2px;
  transition: opacity 0.2s ease;
  flex-shrink: 0;
}

.legend-label {
  font-size: 12px;
  font-weight: 500;
  transition: opacity 0.2s ease;
  color: var(--foreground);
}

.legend-value {
  font-size: 11px;
  font-weight: 600;
  margin-left: 4px;
  transition: opacity 0.2s ease;
  color: var(--muted-foreground);
}
</style>

