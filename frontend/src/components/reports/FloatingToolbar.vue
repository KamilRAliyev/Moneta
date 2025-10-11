<template>
  <!-- No backdrop - content should remain visible and interactive -->
  
  <div 
    ref="toolbarRef"
    :style="toolbarStyle"
    :class="[
      'fixed bg-card border shadow-lg p-4 z-50 overflow-y-auto',
      mode === 'sidebar' ? 'w-[400px] max-w-full h-full rounded-none' : 'rounded-lg min-w-[300px] max-w-[400px] max-h-[80vh]'
    ]"
    @mousedown="mode === 'floating' ? startDrag($event) : undefined"
  >
    <!-- Drag Handle (floating mode only) -->
    <div 
      v-if="mode === 'floating'"
      class="flex items-center justify-between mb-3 cursor-move border-b pb-2 sticky top-0 bg-card z-10">
      <div class="flex items-center space-x-2">
        <GripVertical class="w-4 h-4 text-muted-foreground" />
        <span class="text-sm font-medium">{{ selectedWidget ? 'Widget Configuration' : 'Report Controls' }}</span>
      </div>
      <div class="flex items-center space-x-1">
        <Button @click="emit('toggle-display-mode')" variant="ghost" size="sm" class="h-6 w-6 p-0" title="Switch to sidebar mode">
          <Monitor class="w-4 h-4" />
        </Button>
        <Button v-if="selectedWidget" @click="closeWidgetConfig" variant="ghost" size="sm" class="h-6 w-6 p-0">
          <X class="w-4 h-4" />
        </Button>
        <Button @click="toggleCollapsed" variant="ghost" size="sm" class="h-6 w-6 p-0">
          <component :is="isCollapsed ? ChevronDown : ChevronUp" class="w-4 h-4" />
        </Button>
      </div>
    </div>
    
    <!-- Header for sidebar mode -->
    <div 
      v-if="mode === 'sidebar'"
      class="flex items-center justify-between mb-3 border-b pb-2 sticky top-0 bg-card z-10"
    >
      <div class="flex items-center space-x-2">
        <span class="text-sm font-medium">{{ selectedWidget ? 'Widget Configuration' : 'Report Controls' }}</span>
      </div>
      <div class="flex items-center space-x-1">
        <Button @click="emit('toggle-display-mode')" variant="ghost" size="sm" class="h-6 w-6 p-0" title="Switch to floating mode">
          <Monitor class="w-4 h-4" />
        </Button>
        <Button v-if="selectedWidget" @click="closeWidgetConfig" variant="ghost" size="sm" class="h-6 w-6 p-0">
          <X class="w-4 h-4" />
        </Button>
        <Button @click="toggleCollapsed" variant="ghost" size="sm" class="h-6 w-6 p-0">
          <component :is="isCollapsed ? ChevronDown : ChevronUp" class="w-4 h-4" />
        </Button>
        <Button @click="emit('close')" variant="ghost" size="sm" class="h-6 w-6 p-0">
          <X class="w-4 h-4" />
        </Button>
      </div>
    </div>

    <!-- Toolbar Content -->
    <div v-if="!isCollapsed" class="space-y-4">
      <!-- Widget Configuration Panel -->
      <div v-if="selectedWidget" class="space-y-3">
        <!-- Widget Type Badge -->
        <div class="flex items-center space-x-2">
          <component :is="getWidgetIcon(selectedWidget.type)" class="w-4 h-4" />
          <span class="text-sm font-medium capitalize">{{ selectedWidget.type }} Widget</span>
        </div>

        <!-- Chart Widget Config -->
        <div v-if="selectedWidget.type === 'chart'" class="space-y-3">
          <!-- Chart Title -->
          <div>
            <Label class="block text-sm font-medium mb-1">Chart Title</Label>
            <Input 
              v-model="localConfig.title" 
              placeholder="Enter chart title"
              @input="emitConfigUpdate"
            />
          </div>

          <!-- Chart Type -->
          <div>
            <Label class="block text-sm font-medium mb-1">Chart Type</Label>
            <Select v-model="localConfig.chartType" @update:modelValue="emitConfigUpdate">
              <SelectTrigger><SelectValue placeholder="Select type..." /></SelectTrigger>
              <SelectContent>
                <SelectItem value="bar">Bar Chart</SelectItem>
                <SelectItem value="line">Line Chart</SelectItem>
                <SelectItem value="donut">Donut Chart</SelectItem>
                <SelectItem value="area">Area Chart</SelectItem>
                <SelectItem value="treemap">Treemap</SelectItem>
                <SelectItem value="scatter">Scatter Plot</SelectItem>
                <SelectItem value="bubble">Bubble Chart</SelectItem>
                <SelectItem value="stacked">Stacked Bar</SelectItem>
                <SelectItem value="waterfall">Waterfall</SelectItem>
                <SelectItem value="heatmap">Heatmap</SelectItem>
                <SelectItem value="sankey">Sankey Diagram</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <!-- X Field -->
          <div>
            <Label class="block text-sm font-medium mb-1">X Field (Group By)</Label>
            <Select v-model="localConfig.x_field" @update:modelValue="emitConfigUpdate">
              <SelectTrigger><SelectValue placeholder="Select field..." /></SelectTrigger>
              <SelectContent>
                <div v-if="availableFields.ingested.length > 0">
                  <div class="px-2 py-1.5 text-xs font-semibold text-muted-foreground">Ingested Columns</div>
                  <SelectItem v-for="field in availableFields.ingested" :key="field" :value="field">{{ field }}</SelectItem>
                </div>
                <div v-if="availableFields.computed.length > 0">
                  <div class="px-2 py-1.5 text-xs font-semibold text-muted-foreground">Computed Columns</div>
                  <SelectItem v-for="field in availableFields.computed" :key="field" :value="field">{{ field }}</SelectItem>
                </div>
              </SelectContent>
            </Select>
          </div>

          <!-- Y Field -->
          <div>
            <Label class="block text-sm font-medium mb-1">Y Field (Aggregate)</Label>
            <Select v-model="localConfig.y_field" @update:modelValue="emitConfigUpdate">
              <SelectTrigger><SelectValue placeholder="Select field..." /></SelectTrigger>
              <SelectContent>
                <div v-if="availableFields.ingested.length > 0">
                  <div class="px-2 py-1.5 text-xs font-semibold text-muted-foreground">Ingested Columns</div>
                  <SelectItem v-for="field in availableFields.ingested" :key="field" :value="field">{{ field }}</SelectItem>
                </div>
                <div v-if="availableFields.computed.length > 0">
                  <div class="px-2 py-1.5 text-xs font-semibold text-muted-foreground">Computed Columns</div>
                  <SelectItem v-for="field in availableFields.computed" :key="field" :value="field">{{ field }}</SelectItem>
                </div>
              </SelectContent>
            </Select>
          </div>

          <!-- Aggregation -->
          <div>
            <Label class="block text-sm font-medium mb-1">Aggregation</Label>
            <Select v-model="localConfig.aggregation" @update:modelValue="emitConfigUpdate">
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="sum">Sum</SelectItem>
                <SelectItem value="avg">Average</SelectItem>
                <SelectItem value="count">Count</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <!-- Show Legend -->
          <div class="flex items-center space-x-2">
            <Checkbox 
              :checked="localConfig.showLegend !== false" 
              @update:checked="(val) => { localConfig.showLegend = val; emitConfigUpdate() }"
            />
            <Label class="text-sm cursor-pointer">Show Legend</Label>
          </div>

          <!-- Number Format -->
          <div class="flex items-center space-x-2">
            <Checkbox 
              :checked="localConfig.compactNumbers === true" 
              @update:checked="(val) => { localConfig.compactNumbers = val; emitConfigUpdate() }"
            />
            <Label class="text-sm cursor-pointer">Compact numbers (K, M)</Label>
          </div>

          <!-- Currency Configuration -->
          <div class="space-y-3 pt-3 border-t">
            <Label class="text-sm font-semibold">Currency Settings</Label>
            
            <!-- Currency Mode -->
            <div>
              <Label class="block text-sm font-medium mb-1">Currency Mode</Label>
              <Select v-model="localConfig.currency_mode" @update:modelValue="emitConfigUpdate">
                <SelectTrigger><SelectValue placeholder="None" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">None</SelectItem>
                  <SelectItem value="field">From Data Field</SelectItem>
                  <SelectItem value="fixed">Fixed Currency (Recommended)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <!-- Currency Field (when mode is "field") -->
            <div v-if="localConfig.currency_mode === 'field'">
              <Label class="block text-sm font-medium mb-1">Currency Field</Label>
              <Select v-model="localConfig.currency_field" @update:modelValue="emitConfigUpdate">
                <SelectTrigger><SelectValue placeholder="Select currency field..." /></SelectTrigger>
                <SelectContent>
                  <SelectItem v-if="currencyFields.length === 0" value="" disabled>
                    No currency fields detected
                  </SelectItem>
                  <SelectItem v-for="field in currencyFields" :key="field" :value="field">{{ field }}</SelectItem>
                </SelectContent>
              </Select>
              <p v-if="currencyFields.length === 0" class="text-xs text-muted-foreground mt-1">
                💡 Tip: Use "Fixed Currency" mode instead
              </p>
              <p v-else class="text-xs text-success mt-1">
                ✓ Found {{ currencyFields.length }} currency field(s)
              </p>
            </div>

            <!-- Fixed Currency Code (when mode is "fixed") -->
            <div v-if="localConfig.currency_mode === 'fixed'">
              <Label class="block text-sm font-medium mb-1">Currency Code</Label>
              <Input 
                v-model="localConfig.currency_code" 
                placeholder="USD"
                @input="emitConfigUpdate"
              />
              <p class="text-xs text-muted-foreground mt-1">
                Enter: USD, EUR, GBP, JPY, etc.
              </p>
            </div>

            <!-- Group by Currency (when mode is "field") -->
            <div v-if="localConfig.currency_mode === 'field'" class="flex items-center space-x-2">
              <Checkbox 
                :checked="localConfig.split_by_currency === true" 
                @update:checked="(val) => { localConfig.split_by_currency = val; emitConfigUpdate() }"
              />
              <Label class="text-sm cursor-pointer">Group by currency (split into series)</Label>
            </div>
          </div>
        </div>

        <!-- Stats Widget Config -->
        <div v-if="selectedWidget.type === 'stats'" class="space-y-3">
          <!-- Stats Title -->
          <div>
            <Label class="block text-sm font-medium mb-1">Title</Label>
            <Input 
              v-model="localConfig.title" 
              placeholder="Enter title"
              @input="emitConfigUpdate"
            />
          </div>

          <!-- Value Field -->
          <div>
            <Label class="block text-sm font-medium mb-1">Value Field</Label>
            <Select v-model="localConfig.y_field" @update:modelValue="emitConfigUpdate">
              <SelectTrigger><SelectValue placeholder="Select field..." /></SelectTrigger>
              <SelectContent>
                <div v-if="availableFields.ingested.length > 0">
                  <div class="px-2 py-1.5 text-xs font-semibold text-muted-foreground">Ingested Columns</div>
                  <SelectItem v-for="field in availableFields.ingested" :key="field" :value="field">{{ field }}</SelectItem>
                </div>
                <div v-if="availableFields.computed.length > 0">
                  <div class="px-2 py-1.5 text-xs font-semibold text-muted-foreground">Computed Columns</div>
                  <SelectItem v-for="field in availableFields.computed" :key="field" :value="field">{{ field }}</SelectItem>
                </div>
              </SelectContent>
            </Select>
          </div>

          <!-- Aggregation -->
          <div>
            <Label class="block text-sm font-medium mb-1">Aggregation</Label>
            <Select v-model="localConfig.aggregation" @update:modelValue="emitConfigUpdate">
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="sum">Sum</SelectItem>
                <SelectItem value="avg">Average</SelectItem>
                <SelectItem value="count">Count</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <!-- Currency Configuration -->
          <div class="space-y-3 pt-3 border-t">
            <Label class="text-sm font-semibold">Currency Settings</Label>
            
            <!-- Currency Mode -->
            <div>
              <Label class="block text-sm font-medium mb-1">Currency Mode</Label>
              <Select v-model="localConfig.currency_mode" @update:modelValue="emitConfigUpdate">
                <SelectTrigger><SelectValue placeholder="None" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">None</SelectItem>
                  <SelectItem value="field">From Data Field</SelectItem>
                  <SelectItem value="fixed">Fixed Currency (Recommended)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <!-- Currency Field (when mode is "field") -->
            <div v-if="localConfig.currency_mode === 'field'">
              <Label class="block text-sm font-medium mb-1">Currency Field</Label>
              <Select v-model="localConfig.currency_field" @update:modelValue="emitConfigUpdate">
                <SelectTrigger><SelectValue placeholder="Select currency field..." /></SelectTrigger>
                <SelectContent>
                  <SelectItem v-if="currencyFields.length === 0" value="" disabled>
                    No currency fields detected
                  </SelectItem>
                  <SelectItem v-for="field in currencyFields" :key="field" :value="field">{{ field }}</SelectItem>
                </SelectContent>
              </Select>
              <p v-if="currencyFields.length === 0" class="text-xs text-muted-foreground mt-1">
                💡 Tip: Use "Fixed Currency" mode instead
              </p>
              <p v-else class="text-xs text-success mt-1">
                ✓ Found {{ currencyFields.length }} currency field(s)
              </p>
            </div>

            <!-- Fixed Currency Code (when mode is "fixed") -->
            <div v-if="localConfig.currency_mode === 'fixed'">
              <Label class="block text-sm font-medium mb-1">Currency Code</Label>
              <Input 
                v-model="localConfig.currency_code" 
                placeholder="USD"
                @input="emitConfigUpdate"
              />
              <p class="text-xs text-muted-foreground mt-1">
                Enter: USD, EUR, GBP, JPY, etc.
              </p>
            </div>
          </div>
        </div>
      </div>

      <!-- Report Controls (when no widget selected) -->
      <div v-else class="space-y-3">
        <!-- Report Name -->
        <div v-if="reportName">
          <Label class="text-xs text-muted-foreground">Report</Label>
          <div class="text-sm font-medium">{{ reportName }}</div>
        </div>

        <!-- Mode Toggle -->
        <Button
          @click="$emit('toggle-mode')"
          :variant="isEditMode ? 'default' : 'outline'"
          class="w-full"
          size="sm"
        >
          <component :is="isEditMode ? Edit : Lock" class="w-4 h-4 mr-2" />
          {{ isEditMode ? 'Edit Mode' : 'Lock Mode' }}
        </Button>

        <!-- Save Report Button (Edit Mode Only) -->
        <Button
          v-if="isEditMode"
          @click="$emit('save-report')"
          variant="default"
          class="w-full bg-green-600 hover:bg-green-700"
          size="sm"
        >
          <Save class="w-4 h-4 mr-2" />
          Save & Lock
        </Button>

        <!-- Used Fields Section -->
        <div v-if="usedFields.length > 0" class="space-y-2 pt-3 border-t">
          <Label class="text-xs text-muted-foreground">Used Fields in Report</Label>
          <div class="flex flex-wrap gap-1.5">
            <span
              v-for="field in categorizedFields"
              :key="field.name"
              :class="getFieldColorClass(field.type)"
              class="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium border"
              :title="`${field.type === 'computed' ? 'Computed' : field.type === 'ingested' ? 'Ingested' : 'Unknown'} field`"
            >
              {{ field.name }}
            </span>
          </div>

          <div class="flex items-center gap-3 text-xs text-muted-foreground pt-1">
            <div class="flex items-center gap-1">
              <div class="w-2 h-2 rounded-full bg-green-500"></div>
              <span>Computed</span>
            </div>
            <div class="flex items-center gap-1">
              <div class="w-2 h-2 rounded-full bg-yellow-500"></div>
              <span>Ingested</span>
            </div>
          </div>
        </div>

        <hr>

        <!-- Widget Actions (Edit Mode) -->
        <div v-if="isEditMode" class="space-y-3">
          <!-- Chart Widgets - Basic -->
          <div>
            <Label class="text-xs text-muted-foreground mb-2 block">Basic Charts</Label>
            <div class="grid grid-cols-2 gap-2">
              <Button @click="$emit('add-widget', 'chart', 'bar')" variant="outline" size="sm">
                <BarChart3 class="w-4 h-4 mr-1" />
                Bar
              </Button>
              <Button @click="$emit('add-widget', 'chart', 'line')" variant="outline" size="sm" title="Supports single or multiple series">
                <TrendingUp class="w-4 h-4 mr-1" />
                Line
              </Button>
              <Button @click="$emit('add-widget', 'chart', 'donut')" variant="outline" size="sm">
                <PieChart class="w-4 h-4 mr-1" />
                Donut
              </Button>
              <Button @click="$emit('add-widget', 'chart', 'area')" variant="outline" size="sm">
                <AreaChartIcon class="w-4 h-4 mr-1" />
                Area
              </Button>
            </div>
          </div>

          <!-- Chart Widgets - Advanced -->
          <div>
            <Label class="text-xs text-muted-foreground mb-2 block">Advanced Charts</Label>
            <div class="grid grid-cols-2 gap-2">
              <Button @click="$emit('add-widget', 'chart', 'scatter')" variant="outline" size="sm">
                <GitBranch class="w-4 h-4 mr-1" />
                Scatter
              </Button>
              <Button @click="$emit('add-widget', 'chart', 'bubble')" variant="outline" size="sm">
                <Circle class="w-4 h-4 mr-1" />
                Bubble
              </Button>
              <Button @click="$emit('add-widget', 'chart', 'stacked')" variant="outline" size="sm">
                <BarChart2 class="w-4 h-4 mr-1" />
                Stacked
              </Button>
              <Button @click="$emit('add-widget', 'chart', 'waterfall')" variant="outline" size="sm">
                <TrendingDown class="w-4 h-4 mr-1" />
                Waterfall
              </Button>
              <Button @click="$emit('add-widget', 'chart', 'heatmap')" variant="outline" size="sm">
                <Grid3X3 class="w-4 h-4 mr-1" />
                Heatmap
              </Button>
              <Button @click="$emit('add-widget', 'chart', 'sankey')" variant="outline" size="sm">
                <GitMerge class="w-4 h-4 mr-1" />
                Sankey
              </Button>
              <Button @click="$emit('add-widget', 'chart', 'treemap')" variant="outline" size="sm">
                <LayoutGrid class="w-4 h-4 mr-1" />
                Treemap
              </Button>
            </div>
          </div>

          <!-- Other Widgets -->
          <div>
            <Label class="text-xs text-muted-foreground mb-2 block">Other Widgets</Label>
            <div class="grid grid-cols-2 gap-2">
              <Button @click="$emit('add-widget', 'stats')" variant="outline" size="sm">
                <Activity class="w-4 h-4 mr-1" />
                Stats
              </Button>
              <Button @click="$emit('add-widget', 'table')" variant="outline" size="sm">
                <Table2 class="w-4 h-4 mr-1" />
                Table
              </Button>
              <Button @click="$emit('add-widget', 'heading')" variant="outline" size="sm">
                <Heading class="w-4 h-4 mr-1" />
                Heading
              </Button>
              <Button @click="$emit('add-widget', 'divider')" variant="outline" size="sm">
                <Minus class="w-4 h-4 mr-1" />
                Divider
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { GripVertical, ChevronDown, ChevronUp, Lock, Edit, BarChart3, Activity, Table2, Heading, Minus, X, Monitor, TrendingUp, PieChart, AreaChart as AreaChartIcon, LayoutGrid, GitBranch, Circle, BarChart2, TrendingDown, Grid3X3, GitMerge, Save } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Checkbox } from '@/components/ui/checkbox'

const props = defineProps({
  isEditMode: {
    type: Boolean,
    default: false
  },
  reportName: {
    type: String,
    default: ''
  },
  widgetCount: {
    type: Number,
    default: 0
  },
  memory: {
    type: String,
    default: '0'
  },
  selectedWidget: {
    type: Object,
    default: null  // { id, type, config }
  },
  metadata: {
    type: Object,
    default: () => ({ ingested_columns: {}, computed_columns: {} })
  },
  mode: {
    type: String,
    default: 'sidebar', // 'sidebar' or 'floating'
    validator: (value) => ['sidebar', 'floating'].includes(value)
  },
  isOpen: {
    type: Boolean,
    default: false
  },
  widgets: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['toggle-mode', 'add-widget', 'update-widget-config', 'close-widget-config', 'close', 'toggle-display-mode', 'save-report'])

const toolbarRef = ref(null)
const isCollapsed = ref(false)
const isDragging = ref(false)
const position = ref({ x: 20, y: 100 }) // Default position
const dragOffset = ref({ x: 0, y: 0 })
const localConfig = ref({})

// Available fields from metadata
const availableFields = computed(() => {
  return {
    ingested: Object.keys(props.metadata.ingested_columns || {}),
    computed: Object.keys(props.metadata.computed_columns || {})
  }
})

// Currency fields from metadata (with fallback to all fields containing "currency")
const currencyFields = computed(() => {
  console.log('💰 FloatingToolbar: Computing currency fields')
  console.log('  - metadata.currency_fields:', props.metadata.currency_fields)
  console.log('  - metadata.ingested_columns:', Object.keys(props.metadata.ingested_columns || {}))
  console.log('  - metadata.computed_columns:', Object.keys(props.metadata.computed_columns || {}))
  
  // First, check if backend provided currency_fields
  if (props.metadata.currency_fields && props.metadata.currency_fields.length > 0) {
    console.log('  ✅ Using backend currency_fields:', props.metadata.currency_fields)
    return props.metadata.currency_fields
  }
  
  // Fallback: look for fields with "currency" in the name
  const allFields = [
    ...Object.keys(props.metadata.ingested_columns || {}),
    ...Object.keys(props.metadata.computed_columns || {})
  ]
  
  const currencyPattern = /currency|curr|ccy/i
  const detectedFields = allFields.filter(field => currencyPattern.test(field))
  console.log('  ⚠️ Using fallback detection, found:', detectedFields)
  return detectedFields
})

// Extract all fields used in the report
const usedFields = computed(() => {
  const fields = new Set()
  
  props.widgets.forEach(widget => {
    if (widget.config) {
      // Chart and stats widgets
      if (widget.config.x_field) fields.add(widget.config.x_field)
      if (widget.config.y_field) fields.add(widget.config.y_field)
      if (widget.config.currency_field) fields.add(widget.config.currency_field)
      
      // Table widgets - track all columns
      if (widget.config.columns && Array.isArray(widget.config.columns)) {
        widget.config.columns.forEach(col => {
          if (col.field || col.key || col.value) {
            fields.add(col.field || col.key || col.value)
          }
        })
      }
      
      // Any other field references
      if (widget.config.field) fields.add(widget.config.field)
      if (widget.config.fields && Array.isArray(widget.config.fields)) {
        widget.config.fields.forEach(f => fields.add(f))
      }
    }
  })
  
  return Array.from(fields).sort()
})

// Categorize fields
const categorizedFields = computed(() => {
  const ingestedFields = Object.keys(props.metadata.ingested_columns || {})
  const computedFields = Object.keys(props.metadata.computed_columns || {})
  
  return usedFields.value.map(field => ({
    name: field,
    type: computedFields.includes(field) ? 'computed' : 
          ingestedFields.includes(field) ? 'ingested' : 'unknown'
  }))
})

const getFieldColorClass = (type) => {
  if (type === 'computed') return 'bg-green-500/10 text-green-700 dark:text-green-400 border-green-500/20'
  if (type === 'ingested') return 'bg-yellow-500/10 text-yellow-700 dark:text-yellow-400 border-yellow-500/20'
  return 'bg-muted text-muted-foreground'
}

// Watch for selectedWidget changes and update localConfig
watch(() => props.selectedWidget, (newWidget) => {
  if (newWidget && newWidget.config) {
    localConfig.value = { ...newWidget.config }
  } else {
    localConfig.value = {}
  }
}, { immediate: true, deep: true })

const toolbarStyle = computed(() => {
  if (props.mode === 'sidebar') {
    return {
      right: '0',
      top: '0',
      bottom: '0',
      transform: props.isOpen ? 'translateX(0)' : 'translateX(100%)',
      transition: 'transform 0.3s ease'
    }
  } else {
    // Floating mode
    return {
      left: `${position.value.x}px`,
      top: `${position.value.y}px`,
      cursor: isDragging.value ? 'grabbing' : 'grab'
    }
  }
})

const getWidgetIcon = (type) => {
  const icons = {
    chart: BarChart3,
    stats: Activity,
    heading: Heading,
    divider: Minus,
    table: Table2
  }
  return icons[type] || BarChart3
}

const emitConfigUpdate = () => {
  if (props.selectedWidget) {
    emit('update-widget-config', {
      id: props.selectedWidget.id,
      config: { ...localConfig.value }
    })
  }
}

const closeWidgetConfig = () => {
  emit('close-widget-config')
}

const startDrag = (e) => {
  // Only drag if clicking on the header area
  if (!e.target.closest('.cursor-move')) return
  
  isDragging.value = true
  dragOffset.value = {
    x: e.clientX - position.value.x,
    y: e.clientY - position.value.y
  }
  
  document.addEventListener('mousemove', onDrag)
  document.addEventListener('mouseup', stopDrag)
}

const onDrag = (e) => {
  if (!isDragging.value) return
  
  position.value = {
    x: e.clientX - dragOffset.value.x,
    y: e.clientY - dragOffset.value.y
  }
  
  savePosition()
}

const stopDrag = () => {
  isDragging.value = false
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', stopDrag)
}

const toggleCollapsed = () => {
  isCollapsed.value = !isCollapsed.value
  savePosition()
}

const savePosition = () => {
  try {
    localStorage.setItem('moneta_toolbar_position', JSON.stringify({
      x: position.value.x,
      y: position.value.y,
      collapsed: isCollapsed.value
    }))
  } catch (err) {
    console.warn('Failed to save toolbar position:', err)
  }
}

const loadPosition = () => {
  try {
    const saved = localStorage.getItem('moneta_toolbar_position')
    if (saved) {
      const data = JSON.parse(saved)
      position.value = { x: data.x, y: data.y }
      isCollapsed.value = data.collapsed || false
    }
  } catch (err) {
    console.warn('Failed to load toolbar position:', err)
  }
}

onMounted(() => {
  loadPosition()
})

onUnmounted(() => {
  stopDrag()
})
</script>
