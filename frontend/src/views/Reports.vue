<template>
  <div class="min-h-screen bg-background">
    <!-- Header -->
    <div class="bg-card shadow-sm border-b">
      <div class="px-6 py-4">
        <div class="flex items-center justify-between">
          <h1 class="text-2xl font-bold text-foreground">Reports</h1>
          
          <!-- Top Toolbar -->
          <div class="flex items-center space-x-3">
            <!-- Report Selector -->
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
                  <div class="flex items-center">
                    <Star 
                      v-if="persistence.isDefaultReport(report.id)"
                      class="w-3 h-3 mr-2 fill-amber-500 text-amber-500"
                    />
                    {{ report.name }}
                  </div>
                </SelectItem>
              </SelectContent>
            </Select>
            
            <!-- Default Report Toggle -->
            <Button
              v-if="selectedReportId"
              @click="() => persistence.toggleDefaultReport(selectedReportId)"
              variant="ghost"
              size="icon"
              :title="persistence.isDefaultReport(selectedReportId) ? 'Remove as default' : 'Set as default'"
            >
              <Star 
                :class="[
                  'w-4 h-4',
                  persistence.isDefaultReport(selectedReportId) 
                    ? 'fill-amber-500 text-amber-500' 
                    : 'text-muted-foreground'
                ]"
              />
            </Button>
            
            <!-- Date Range Filter -->
            <DateRangePicker 
              v-if="currentReport"
              :model-value="dateRange"
              :metadata="metadata"
              @update:modelValue="updateDateRange"
            />
            
            <!-- Refresh Data Button -->
            <Button 
              v-if="currentReport"
              @click="refreshAllWidgets" 
              variant="outline"
              :disabled="refreshing"
            >
              <RefreshCw :class="['w-4 h-4 mr-2', { 'animate-spin': refreshing }]" />
              Refresh Data
            </Button>
            
            <!-- Create New Report -->
            <Button @click="createNewReport" variant="outline">
              <Plus class="w-4 h-4 mr-2" />
              New Report
            </Button>
            
            <!-- Lock/Edit Toggle -->
            <Button
              v-if="currentReport"
              @click="toggleMode"
              :variant="isEditMode ? 'default' : 'outline'"
            >
              <component :is="isEditMode ? Edit : Lock" class="w-4 h-4 mr-2" />
              {{ isEditMode ? 'Edit Mode' : 'Lock Mode' }}
            </Button>

            <!-- Resource Usage Monitor -->
            <div v-if="currentReport" class="flex items-center px-3 py-1.5 bg-muted rounded-md text-xs text-muted-foreground">
              <span class="font-mono">{{ resourceUsage.widgetCount }} widgets</span>
              <span class="mx-2">•</span>
              <span class="font-mono">{{ resourceUsage.memory }}MB</span>
              <RefreshCw 
                @click="refreshMemory" 
                class="w-3 h-3 ml-1.5 cursor-pointer hover:text-foreground transition-colors" 
                title="Refresh memory usage"
              />
            </div>

            <!-- Delete Report -->
            <Button
              v-if="currentReport"
              @click="deleteCurrentReport"
              variant="ghost"
              size="icon"
              class="text-destructive hover:text-destructive"
              title="Delete report"
            >
              <Trash2 class="w-4 h-4" />
            </Button>
          </div>
        </div>
      </div>
    </div>

    <!-- Main Content -->
    <div 
      class="p-6 transition-all duration-300"
      :class="{ 'mr-[400px]': persistence.sidebarMode.value === 'sidebar' && sidebarOpen }"
    >
      <!-- Floating Toolbar -->
      <FloatingToolbar
        v-if="currentReport"
        :is-edit-mode="isEditMode"
        :report-name="currentReport.name"
        :widget-count="resourceUsage.widgetCount"
        :memory="resourceUsage.memory"
        :mode="persistence.sidebarMode.value"
        :is-open="sidebarOpen"
        :selected-widget="selectedWidget"
        :metadata="metadata"
        :widgets="layout"
        :global-filters="globalFilters"
        :report-metrics="reportMetrics"
        @toggle-mode="toggleMode"
        @add-widget="addWidget"
        @update-widget-config="updateWidgetConfigFromToolbar"
        @close-widget-config="closeWidgetConfig"
        @close="closeSidebar"
        @toggle-display-mode="toggleDisplayMode"
        @save-report="handleManualSave"
        @update-global-filters="updateGlobalFilters"
      />
      
      <!-- Reopen Sidebar Button (when closed in edit mode) -->
      <Button
        v-if="isEditMode && persistence.sidebarMode.value === 'sidebar' && !sidebarOpen"
        @click="sidebarOpen = true"
        class="fixed top-20 right-4 z-50 shadow-lg"
        size="icon"
        title="Open Controls"
      >
        <PanelRightOpen class="w-4 h-4" />
      </Button>
      
      <!-- Loading State -->
      <div v-if="loading" class="flex justify-center items-center h-64">
        <div class="text-muted-foreground">Loading...</div>
      </div>
      
      <!-- Empty State -->
      <div v-else-if="!currentReport" class="text-center py-12">
        <BarChart3 class="w-16 h-16 mx-auto text-muted-foreground mb-4" />
        <div class="text-muted-foreground text-lg mb-2">No report selected</div>
        <p class="text-sm text-muted-foreground mb-4">Create a new report to get started</p>
        <Button @click="createNewReport">
          <Plus class="w-4 h-4 mr-2" />
          Create Report
        </Button>
      </div>
      
      <!-- Report Grid -->
      <div v-else>
        <!-- Grid Layout -->
        <GridLayout
          v-model:layout="layout"
          :col-num="12"
          :row-height="50"
          :is-draggable="isEditMode"
          :is-resizable="isEditMode"
          :is-mirrored="false"
          :vertical-compact="true"
          :margin="[8, 8]"
          :use-css-transforms="true"
          @layout-updated="onLayoutUpdated"
        >
          <GridItem
            v-for="item in layout"
            :key="item.i"
            :x="item.x"
            :y="item.y"
            :w="item.w"
            :h="item.h"
            :i="item.i"
            :static="!isEditMode"
          >
            <Card class="h-full" :class="{ 'border-2 border-dashed border-primary/30': isEditMode, 'border-0': !isEditMode }">
              <CardContent class="h-full overflow-auto" :class="isEditMode ? 'p-2' : 'p-3'">
                <!-- Chart Widget -->
                <ChartWidget
                  v-if="item.type === 'chart'"
                  :key="`chart-${item.i}`"
                  :config="item.config"
                  :is-edit-mode="isEditMode"
                  :date-range="dateRange"
                  :global-filters="globalFilters"
                  :metadata="metadata"
                  @config-updated="(newConfig) => updateWidgetConfig(item.i, newConfig)"
                  @remove="() => removeWidget(item.i)"
                  @configure="() => openWidgetConfig(item)"
                  @copy="() => copyWidget(item)"
                />
                
                <!-- Stats Widget -->
                <StatsWidget
                  v-else-if="item.type === 'stats'"
                  :key="`stats-${item.i}`"
                  :config="item.config"
                  :is-edit-mode="isEditMode"
                  :date-range="dateRange"
                  :global-filters="globalFilters"
                  :metadata="metadata"
                  @config-updated="(newConfig) => updateWidgetConfig(item.i, newConfig)"
                  @remove="() => removeWidget(item.i)"
                  @configure="() => openWidgetConfig(item)"
                  @copy="() => copyWidget(item)"
                />
                
                <!-- Heading Widget -->
                <HeadingWidget
                  v-else-if="item.type === 'heading'"
                  :config="item.config"
                  :is-edit-mode="isEditMode"
                  @config-updated="(newConfig) => updateWidgetConfig(item.i, newConfig)"
                  @remove="() => removeWidget(item.i)"
                />
                
                <!-- Divider Widget -->
                <DividerWidget
                  v-else-if="item.type === 'divider'"
                  :config="item.config"
                  :is-edit-mode="isEditMode"
                  @config-updated="(newConfig) => updateWidgetConfig(item.i, newConfig)"
                  @remove="() => removeWidget(item.i)"
                />
                
                <!-- Table Widget -->
                <TableWidget
                  v-else-if="item.type === 'table'"
                  :key="`table-${item.i}-${widgetRefreshKey}`"
                  :config="item.config"
                  :is-edit-mode="isEditMode"
                  :date-range="dateRange"
                  @config-updated="(newConfig) => updateWidgetConfig(item.i, newConfig)"
                  @remove="() => removeWidget(item.i)"
                />
                
                <!-- Info Widget -->
                <InfoWidget
                  v-else-if="item.type === 'info'"
                  :is-edit-mode="isEditMode"
                  :report-metrics="reportMetrics"
                  :widget-count="layout.length"
                  :date-range="dateRange"
                  :transaction-count="transactionCount"
                  :metadata="metadata"
                  @remove="() => removeWidget(item.i)"
                />
                
                <!-- Performance Widget -->
                <PerformanceWidget
                  v-else-if="item.type === 'performance'"
                  :is-edit-mode="isEditMode"
                  @remove="() => removeWidget(item.i)"
                />
                
                <!-- Paragraph Widget -->
                <ParagraphWidget
                  v-else-if="item.type === 'paragraph'"
                  :config="item.config"
                  :is-edit-mode="isEditMode"
                  @config-updated="(newConfig) => updateWidgetConfig(item.i, newConfig)"
                  @remove="() => removeWidget(item.i)"
                />
                
                <!-- List Widget -->
                <ListWidget
                  v-else-if="item.type === 'list'"
                  :config="item.config"
                  :is-edit-mode="isEditMode"
                  @config-updated="(newConfig) => updateWidgetConfig(item.i, newConfig)"
                  @remove="() => removeWidget(item.i)"
                />
                
                <!-- Code Widget -->
                <CodeWidget
                  v-else-if="item.type === 'code'"
                  :config="item.config"
                  :is-edit-mode="isEditMode"
                  @config-updated="(newConfig) => updateWidgetConfig(item.i, newConfig)"
                  @remove="() => removeWidget(item.i)"
                />
                
                <!-- Quote Widget -->
                <QuoteWidget
                  v-else-if="item.type === 'quote'"
                  :config="item.config"
                  :is-edit-mode="isEditMode"
                  @config-updated="(newConfig) => updateWidgetConfig(item.i, newConfig)"
                  @remove="() => removeWidget(item.i)"
                />
                
                <!-- Filter Widget -->
                <FilterWidget
                  v-else-if="item.type === 'filter'"
                  :config="item.config"
                  :is-edit-mode="isEditMode"
                  :metadata="metadata"
                  @config-updated="(newConfig) => updateWidgetConfig(item.i, newConfig)"
                  @filter-apply="(filter) => applyFilterFromWidget(filter)"
                  @filter-remove="(filter) => removeFilterFromWidget(filter)"
                  @remove="() => removeWidget(item.i)"
                  @copy="() => copyWidget(item)"
                />
              </CardContent>
            </Card>
          </GridItem>
        </GridLayout>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted, nextTick } from 'vue'
import { GridLayout, GridItem } from 'grid-layout-plus'
import { Plus, Lock, Edit, BarChart3, Heading, Minus, Trash2, Star, RefreshCw, PanelRightOpen } from 'lucide-vue-next'
import { reportsApi } from '@/api/reports'
import ChartWidget from '@/components/reports/ChartWidget.vue'
import HeadingWidget from '@/components/reports/HeadingWidget.vue'
import DividerWidget from '@/components/reports/DividerWidget.vue'
import StatsWidget from '@/components/reports/StatsWidget.vue'
import FilterWidget from '@/components/reports/FilterWidget.vue'
import DateRangePicker from '@/components/reports/DateRangePicker.vue'
import FloatingToolbar from '@/components/reports/FloatingToolbar.vue'
import TableWidget from '@/components/reports/TableWidget.vue'
import InfoWidget from '@/components/reports/InfoWidget.vue'
import PerformanceWidget from '@/components/reports/PerformanceWidget.vue'
import ParagraphWidget from '@/components/reports/ParagraphWidget.vue'
import ListWidget from '@/components/reports/ListWidget.vue'
import CodeWidget from '@/components/reports/CodeWidget.vue'
import QuoteWidget from '@/components/reports/QuoteWidget.vue'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { useDebounceFn } from '@vueuse/core'
import { useReportsPersistence } from '@/composables/useReportsPersistence'
import { useAlert } from '@/composables/useAlert'
import { useReportMetrics } from '@/composables/useReportMetrics'

// State
const reports = ref([])
const currentReport = ref(null)
const selectedReportId = ref('')
const layout = ref([])
const isEditMode = ref(false)
const loading = ref(false)
const saving = ref(false)
const refreshing = ref(false)
const dateRange = ref({ from: null, to: null, dateField: 'date' })
const globalFilters = ref({ fieldFilters: [] })
const metadata = ref({ ingested_columns: {}, computed_columns: {} })
const transactionCount = ref(null)
const widgetRefreshKey = ref(0)
const sidebarOpen = ref(false)
const selectedWidget = ref(null)

// Report metrics tracking
const metricsTracker = useReportMetrics()
const reportMetrics = computed(() => ({
  loadTime: metricsTracker.reportLoadTime.value,
  lastRefresh: metricsTracker.lastRefresh.value,
  apiCallCount: metricsTracker.apiCallCount.value
}))

// Persistence
const persistence = useReportsPersistence()

// Alerts
const alert = useAlert()

// Resource monitoring - using REAL Chrome performance data
const currentMemory = ref('0.0')
const resourceUsage = computed(() => {
  return {
    widgetCount: layout.value.length,
    memory: currentMemory.value
  }
})

// Refresh memory - expensive operation, only on demand
const refreshMemory = () => {
  if (performance.memory) {
    const usedMB = performance.memory.usedJSHeapSize / (1024 * 1024)
    currentMemory.value = usedMB.toFixed(1)
  }
}

// Computed
const nextWidgetId = computed(() => {
  return layout.value.length > 0 
    ? Math.max(...layout.value.map(item => parseInt(item.i))) + 1 
    : 1
})

// Methods
const loadReports = async () => {
  try {
    loading.value = true
    const response = await reportsApi.getReports()
    reports.value = response.data
    
    // Auto-select preferred report if none selected
    if (reports.value.length > 0 && !selectedReportId.value) {
      const preferredId = persistence.getPreferredReportId()
      const reportExists = reports.value.some(r => r.id === preferredId)
      
      selectedReportId.value = reportExists 
        ? preferredId 
        : reports.value[0].id
        
      await loadReport()
    }
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
    metricsTracker.resetMetrics()
    return
  }
  
  try {
    loading.value = true
    metricsTracker.startLoadTracking()
    const response = await reportsApi.getReport(selectedReportId.value)
    
    // IMPORTANT: Restore date filters BEFORE setting currentReport
    // This ensures DateRangePicker receives the correct saved filters when it mounts
    if (response.data.filters && response.data.filters.dateRange) {
      console.log('📅 Restoring saved date filters:', response.data.filters.dateRange)
      dateRange.value = { ...response.data.filters.dateRange }
    } else {
      // Reset to default if no filters saved
      console.log('📅 No saved filters, using defaults')
      dateRange.value = { from: null, to: null, dateField: 'date' }
    }
    
    // Restore global filters
    if (response.data.filters && response.data.filters.globalFilters) {
      console.log('🔍 Restoring saved global filters:', response.data.filters.globalFilters)
      globalFilters.value = { ...response.data.filters.globalFilters }
    } else {
      console.log('🔍 No saved global filters, using defaults')
      globalFilters.value = { fieldFilters: [] }
    }
    
    // Save as last viewed
    persistence.setLastViewedReportId(selectedReportId.value)
    
    // Convert widgets to grid layout format
    layout.value = (response.data.widgets || []).map((widget, index) => ({
      i: widget.id || `${index}`,
      x: widget.x || 0,
      y: widget.y || 0,
      w: widget.w || 6,
      h: widget.h || 4,
      type: widget.type,
      config: widget.config || {}
    }))
    
    // Set currentReport AFTER updating filters
    // This triggers v-if="currentReport" and creates DateRangePicker with correct values
    currentReport.value = response.data
    
    // Wait for next tick to ensure all widgets have mounted, then end tracking
    await nextTick()
    metricsTracker.endLoadTracking()
    
    // Refresh memory once after report is fully loaded (expensive operation)
    refreshMemory()
    
    // Load transaction count
    await loadTransactionCount()
  } catch (error) {
    console.error('Failed to load report:', error)
    alert.error('Failed to load report.')
  } finally {
    loading.value = false
  }
}

const createNewReport = async () => {
  const name = prompt('Enter report name:')
  if (!name) return
  
  try {
    const response = await reportsApi.createReport({
      name,
      widgets: [],
      filters: {
        dateRange: dateRange.value,
        globalFilters: globalFilters.value
      }
    })
    
    reports.value.push(response.data)
    selectedReportId.value = response.data.id
    currentReport.value = response.data
    layout.value = []
    isEditMode.value = true
    
    alert.success('Report created successfully!')
  } catch (error) {
    console.error('Failed to create report:', error)
    alert.error('Failed to create report. Please try again.')
  }
}

const saveReport = async () => {
  if (!currentReport.value) return false
  
  try {
    saving.value = true
    
    // Convert layout to widgets format
    const widgets = layout.value.map(item => ({
      id: item.i,
      type: item.type,
      x: item.x,
      y: item.y,
      w: item.w,
      h: item.h,
      config: item.config
    }))
    
    // Include filters with dateRange and globalFilters
    const filters = {
      dateRange: dateRange.value,
      globalFilters: globalFilters.value
    }
    
    await reportsApi.updateReport(currentReport.value.id, {
      name: currentReport.value.name,
      widgets,
      filters
    })
    
    // Update local reports list
    const reportIndex = reports.value.findIndex(r => r.id === currentReport.value.id)
    if (reportIndex !== -1) {
      reports.value[reportIndex] = { ...currentReport.value, widgets, filters }
    }
    
    alert.success('Report saved successfully!')
    return true
  } catch (error) {
    console.error('Failed to save report:', error)
    alert.error('Failed to save report. Please try again.')
    return false
  } finally {
    saving.value = false
  }
}

const deleteCurrentReport = async () => {
  if (!currentReport.value) return
  
  const confirmed = confirm(`Are you sure you want to delete "${currentReport.value.name}"?`)
  if (!confirmed) return
  
  try {
    await reportsApi.deleteReport(currentReport.value.id)
    
    // Remove from list
    reports.value = reports.value.filter(r => r.id !== currentReport.value.id)
    
    // Clear current report
    currentReport.value = null
    selectedReportId.value = ''
    layout.value = []
  } catch (error) {
    console.error('Failed to delete report:', error)
    alert('Failed to delete report. Please try again.')
  }
}

const toggleMode = async () => {
  // If leaving edit mode, save the report automatically
  if (isEditMode.value && currentReport.value) {
    const saved = await saveReport()
    if (!saved) {
      // Don't toggle mode if save failed
      return
    }
  }
  isEditMode.value = !isEditMode.value
  
  // Auto-open sidebar when entering edit mode (only if in sidebar mode)
  if (isEditMode.value && persistence.sidebarMode.value === 'sidebar') {
    sidebarOpen.value = true
  } else if (!isEditMode.value) {
    sidebarOpen.value = false
    selectedWidget.value = null
  }
}

const addWidget = (type, chartType = null) => {
  const widthMap = {
    chart: 6,
    stats: 3,
    table: 12,
    heading: 12,
    divider: 12,
    info: 4,
    performance: 4,
    paragraph: 6,
    list: 4,
    code: 6,
    quote: 6,
    filter: 4
  }
  
  const heightMap = {
    chart: 4,
    stats: 3,
    table: 6,
    heading: 1,
    divider: 1,
    info: 4,
    performance: 5,
    paragraph: 3,
    list: 4,
    code: 4,
    quote: 3,
    filter: 3
  }
  
  const newWidget = {
    i: nextWidgetId.value.toString(),
    x: 0,
    y: layout.value.length > 0 ? Math.max(...layout.value.map(item => item.y + item.h)) : 0,
    w: widthMap[type] || 6,
    h: heightMap[type] || 4,
    type,
    config: getDefaultConfig(type, chartType)
  }
  
  layout.value.push(newWidget)
  autoSave()
}

const removeWidget = (widgetId) => {
  const index = layout.value.findIndex(item => item.i === widgetId)
  if (index !== -1) {
    layout.value.splice(index, 1)
    autoSave()
  }
}

const copyWidget = (widget) => {
  // Create a deep copy of the widget
  const newWidget = {
    ...widget,
    i: `widget-${Date.now()}`,
    config: { ...widget.config },
    // Offset position slightly so the copy doesn't overlap exactly
    x: (widget.x + widget.w) % 12, // Wrap around if exceeds grid width
    y: widget.y + (widget.x + widget.w >= 12 ? widget.h : 0) // Move down if wrapping
  }
  layout.value.push(newWidget)
  autoSave()
}

const updateWidgetConfig = (widgetId, newConfig) => {
  const widget = layout.value.find(item => item.i === widgetId)
  if (widget) {
    widget.config = { ...widget.config, ...newConfig }
    autoSave()
  }
}

// Apply filter from widget to global filters
const applyFilterFromWidget = (filter) => {
  // Ensure globalFilters has fieldFilters array
  if (!globalFilters.value.fieldFilters) {
    globalFilters.value.fieldFilters = []
  }
  
  // Check if filter already exists
  const existingIndex = globalFilters.value.fieldFilters.findIndex(
    f => f.field === filter.field && f.operator === filter.operator && f.value === filter.value
  )
  
  // If not exists, add it
  if (existingIndex === -1) {
    globalFilters.value.fieldFilters.push(filter)
  }
  
  // Save and trigger widget refresh
  autoSave()
  widgetRefreshKey.value++
}

// Remove filter from global filters
const removeFilterFromWidget = (filter) => {
  if (!globalFilters.value.fieldFilters) {
    return
  }
  
  // Find and remove the filter
  const index = globalFilters.value.fieldFilters.findIndex(
    f => f.field === filter.field && f.operator === filter.operator && f.value === filter.value
  )
  
  if (index !== -1) {
    globalFilters.value.fieldFilters.splice(index, 1)
  }
  
  // Save and trigger widget refresh
  autoSave()
  widgetRefreshKey.value++
}

const updateWidgetConfigFromToolbar = ({ id, config }) => {
  const widget = layout.value.find(item => item.i === id)
  if (widget) {
    widget.config = { ...widget.config, ...config }
    autoSave()
  }
}

const closeWidgetConfig = () => {
  selectedWidget.value = null
}

const closeSidebar = () => {
  sidebarOpen.value = false
  selectedWidget.value = null
}

const toggleDisplayMode = () => {
  const newMode = persistence.sidebarMode.value === 'sidebar' ? 'floating' : 'sidebar'
  persistence.setSidebarMode(newMode)
  console.log('🔄 Switched display mode to:', newMode)
  
  if (newMode === 'floating') {
    sidebarOpen.value = false
  } else if (isEditMode.value) {
    sidebarOpen.value = true
  }
}

const handleManualSave = async () => {
  const saved = await saveReport()
  if (saved) {
    // Switch to lock mode and close sidebar
    isEditMode.value = false
    sidebarOpen.value = false
    selectedWidget.value = null
  }
}

const openWidgetConfig = (item) => {
  console.log('🔧 Opening widget config for:', item.i, item.type)
  selectedWidget.value = {
    id: item.i,
    type: item.type,
    config: item.config
  }
  sidebarOpen.value = true
}

const onLayoutUpdated = (newLayout) => {
  layout.value = newLayout
  autoSave()
}

const getDefaultConfig = (type, chartType = null) => {
  if (type === 'chart') {
    const chartTitles = {
      bar: 'Bar Chart',
      line: 'Line Chart',
      donut: 'Donut Chart',
      area: 'Area Chart',
      treemap: 'Treemap',
      multiline: 'Multi-Line Chart'
    }
    
    return {
      title: chartTitles[chartType] || 'New Chart',
      chartType: chartType || 'bar',
      x_field: 'category',
      y_field: 'amount',
      aggregation: 'sum'
    }
  } else if (type === 'stats') {
    return {
      label: 'Total',
      y_field: 'amount',
      aggregation: 'sum',
      colorTheme: 'default'
    }
  } else if (type === 'table') {
    return {
      title: 'Transactions',
      visibleColumns: ['date', 'description', 'category', 'amount']
    }
  } else if (type === 'heading') {
    return {
      text: 'Heading',
      level: 'h2'
    }
  } else if (type === 'divider') {
    return {
      thickness: 'thin'
    }
  } else if (type === 'info') {
    return {}
  } else if (type === 'performance') {
    return {}
  } else if (type === 'paragraph') {
    return {
      text: 'Enter your text here...',
      fontSize: 'base',
      align: 'left'
    }
  } else if (type === 'list') {
    return {
      listType: 'bullet',
      items: ['Item 1', 'Item 2', 'Item 3']
    }
  } else if (type === 'code') {
    return {
      code: '// Enter your code here...',
      language: 'javascript'
    }
  } else if (type === 'quote') {
    return {
      quote: 'Enter your quote here...',
      author: ''
    }
  } else if (type === 'filter') {
    const filterWidgets = layout.value.filter(w => w.type === 'filter')
    return {
      label: `Quick Filter ${filterWidgets.length + 1}`,
      field: 'computed_month',
      operator: 'equals',
      value: '',
      applied: false
    }
  }
  return {}
}

// Auto-save with debounce
const autoSave = useDebounceFn(() => {
  if (isEditMode.value && currentReport.value) {
    saveReport()
  }
}, 1000)

const updateDateRange = async (newRange) => {
  console.log('=== DATE RANGE UPDATE ===')
  console.log('Old range:', dateRange.value)
  console.log('New range:', newRange)
  
  // Update the ref with a completely new object to trigger reactivity
  dateRange.value = { ...newRange }
  
  console.log('Updated range:', dateRange.value)
  
  // Wait for Vue to finish updating the DOM
  await nextTick()
  await nextTick() // Double nextTick to ensure complete processing
  
  console.log('Auto-refreshing widgets...')
  
  // Now trigger refresh - widgets will get the updated dateRange
  widgetRefreshKey.value++
  
  // Reload transaction count with new date range
  await loadTransactionCount()
  
  console.log('=== END DATE RANGE UPDATE ===')
}

const updateGlobalFilters = async (newFilters) => {
  console.log('=== GLOBAL FILTERS UPDATE ===')
  console.log('Old filters:', globalFilters.value)
  console.log('New filters:', newFilters)
  
  // Update the ref with a completely new object to trigger reactivity
  globalFilters.value = { ...newFilters }
  
  console.log('Updated filters:', globalFilters.value)
  
  // Wait for Vue to finish updating the DOM
  await nextTick()
  await nextTick()
  
  console.log('Auto-refreshing widgets with filters...')
  
  // Trigger refresh - widgets will get the updated globalFilters
  widgetRefreshKey.value++
  
  // Reload transaction count with new filters
  await loadTransactionCount()
  
  console.log('=== END GLOBAL FILTERS UPDATE ===')
}

const refreshAllWidgets = async () => {
  refreshing.value = true
  console.log('Manually refreshing all widgets with date range:', dateRange.value)
  
  // Update last refresh timestamp
  metricsTracker.updateLastRefresh()
  
  // Force re-render all widgets by incrementing the key
  widgetRefreshKey.value++
  
  // Wait a bit for the refresh to complete
  await new Promise(resolve => setTimeout(resolve, 500))
  refreshing.value = false
  
  // Reload transaction count
  await loadTransactionCount()
}

const loadMetadata = async () => {
  try {
    const response = await reportsApi.getTransactionMetadata()
    metadata.value = response.data
  } catch (error) {
    console.error('Failed to load metadata:', error)
  }
}

const loadTransactionCount = async () => {
  try {
    console.log('🔢 Loading transaction count with filters:', {
      dateRange: dateRange.value,
      globalFilters: globalFilters.value
    })
    
    // Fetch transaction count from API with current filters
    const params = {}
    if (dateRange.value.from) params.date_from = dateRange.value.from
    if (dateRange.value.to) params.date_to = dateRange.value.to
    if (dateRange.value.dateField) params.date_field = dateRange.value.dateField
    
    // Add global filters if any
    if (globalFilters.value?.fieldFilters && globalFilters.value.fieldFilters.length > 0) {
      globalFilters.value.fieldFilters.forEach((filter, index) => {
        // Check for field and that value is not null/undefined (0 is a valid value!)
        if (filter.field && filter.value !== null && filter.value !== undefined) {
          params[`filter_${index}_field`] = filter.field
          params[`filter_${index}_operator`] = filter.operator || 'equals'
          params[`filter_${index}_value`] = filter.value
          params[`filter_${index}_connector`] = filter.connector || 'AND'
        }
      })
    }
    
    console.log('🔢 Transaction count API params:', JSON.stringify(params))
    
    // Use a common field to group by and then sum all counts
    // Using 'merchant' as it exists in most transactions
    const response = await reportsApi.getAggregatedData({
      ...params,
      x_field: 'merchant',
      y_field: 'merchant',
      aggregation: 'count'
    })
    
    console.log('🔢 Transaction count response:', response.data)
    
    // The response includes a filtered_records count - use that if available
    if (response.data && typeof response.data.filtered_records === 'number') {
      transactionCount.value = response.data.filtered_records
      console.log('🔢 Using filtered_records count:', transactionCount.value)
    } else if (response.data && response.data.values && Array.isArray(response.data.values)) {
      // Fallback: Sum all the counts from each group
      transactionCount.value = response.data.values.reduce((sum, count) => sum + count, 0)
      console.log('🔢 Summed from values:', transactionCount.value)
    } else {
      console.warn('🔢 Unexpected response format:', response.data)
      transactionCount.value = 0
    }
  } catch (error) {
    console.error('Failed to load transaction count:', error)
    transactionCount.value = 0
  }
}

// Watch dateRange for debugging
watch(dateRange, (newVal) => {
  console.log('🔍 Reports.vue: dateRange watch triggered!', newVal)
  console.log('🔍 Current widgets will get:', newVal)
})

// Lifecycle
onMounted(async () => {
  await loadMetadata()
  await loadReports()
})
</script>

<style>
/* Grid layout styles */
.vue-grid-layout {
  position: relative;
  transition: height 200ms ease;
}

.vue-grid-item {
  transition: all 200ms ease;
  transition-property: left, top, right, bottom;
}

.vue-grid-item.resizing {
  opacity: 0.9;
}

.vue-grid-item.static {
  background: transparent;
}

.vue-grid-item .vue-resizable-handle {
  position: absolute;
  width: 20px;
  height: 20px;
}

.vue-grid-item .vue-resizable-handle::after {
  content: "";
  position: absolute;
  right: 3px;
  bottom: 3px;
  width: 8px;
  height: 8px;
  border-right: 2px solid hsl(var(--border));
  border-bottom: 2px solid hsl(var(--border));
}

.vue-grid-item > .vue-resizable-handle {
  position: absolute;
  width: 20px;
  height: 20px;
  bottom: 0;
  right: 0;
  cursor: se-resize;
}

.vue-grid-item.vue-grid-placeholder {
  background: hsl(var(--primary) / 0.2);
  opacity: 0.2;
  transition-duration: 100ms;
  z-index: 2;
  border-radius: 4px;
}
</style>
