<template>
  <div class="min-h-screen bg-background">
    <!-- Header -->
    <div class="bg-card shadow-sm border-b">
      <div class="px-6 py-4">
        <div class="flex items-center justify-between">
          <h1 class="text-2xl font-bold text-foreground">Reports</h1>
          
          <!-- Top mini-navbar -->
          <div class="flex items-center space-x-4">
            <!-- Report selector dropdown -->
            <Select v-model="selectedReportId" @update:modelValue="loadReport">
              <SelectTrigger class="w-[200px]">
                <SelectValue placeholder="Select a report..." />
              </SelectTrigger>
              <SelectContent>
                <SelectItem 
                  v-for="report in reports" 
                  :key="report.id" 
                  :value="report.id"
                >
                  {{ report.name }}
                </SelectItem>
              </SelectContent>
            </Select>
            
            <!-- Create new report button -->
            <Button @click="createNewReport">
              Create New Report
            </Button>
            
            <!-- Mode toggle -->
            <Button
              @click="toggleMode"
              :variant="isEditMode ? 'default' : 'outline'"
            >
              {{ isEditMode ? 'Edit Mode' : 'View Mode' }}
            </Button>
            
            <!-- Save button (only in edit mode) -->
            <Button
              v-if="isEditMode"
              @click="saveReport"
              :disabled="saving"
              variant="secondary"
            >
              {{ saving ? 'Saving...' : 'Save' }}
            </Button>
          </div>
        </div>
      </div>
    </div>

    <!-- Main content -->
    <div class="p-6">
      <div v-if="loading" class="flex justify-center items-center h-64">
        <div class="text-muted-foreground">Loading...</div>
      </div>
      
      <div v-else-if="!currentReport" class="text-center py-12">
        <div class="text-muted-foreground text-lg">Select or create a report to get started</div>
      </div>
      
      <div v-else class="h-full">
        <!-- Grid Layout -->
        <grid-layout
          v-model:layout="layout"
          :col-num="12"
          :row-height="60"
          :is-draggable="isEditMode"
          :is-resizable="isEditMode"
          :is-mirrored="false"
          :vertical-compact="true"
          :margin="[10, 10]"
          :use-css-transforms="true"
          @layout-updated="onLayoutUpdated"
        >
          <grid-item
            v-for="item in layout"
            :key="item.i"
            :x="item.x"
            :y="item.y"
            :w="item.w"
            :h="item.h"
            :i="item.i"
            :static="!isEditMode"
          >
            <Card class="h-full">
              <CardContent class="p-4 h-full">
                <!-- Chart Widget -->
                <ChartWidget
                  v-if="item.type === 'chart'"
                  :config="item.config"
                  :is-edit-mode="isEditMode"
                  @config-updated="(newConfig) => updateWidgetConfig(item.i, newConfig)"
                  @remove="() => removeWidget(item.i)"
                />
                
                <!-- Dropdown Widget -->
                <DropdownWidget
                  v-else-if="item.type === 'dropdown'"
                  :config="item.config"
                  :is-edit-mode="isEditMode"
                  @config-updated="(newConfig) => updateWidgetConfig(item.i, newConfig)"
                  @value-changed="(value) => onDropdownValueChanged(item.i, value)"
                  @remove="() => removeWidget(item.i)"
                />
              </CardContent>
            </Card>
          </grid-item>
        </grid-layout>
        
        <!-- Add Widget Button (only in edit mode) -->
        <div v-if="isEditMode" class="mt-6 flex justify-center">
          <div class="flex space-x-4">
            <Button @click="addWidget('chart')" variant="default">
              Add Chart
            </Button>
            <Button @click="addWidget('dropdown')" variant="outline">
              Add Filter
            </Button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { GridLayout, GridItem } from 'vue3-grid-layout'
import { reportsApi } from '@/api/reports'
import ChartWidget from '@/components/reports/ChartWidget.vue'
import DropdownWidget from '@/components/reports/DropdownWidget.vue'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

// Reactive data
const reports = ref([])
const currentReport = ref(null)
const selectedReportId = ref('')
const layout = ref([])
const isEditMode = ref(true)
const loading = ref(false)
const saving = ref(false)

// Computed properties
const nextWidgetId = computed(() => {
  return layout.value.length > 0 
    ? Math.max(...layout.value.map(item => parseInt(item.i))) + 1 
    : 1
})

// Methods
const loadReports = async () => {
  try {
    loading.value = true
    console.log('Loading reports...')
    const response = await reportsApi.getReports()
    console.log('Reports response:', response.data)
    reports.value = response.data
    console.log('Reports loaded:', reports.value.length)
  } catch (error) {
    console.error('Failed to load reports:', error)
  } finally {
    loading.value = false
  }
}

const loadReport = async () => {
  if (!selectedReportId.value) {
    currentReport.value = null
    layout.value = []
    return
  }
  
  try {
    loading.value = true
    const response = await reportsApi.getReport(selectedReportId.value)
    currentReport.value = response.data
    
    // Convert widgets to grid layout format
    layout.value = response.data.widgets.map(widget => ({
      i: widget.id,
      x: widget.x,
      y: widget.y,
      w: widget.w,
      h: widget.h,
      type: widget.type,
      config: widget.config
    }))
  } catch (error) {
    console.error('Failed to load report:', error)
  } finally {
    loading.value = false
  }
}

const createNewReport = async () => {
  console.log('Creating new report...')
  const name = prompt('Enter report name:')
  if (!name) {
    console.log('No name provided, cancelling')
    return
  }
  
  try {
    console.log('Calling API to create report:', name)
    const response = await reportsApi.createReport({
      name,
      widgets: []
    })
    
    console.log('Report created:', response.data)
    reports.value.push(response.data)
    selectedReportId.value = response.data.id
    currentReport.value = response.data
    layout.value = []
  } catch (error) {
    console.error('Failed to create report:', error)
  }
}

const saveReport = async () => {
  if (!currentReport.value) return
  
  try {
    saving.value = true
    
    // Convert layout to widgets format
    const widgets = layout.value.map(item => ({
      type: item.type,
      x: item.x,
      y: item.y,
      w: item.w,
      h: item.h,
      config: item.config
    }))
    
    await reportsApi.updateReport(currentReport.value.id, {
      name: currentReport.value.name,
      widgets
    })
    
    // Update local reports list
    const reportIndex = reports.value.findIndex(r => r.id === currentReport.value.id)
    if (reportIndex !== -1) {
      reports.value[reportIndex] = { ...currentReport.value, widgets }
    }
  } catch (error) {
    console.error('Failed to save report:', error)
  } finally {
    saving.value = false
  }
}

const toggleMode = () => {
  isEditMode.value = !isEditMode.value
}

const addWidget = (type) => {
  console.log('Adding widget of type:', type)
  const newWidget = {
    i: nextWidgetId.value.toString(),
    x: 0,
    y: 0,
    w: type === 'chart' ? 6 : 3,
    h: type === 'chart' ? 4 : 2,
    type,
    config: getDefaultConfig(type)
  }
  
  console.log('New widget:', newWidget)
  layout.value.push(newWidget)
  console.log('Layout after adding widget:', layout.value.length)
}

const removeWidget = (widgetId) => {
  const index = layout.value.findIndex(item => item.i === widgetId)
  if (index !== -1) {
    layout.value.splice(index, 1)
  }
}

const updateWidgetConfig = (widgetId, newConfig) => {
  const widget = layout.value.find(item => item.i === widgetId)
  if (widget) {
    widget.config = { ...widget.config, ...newConfig }
  }
}

const onLayoutUpdated = (newLayout) => {
  layout.value = newLayout
}

const onDropdownValueChanged = (widgetId, value) => {
  // Handle dropdown value changes
  // This will trigger chart refreshes for affected widgets
  console.log(`Dropdown ${widgetId} changed to:`, value)
}

const getDefaultConfig = (type) => {
  if (type === 'chart') {
    return {
      type: 'bar',
      title: 'New Chart',
      x_field: 'date',
      y_field: 'amount',
      aggregation: 'sum',
      filters: {}
    }
  } else if (type === 'dropdown') {
    return {
      label: 'Select Filter',
      options: ['Option 1', 'Option 2', 'Option 3'],
      target_widgets: []
    }
  }
  return {}
}

// Lifecycle
onMounted(() => {
  console.log('ReportsView mounted, loading reports...')
  loadReports()
})
</script>

<style>
/* Grid layout styles */
.vue-grid-layout {
  position: relative;
}

.vue-grid-item {
  transition: all 200ms ease;
  transition-property: left, top;
}

.vue-grid-item.vue-grid-placeholder {
  background: #3b82f6;
  opacity: 0.2;
  transition-duration: 100ms;
  z-index: 2;
  -webkit-user-select: none;
  -moz-user-select: none;
  -ms-user-select: none;
  -o-user-select: none;
  user-select: none;
}

.vue-grid-item > .vue-resizable-handle {
  position: absolute;
  width: 20px;
  height: 20px;
  bottom: 0;
  right: 0;
  background: url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNiIgaGVpZ2h0PSI2IiB2aWV3Qm94PSIwIDAgNiA2IiBmaWxsPSJub25lIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPgo8cGF0aCBkPSJtNiA2LTEgMUw0IDVsMS0xIDEtMXoiIGZpbGw9IiM0MDQwNDAiLz4KPC9zdmc+');
  background-position: bottom right;
  padding: 0 3px 3px 0;
  background-repeat: no-repeat;
  background-origin: content-box;
  box-sizing: border-box;
  cursor: se-resize;
}
</style>
