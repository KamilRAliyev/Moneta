<template>
  <div class="h-full flex flex-col">
    <!-- Widget Header -->
    <div v-if="isEditMode" class="flex items-center justify-between mb-2 flex-shrink-0">
      <h3 class="text-sm font-medium text-muted-foreground">Table Widget</h3>
      <div class="flex items-center space-x-1">
        <Button
          @click="toggleConfig"
          variant="ghost"
          size="sm"
          title="Configure widget"
        >
          <Settings class="w-4 h-4" />
        </Button>
        <Button
          @click="$emit('remove')"
          variant="ghost"
          size="sm"
          class="text-destructive hover:text-destructive"
          title="Remove widget"
        >
          <X class="w-4 h-4" />
        </Button>
      </div>
    </div>

    <!-- Configuration Panel -->
    <Card v-if="showConfig && isEditMode" class="mb-3 flex-shrink-0">
      <CardContent class="p-4">
        <div class="space-y-3">
          <div>
            <Label class="block text-sm font-medium mb-1">Title</Label>
            <Input v-model="localConfig.title" type="text" placeholder="Transaction Data" />
          </div>
          
          <div>
            <Label class="block text-sm font-medium mb-2">Visible Columns</Label>
            <div class="grid grid-cols-2 gap-2 max-h-40 overflow-y-auto">
              <div v-for="col in availableColumns" :key="col.key" class="flex items-center space-x-2">
                <Checkbox 
                  :checked="localConfig.visibleColumns?.includes(col.key)"
                  @update:checked="(val) => toggleColumn(col.key, val)"
                  :id="`col-${col.key}`"
                />
                <Label :for="`col-${col.key}`" class="text-sm cursor-pointer">
                  {{ col.label }}
                </Label>
              </div>
            </div>
          </div>
          
          <div class="flex items-end justify-end space-x-2">
            <Button @click="cancelConfig" variant="outline" size="sm">
              Cancel
            </Button>
            <Button @click="saveConfig" size="sm">
              Apply
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>

    <!-- Table Display -->
    <div class="flex-1 min-h-0 overflow-auto">
      <div v-if="loading" class="flex items-center justify-center h-full text-muted-foreground text-sm">
        Loading data...
      </div>
      <div v-else-if="error" class="flex items-center justify-center h-full text-destructive text-sm">
        {{ error }}
      </div>
      <div v-else-if="!tableData || tableData.length === 0" class="flex items-center justify-center h-full text-muted-foreground text-sm">
        No data available
      </div>
      <Table v-else class="text-sm">
        <TableHeader>
          <TableRow>
            <TableHead 
              v-for="col in visibleColumnDefs" 
              :key="col.key"
              class="cursor-pointer hover:bg-muted/50"
              @click="sortBy(col.key)"
            >
              <div class="flex items-center space-x-1">
                <span>{{ col.label }}</span>
                <component 
                  v-if="sortColumn === col.key" 
                  :is="sortOrder === 'asc' ? ChevronUp : ChevronDown" 
                  class="w-3 h-3"
                />
              </div>
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          <TableRow v-for="(row, idx) in paginatedData" :key="idx">
            <TableCell v-for="col in visibleColumnDefs" :key="col.key">
              {{ formatCellValue(row[col.key], col.key) }}
            </TableCell>
          </TableRow>
        </TableBody>
      </Table>
    </div>

    <!-- Pagination -->
    <div v-if="tableData && tableData.length > 0" class="flex items-center justify-between pt-2 border-t mt-2 flex-shrink-0">
      <div class="text-xs text-muted-foreground">
        Showing {{ ((currentPage - 1) * pageSize) + 1 }} to {{ Math.min(currentPage * pageSize, tableData.length) }} of {{ tableData.length }} rows
      </div>
      <div class="flex items-center space-x-2">
        <Button 
          @click="currentPage--" 
          :disabled="currentPage === 1"
          variant="outline"
          size="sm"
        >
          <ChevronLeft class="w-4 h-4" />
        </Button>
        <span class="text-xs">Page {{ currentPage }} of {{ totalPages }}</span>
        <Button 
          @click="currentPage++" 
          :disabled="currentPage === totalPages"
          variant="outline"
          size="sm"
        >
          <ChevronRight class="w-4 h-4" />
        </Button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { Settings, X, ChevronUp, ChevronDown, ChevronLeft, ChevronRight } from 'lucide-vue-next'
import axios from '@/api/axios'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Checkbox } from '@/components/ui/checkbox'
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '@/components/ui/table'

const props = defineProps({
  config: {
    type: Object,
    required: true
  },
  isEditMode: {
    type: Boolean,
    default: false
  },
  dateRange: {
    type: Object,
    default: () => ({ from: null, to: null })
  }
})

const emit = defineEmits(['config-updated', 'remove'])

const showConfig = ref(false)
const localConfig = reactive({ 
  title: props.config.title || 'Transactions',
  visibleColumns: props.config.visibleColumns || ['date', 'description', 'category', 'amount']
})

const tableData = ref([])
const loading = ref(false)
const error = ref(null)
const sortColumn = ref('date')
const sortOrder = ref('desc')
const currentPage = ref(1)
const pageSize = 10

const availableColumns = [
  { key: 'date', label: 'Date' },
  { key: 'description', label: 'Description' },
  { key: 'category', label: 'Category' },
  { key: 'amount', label: 'Amount' },
  { key: 'account', label: 'Account' },
  { key: 'type', label: 'Type' },
  { key: 'balance', label: 'Balance' }
]

const visibleColumnDefs = computed(() => {
  return availableColumns.filter(col => localConfig.visibleColumns?.includes(col.key))
})

const sortedData = computed(() => {
  if (!tableData.value) return []
  
  return [...tableData.value].sort((a, b) => {
    const aVal = a[sortColumn.value]
    const bVal = b[sortColumn.value]
    
    if (aVal === bVal) return 0
    if (aVal === null || aVal === undefined) return 1
    if (bVal === null || bVal === undefined) return -1
    
    const comparison = aVal < bVal ? -1 : 1
    return sortOrder.value === 'asc' ? comparison : -comparison
  })
})

const totalPages = computed(() => {
  return Math.ceil(sortedData.value.length / pageSize)
})

const paginatedData = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  const end = start + pageSize
  return sortedData.value.slice(start, end)
})

const toggleConfig = () => {
  showConfig.value = !showConfig.value
}

const toggleColumn = (key, checked) => {
  if (!localConfig.visibleColumns) {
    localConfig.visibleColumns = []
  }
  
  if (checked) {
    if (!localConfig.visibleColumns.includes(key)) {
      localConfig.visibleColumns.push(key)
    }
  } else {
    localConfig.visibleColumns = localConfig.visibleColumns.filter(col => col !== key)
  }
}

const saveConfig = () => {
  emit('config-updated', { ...localConfig })
  showConfig.value = false
}

const cancelConfig = () => {
  Object.assign(localConfig, props.config)
  showConfig.value = false
}

const sortBy = (column) => {
  if (sortColumn.value === column) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortColumn.value = column
    sortOrder.value = 'asc'
  }
}

const formatCellValue = (value, key) => {
  if (value === null || value === undefined) return '-'
  
  if (key === 'amount' || key === 'balance') {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(value)
  }
  
  if (key === 'date') {
    return new Date(value).toLocaleDateString()
  }
  
  return value
}

const fetchData = async () => {
  try {
    loading.value = true
    error.value = null
    
    const params = {
      limit: 100 // Get more rows for table
    }
    
    if (props.dateRange.from) {
      params.date_from = props.dateRange.from
    }
    if (props.dateRange.to) {
      params.date_to = props.dateRange.to
    }
    
    const response = await axios.get('/api/transactions/', { params })
    tableData.value = response.data
    
  } catch (err) {
    console.error('Failed to fetch table data:', err)
    error.value = 'Failed to load data'
    tableData.value = []
  } finally {
    loading.value = false
  }
}

watch(() => props.dateRange, () => {
  fetchData()
}, { deep: true })

onMounted(() => {
  fetchData()
})
</script>

