<script setup>
import { computed, ref, onMounted, nextTick } from 'vue'
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '@/components/ui/table'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Checkbox } from '@/components/ui/checkbox'
import { ChevronUp, ChevronDown, Search, ArrowUpDown } from 'lucide-vue-next'
import { useSettingsStore } from '@/stores/settings.js'

const props = defineProps({
  data: {
    type: Array,
    required: true,
    default: () => []
  },
  columns: {
    type: Array,
    required: true,
    default: () => []
  },
  searchable: {
    type: Boolean,
    default: true
  },
  searchPlaceholder: {
    type: String,
    default: 'Search...'
  },
  searchFields: {
    type: Array,
    default: () => []
  },
  selectable: {
    type: Boolean,
    default: true
  },
  resizable: {
    type: Boolean,
    default: true
  },
  paginated: {
    type: Boolean,
    default: false
  },
  pageSize: {
    type: Number,
    default: 50
  },
  currentPage: {
    type: Number,
    default: 1
  }
})

const emit = defineEmits(['rowClick', 'sort', 'selectionChange', 'pageChange'])

// Store
const settingsStore = useSettingsStore()

// Search functionality
const searchQuery = ref('')
const sortField = ref('')
const sortDirection = ref('asc')

// Selection functionality
const selectedRows = ref(new Set())
const isAllSelected = computed(() => 
  sortedData.value.length > 0 && selectedRows.value.size === sortedData.value.length
)
const isIndeterminate = computed(() => 
  selectedRows.value.size > 0 && selectedRows.value.size < sortedData.value.length
)

// Column resizing
const columnWidths = ref({})
const isResizing = ref(false)
const resizingColumn = ref(null)
const startX = ref(0)
const startWidth = ref(0)

const filteredData = computed(() => {
  // Safety check for data
  if (!props.data || !Array.isArray(props.data)) {
    console.warn('DataTable: props.data is not an array:', props.data)
    return []
  }

  if (!props.searchable || !searchQuery.value) {
    return props.data
  }

  const query = searchQuery.value.toLowerCase()
  return props.data.filter(item => {
    if (props.searchFields.length > 0) {
      return props.searchFields.some(field => {
        const value = getNestedValue(item, field)
        return value && value.toString().toLowerCase().includes(query)
      })
    }
    
    // Search all string values if no specific fields provided
    return Object.values(item).some(value => 
      value && value.toString().toLowerCase().includes(query)
    )
  })
})

const sortedData = computed(() => {
  let data = filteredData.value
  
  if (sortField.value) {
    data = [...data].sort((a, b) => {
      const aValue = getNestedValue(a, sortField.value)
      const bValue = getNestedValue(b, sortField.value)
      
      if (aValue < bValue) {
        return sortDirection.value === 'asc' ? -1 : 1
      }
      if (aValue > bValue) {
        return sortDirection.value === 'asc' ? 1 : -1
      }
      return 0
    })
  }
  
  return data
})

// Pagination - memoized for better performance
const paginatedData = computed(() => {
  if (!props.paginated) {
    return sortedData.value
  }
  
  const start = (props.currentPage - 1) * props.pageSize
  const end = start + props.pageSize
  return sortedData.value.slice(start, end)
})

const totalPages = computed(() => {
  if (!props.paginated) return 1
  return Math.ceil(sortedData.value.length / props.pageSize)
})

const paginationInfo = computed(() => {
  if (!props.paginated) return null
  
  const start = (props.currentPage - 1) * props.pageSize + 1
  const end = Math.min(props.currentPage * props.pageSize, sortedData.value.length)
  const total = sortedData.value.length
  
  return { start, end, total }
})

const handleSort = (field) => {
  if (sortField.value === field) {
    sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortField.value = field
    sortDirection.value = 'asc'
  }
  
  emit('sort', { field: sortField.value, direction: sortDirection.value })
}

const handleRowClick = (item, index) => {
  emit('rowClick', { item, index })
}

const getNestedValue = (obj, path) => {
  return path.split('.').reduce((current, key) => current?.[key], obj)
}

const getSortIcon = (field) => {
  if (sortField.value !== field) return ArrowUpDown
  return sortDirection.value === 'asc' ? ChevronUp : ChevronDown
}

// Selection handlers
const toggleAllSelection = () => {
  if (isAllSelected.value) {
    selectedRows.value.clear()
  } else {
    selectedRows.value.clear()
    sortedData.value.forEach((_, index) => selectedRows.value.add(index))
  }
  emitSelectionChange()
}

const toggleRowSelection = (index) => {
  if (selectedRows.value.has(index)) {
    selectedRows.value.delete(index)
  } else {
    selectedRows.value.add(index)
  }
  emitSelectionChange()
}

const emitSelectionChange = () => {
  const selectedItems = Array.from(selectedRows.value).map(index => sortedData.value[index])
  emit('selectionChange', { selectedRows: selectedItems, selectedIndices: Array.from(selectedRows.value) })
}

// Pagination handlers
const handlePageChange = (page) => {
  emit('pageChange', { page, pageSize: props.pageSize })
}

const handlePageSizeChange = (pageSize) => {
  emit('pageChange', { page: 1, pageSize })
}

// Column resizing handlers
const startResize = (event, columnKey) => {
  if (!props.resizable) return
  
  isResizing.value = true
  resizingColumn.value = columnKey
  startX.value = event.clientX
  startWidth.value = columnWidths.value[columnKey] || settingsStore.getTableColumnWidth(columnKey)
  
  document.addEventListener('mousemove', handleResize)
  document.addEventListener('mouseup', stopResize)
  event.preventDefault()
}

const handleResize = (event) => {
  if (!isResizing.value) return
  
  const deltaX = event.clientX - startX.value
  const newWidth = Math.max(50, startWidth.value + deltaX)
  
  columnWidths.value[resizingColumn.value] = newWidth
  settingsStore.setTableColumnWidth(resizingColumn.value, newWidth)
}

const stopResize = () => {
  isResizing.value = false
  resizingColumn.value = null
  document.removeEventListener('mousemove', handleResize)
  document.removeEventListener('mouseup', stopResize)
}

const getColumnWidth = (columnKey) => {
  return columnWidths.value[columnKey] || settingsStore.getTableColumnWidth(columnKey)
}

// Initialize column widths
onMounted(() => {
  props.columns.forEach(column => {
    if (!columnWidths.value[column.key]) {
      columnWidths.value[column.key] = settingsStore.getTableColumnWidth(column.key, column.defaultWidth || 150)
    }
  })
})
</script>

<template>
  <div class="space-y-4">
    <!-- Search -->
    <div v-if="searchable" class="flex items-center space-x-2">
      <div class="relative flex-1 max-w-sm">
        <Search class="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
        <Input
          v-model="searchQuery"
          :placeholder="searchPlaceholder"
          class="pl-8"
        />
      </div>
    </div>

    <!-- Selection Info -->
    <div v-if="selectable && selectedRows.size > 0" class="flex items-center space-x-2 text-sm text-muted-foreground">
      <span>{{ selectedRows.size }} of {{ sortedData.length }} row(s) selected</span>
    </div>

    <!-- Table -->
    <div class="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <!-- Selection column -->
            <TableHead v-if="selectable" class="w-12">
              <Checkbox
                :checked="isAllSelected"
                :indeterminate="isIndeterminate"
                @update:checked="toggleAllSelection"
              />
            </TableHead>
            
            <!-- Data columns -->
            <TableHead
              v-for="column in columns"
              :key="column.key"
              :class="[
                column.sortable ? 'cursor-pointer hover:bg-muted/50' : '',
                'relative select-none'
              ]"
              :style="{ width: `${getColumnWidth(column.key)}px` }"
              @click="column.sortable ? handleSort(column.key) : null"
            >
              <div class="flex items-center space-x-2">
                <span>{{ column.label }}</span>
                <component
                  v-if="column.sortable"
                  :is="getSortIcon(column.key)"
                  class="h-4 w-4"
                />
              </div>
              
              <!-- Resize handle -->
              <div
                v-if="resizable"
                class="absolute right-0 top-0 h-full w-1 cursor-col-resize hover:bg-primary/50"
                @mousedown="startResize($event, column.key)"
              />
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          <TableRow
            v-for="(item, index) in paginatedData"
            :key="index"
            :class="[
              'cursor-pointer',
              selectedRows.has(index) ? 'bg-muted/50' : ''
            ]"
            @click="handleRowClick(item, index)"
          >
            <!-- Selection cell -->
            <TableCell v-if="selectable" @click.stop="toggleRowSelection(index)">
              <Checkbox :checked="selectedRows.has(index)" />
            </TableCell>
            
            <!-- Data cells -->
            <TableCell
              v-for="column in columns"
              :key="column.key"
              :style="{ width: `${getColumnWidth(column.key)}px` }"
            >
              <slot
                :name="`cell-${column.key}`"
                :value="getNestedValue(item, column.key)"
                :item="item"
                :index="index"
              >
                {{ getNestedValue(item, column.key) }}
              </slot>
            </TableCell>
          </TableRow>
        </TableBody>
      </Table>
    </div>

    <!-- Pagination Controls -->
    <div v-if="paginated && totalPages > 1" class="flex items-center justify-between px-2 py-4">
      <div class="flex items-center space-x-2">
        <p class="text-sm text-muted-foreground">
          Showing {{ paginationInfo?.start || 0 }} to {{ paginationInfo?.end || 0 }} of {{ paginationInfo?.total || 0 }} results
        </p>
      </div>
      
      <div class="flex items-center space-x-2">
        <Button
          variant="outline"
          size="sm"
          :disabled="currentPage <= 1"
          @click="handlePageChange(currentPage - 1)"
        >
          Previous
        </Button>
        
        <span class="text-sm text-muted-foreground">
          Page {{ currentPage }} of {{ totalPages }}
        </span>
        
        <Button
          variant="outline"
          size="sm"
          :disabled="currentPage >= totalPages"
          @click="handlePageChange(currentPage + 1)"
        >
          Next
        </Button>
      </div>
    </div>

    <!-- Empty state -->
    <div v-if="sortedData.length === 0" class="text-center py-8">
      <p class="text-muted-foreground">
        {{ searchQuery ? 'No results found' : 'No data available' }}
      </p>
    </div>
  </div>
</template>