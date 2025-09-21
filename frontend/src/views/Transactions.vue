<script setup>
import { ref, computed, onMounted, watch, onUnmounted } from 'vue'
import { useTransactionsStore } from '@/stores/transactions.js'
import { useSettingsStore } from '@/stores/settings.js'
import { useAlert } from '@/composables/useAlert.js'
import DataTable from '@/components/DataTable.vue'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { ChevronDown, Settings, RefreshCw } from 'lucide-vue-next'

const transactionsStore = useTransactionsStore()
const settingsStore = useSettingsStore()
const { success, error, warning } = useAlert()

// State
const metadata = ref({ ingested_columns: {}, computed_columns: {} })
const selectedColumns = computed({
  get: () => settingsStore.selectedColumns,
  set: (value) => settingsStore.setSelectedColumns(value)
})
const filteredTransactions = ref([])
const totalCount = ref(0)
const currentPage = ref(1)
const pageSize = ref(100)
const loading = ref(false)
const metadataLoading = ref(false)
const showColumnDropdown = ref(false)
const showDebugInfo = ref(false)
const showJsonModal = ref(false)
const selectedTransactionJson = ref(null)

// Computed
const availableColumns = computed(() => {
  const columns = []
  
  // Add ingested columns
  if (metadata.value.ingested_columns && Object.keys(metadata.value.ingested_columns).length > 0) {
    columns.push({
      category: 'ingested',
      label: 'Ingested Columns',
      columns: Object.keys(metadata.value.ingested_columns).map(col => ({
        key: col,
        label: col,
        type: 'ingested'
      }))
    })
  }
  
  // Add computed columns
  if (metadata.value.computed_columns && Object.keys(metadata.value.computed_columns).length > 0) {
    columns.push({
      category: 'computed',
      label: 'Computed Columns',
      columns: Object.keys(metadata.value.computed_columns).map(col => ({
        key: col,
        label: col,
        type: 'computed'
      }))
    })
  }
  
  return columns
})

const tableColumns = computed(() => {
  const cols = [
    { key: 'id', label: 'ID', sortable: true, defaultWidth: 200 },
    { key: 'statement_id', label: 'Statement ID', sortable: true, defaultWidth: 200 },
    { key: 'created_at', label: 'Created', sortable: true, defaultWidth: 150 },
    { key: 'actions', label: 'Actions', sortable: false, defaultWidth: 100 }
  ]
  
  // Add selected columns
  selectedColumns.value.forEach(colKey => {
    const col = availableColumns.value
      .flatMap(cat => cat.columns)
      .find(c => c.key === colKey)
    
    if (col) {
      cols.push({
        key: colKey,
        label: col.label,
        sortable: true,
        defaultWidth: 150
      })
    }
  })
  
  return cols
})

const tableData = computed(() => {
  if (!filteredTransactions.value || filteredTransactions.value.length === 0) {
    return []
  }
  
  return filteredTransactions.value.map(transaction => {
    const row = {
      id: transaction.id,
      statement_id: transaction.statement_id,
      created_at: new Date(transaction.created_at).toLocaleDateString()
    }
    
    // Add selected column data
    selectedColumns.value.forEach(colKey => {
      if (transaction.ingested_content && transaction.ingested_content[colKey] !== undefined) {
        row[colKey] = transaction.ingested_content[colKey]
      } else if (transaction.computed_content && transaction.computed_content[colKey] !== undefined) {
        row[colKey] = transaction.computed_content[colKey]
      } else {
        row[colKey] = '-'
      }
    })
    
    // Add actions column
    row.actions = transaction.id
    
    return row
  })
})

const hasSelectedColumns = computed(() => selectedColumns.value.length > 0)

// Methods
async function loadMetadata() {
  metadataLoading.value = true
  try {
    metadata.value = await transactionsStore.fetchTransactionMetadata()
    success('Metadata loaded successfully')
  } catch (err) {
    error('Failed to load metadata')
    console.error('Metadata load error:', err)
  } finally {
    metadataLoading.value = false
  }
}

async function loadTransactions() {
  if (!hasSelectedColumns.value) {
    // Load 100 transactions by default with basic columns
    const basicColumns = ['amount', 'date', 'description'].filter(col => 
      availableColumns.value.some(cat => cat.columns.some(c => c.key === col))
    )
    
    if (basicColumns.length === 0) {
      // If no basic columns exist, select first available column
      const firstColumn = availableColumns.value[0]?.columns[0]?.key
      if (firstColumn) {
        settingsStore.setSelectedColumns([firstColumn])
      }
    } else {
      settingsStore.setSelectedColumns(basicColumns)
    }
  }
  
  loading.value = true
  try {
    const skip = (currentPage.value - 1) * pageSize.value
    const columns = selectedColumns.value.join(',')
    
    const response = await transactionsStore.fetchFilteredTransactions({
      columns,
      skip,
      limit: pageSize.value
    })
    
    filteredTransactions.value = response.transactions
    totalCount.value = response.total
    
    success(`Loaded ${response.transactions.length} transactions`)
  } catch (err) {
    error('Failed to load transactions')
    console.error('Transaction load error:', err)
  } finally {
    loading.value = false
  }
}

function toggleColumn(columnKey) {
  const currentColumns = [...selectedColumns.value]
  const index = currentColumns.indexOf(columnKey)
  if (index > -1) {
    currentColumns.splice(index, 1)
  } else {
    currentColumns.push(columnKey)
  }
  settingsStore.setSelectedColumns(currentColumns)
}

function toggleCategory(category) {
  const categoryColumns = availableColumns.value
    .find(cat => cat.category === category)
    .columns.map(col => col.key)
  
  const currentColumns = [...selectedColumns.value]
  const allSelected = categoryColumns.every(col => currentColumns.includes(col))
  
  if (allSelected) {
    // Deselect all columns in this category
    const newColumns = currentColumns.filter(col => !categoryColumns.includes(col))
    settingsStore.setSelectedColumns(newColumns)
  } else {
    // Select all columns in this category
    categoryColumns.forEach(col => {
      if (!currentColumns.includes(col)) {
        currentColumns.push(col)
      }
    })
    settingsStore.setSelectedColumns(currentColumns)
  }
}

function isCategorySelected(category) {
  const categoryColumns = availableColumns.value
    .find(cat => cat.category === category)
    .columns.map(col => col.key)
  
  return categoryColumns.every(col => selectedColumns.value.includes(col))
}

function isCategoryPartiallySelected(category) {
  const categoryColumns = availableColumns.value
    .find(cat => cat.category === category)
    .columns.map(col => col.key)
  
  const selectedCount = categoryColumns.filter(col => selectedColumns.value.includes(col)).length
  return selectedCount > 0 && selectedCount < categoryColumns.length
}

function clearSelection() {
  settingsStore.setSelectedColumns([])
  filteredTransactions.value = []
  totalCount.value = 0
}

function refreshData() {
  loadTransactions()
}

async function showTransactionJson(transactionId) {
  try {
    loading.value = true
    const transaction = await transactionsStore.fetchTransaction(transactionId)
    selectedTransactionJson.value = transaction
    showJsonModal.value = true
  } catch (err) {
    error('Failed to load transaction details')
    console.error('Transaction load error:', err)
  } finally {
    loading.value = false
  }
}

function closeJsonModal() {
  showJsonModal.value = false
  selectedTransactionJson.value = null
}

async function refreshTransactions() {
  loading.value = true
  try {
    await loadTransactions()
    success('Transactions refreshed successfully')
  } catch (err) {
    error('Failed to refresh transactions')
    console.error('Refresh error:', err)
  } finally {
    loading.value = false
  }
}

async function removeAllTransactions() {
  if (!confirm('Are you sure you want to remove ALL transactions? This action cannot be undone.')) {
    return
  }
  
  if (!confirm('This will permanently delete all transaction data. Are you absolutely sure?')) {
    return
  }
  
  loading.value = true
  try {
    const response = await fetch('/api/transactions/', {
      method: 'DELETE'
    })
    
    if (!response.ok) {
      throw new Error('Failed to remove transactions')
    }
    
    const result = await response.json()
    success(`Successfully removed ${result.removed_count || 'all'} transactions`)
    
    // Clear local data
    filteredTransactions.value = []
    totalCount.value = 0
    
    // Refresh metadata to update column information
    await loadMetadata()
    
  } catch (err) {
    error('Failed to remove transactions')
    console.error('Remove transactions error:', err)
  } finally {
    loading.value = false
  }
}

// Close dropdown when clicking outside
function handleClickOutside(event) {
  const dropdown = event.target.closest('.dropdown-container')
  if (!dropdown && showColumnDropdown.value) {
    showColumnDropdown.value = false
  }
}

// Watchers
watch(selectedColumns, () => {
  if (hasSelectedColumns.value) {
    currentPage.value = 1
    loadTransactions()
  } else {
    filteredTransactions.value = []
    totalCount.value = 0
  }
}, { deep: true })

watch(currentPage, () => {
  if (hasSelectedColumns.value) {
    loadTransactions()
  }
})

watch(pageSize, () => {
  if (hasSelectedColumns.value) {
    currentPage.value = 1
    loadTransactions()
  }
})

// Lifecycle
onMounted(async () => {
  // Add event listener for clicking outside
  document.addEventListener('click', handleClickOutside)
  
  await loadMetadata()
  // Load 100 transactions by default after metadata is loaded
  await loadTransactions()
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<template>
  <div class="container mx-auto p-6 space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-3xl font-bold">Transactions</h1>
        <p class="text-muted-foreground">
          View and manage your transaction data with custom column selection
        </p>
      </div>
      <div class="flex items-center gap-2">
        <Button 
          @click="loadMetadata" 
          :disabled="metadataLoading"
          variant="outline"
          size="sm"
        >
          <RefreshCw :class="['h-4 w-4 mr-2', { 'animate-spin': metadataLoading }]" />
          Refresh Metadata
        </Button>
        <Button 
          @click="refreshTransactions" 
          :disabled="loading"
          variant="outline"
          size="sm"
        >
          <RefreshCw :class="['h-4 w-4 mr-2', { 'animate-spin': loading }]" />
          Refresh
        </Button>
        <Button 
          @click="removeAllTransactions" 
          :disabled="loading || totalCount === 0"
          variant="destructive"
          size="sm"
        >
          <Settings class="h-4 w-4 mr-2" />
          Remove All Transactions
        </Button>
        <Button 
          @click="showDebugInfo = !showDebugInfo"
          variant="outline"
          size="sm"
        >
          <Settings class="h-4 w-4 mr-2" />
          {{ showDebugInfo ? 'Hide' : 'Show' }} Debug
        </Button>
        <div class="relative dropdown-container">
          <Button 
            @click="showColumnDropdown = !showColumnDropdown"
            variant="outline"
            size="sm"
            class="min-w-[150px] justify-between"
          >
            <div class="flex items-center">
              <Settings class="h-4 w-4 mr-2" />
              <span>Columns ({{ selectedColumns.length }})</span>
            </div>
            <ChevronDown :class="['h-4 w-4 ml-2 transition-transform', showColumnDropdown ? 'rotate-180' : '']" />
          </Button>
          
          <!-- Dropdown Menu -->
          <div 
            v-if="showColumnDropdown"
            class="absolute right-0 top-full mt-2 w-80 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg z-50 max-h-96 overflow-hidden"
          >
            <!-- Header -->
            <div class="px-4 py-3 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900">
              <div class="flex items-center justify-between">
                <h3 class="text-sm font-semibold text-gray-900 dark:text-gray-100">Select Columns</h3>
                <Button @click="showColumnDropdown = false" variant="ghost" size="sm" class="h-6 w-6 p-0">
                  <span class="text-lg leading-none">&times;</span>
                </Button>
              </div>
              <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Choose which columns to display in the table
              </p>
            </div>

            <!-- Content -->
            <div class="max-h-80 overflow-y-auto">
              <div class="p-2">
                <!-- Category Selection -->
                <div v-for="category in availableColumns" :key="category.category" class="mb-4">
                  <!-- Category Header -->
                  <div class="flex items-center px-2 py-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer"
                       @click="toggleCategory(category.category)">
                    <Checkbox
                      :id="`category-${category.category}`"
                      :checked="isCategorySelected(category.category)"
                      :indeterminate="isCategoryPartiallySelected(category.category)"
                      @update:checked="toggleCategory(category.category)"
                      @click.stop
                    />
                    <label 
                      :for="`category-${category.category}`"
                      class="ml-3 text-sm font-medium text-gray-900 dark:text-gray-100 cursor-pointer flex-1"
                    >
                      {{ category.label }}
                    </label>
                    <Badge variant="secondary" class="ml-2 text-xs">
                      {{ category.columns.length }}
                    </Badge>
                  </div>
                  
                  <!-- Individual Column Selection -->
                  <div class="ml-6 mt-2 space-y-1">
                    <div 
                      v-for="column in category.columns" 
                      :key="column.key"
                      class="flex items-center px-2 py-1.5 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer"
                      @click="toggleColumn(column.key)"
                    >
                      <Checkbox
                        :id="`column-${column.key}`"
                        :checked="selectedColumns.includes(column.key)"
                        @update:checked="toggleColumn(column.key)"
                        @click.stop
                      />
                      <label 
                        :for="`column-${column.key}`"
                        class="ml-3 text-xs text-gray-600 dark:text-gray-300 cursor-pointer flex-1"
                      >
                        {{ column.label }}
                      </label>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Footer -->
            <div class="px-4 py-3 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900">
              <div class="flex items-center justify-between">
                <div class="text-xs text-gray-500 dark:text-gray-400">
                  {{ selectedColumns.length }} column{{ selectedColumns.length !== 1 ? 's' : '' }} selected
                </div>
                <div class="flex gap-2">
                  <Button @click="clearSelection" variant="outline" size="sm" class="text-xs">
                    Clear All
                  </Button>
                  <Button @click="showColumnDropdown = false" size="sm" class="text-xs">
                    Done
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>


    <!-- Pagination Controls -->
    <div v-if="hasSelectedColumns" class="flex items-center justify-between">
      <div class="flex items-center gap-4">
        <div class="flex items-center gap-2">
          <label for="pageSize" class="text-sm font-medium">Rows per page:</label>
          <Select v-model="pageSize">
            <SelectTrigger class="w-20">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem :value="25">25</SelectItem>
              <SelectItem :value="50">50</SelectItem>
              <SelectItem :value="100">100</SelectItem>
              <SelectItem :value="200">200</SelectItem>
              <SelectItem :value="500">500</SelectItem>
              <SelectItem :value="1000">1000</SelectItem>
              <SelectItem :value="2000">2000</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div class="text-sm text-muted-foreground">
          Showing {{ ((currentPage - 1) * pageSize) + 1 }} to {{ Math.min(currentPage * pageSize, totalCount) }} of {{ totalCount }} transactions
        </div>
      </div>
      
      <div class="flex items-center gap-2">
        <Button 
          @click="currentPage = Math.max(1, currentPage - 1)"
          :disabled="currentPage <= 1"
          variant="outline"
          size="sm"
        >
          Previous
        </Button>
        <span class="text-sm">
          Page {{ currentPage }} of {{ Math.ceil(totalCount / pageSize) }}
        </span>
        <Button 
          @click="currentPage = Math.min(Math.ceil(totalCount / pageSize), currentPage + 1)"
          :disabled="currentPage >= Math.ceil(totalCount / pageSize)"
          variant="outline"
          size="sm"
        >
          Next
        </Button>
      </div>
    </div>

    <!-- Debug Info -->
    <div v-if="showDebugInfo" class="mb-4 p-4 bg-gray-100 dark:bg-gray-800 rounded-lg border text-sm">
      <div class="flex items-center justify-between mb-3">
        <h3 class="font-semibold text-gray-900 dark:text-gray-100">Debug Information</h3>
        <Button @click="showDebugInfo = false" variant="ghost" size="sm" class="h-6 w-6 p-0">
          <span class="text-lg leading-none">&times;</span>
        </Button>
      </div>
      <div class="grid grid-cols-2 gap-4 text-gray-600 dark:text-gray-300">
        <div>
          <p><strong>Has Selected Columns:</strong> {{ hasSelectedColumns }}</p>
          <p><strong>Selected Columns:</strong> {{ selectedColumns.length }} ({{ selectedColumns.join(', ') }})</p>
          <p><strong>Filtered Transactions:</strong> {{ filteredTransactions.length }}</p>
          <p><strong>Table Data:</strong> {{ tableData.length }} rows</p>
        </div>
        <div>
          <p><strong>Table Columns:</strong> {{ tableColumns.length }} columns</p>
          <p><strong>Loading:</strong> {{ loading }}</p>
          <p><strong>Available Columns:</strong> {{ availableColumns.length }} categories</p>
          <p><strong>Metadata:</strong> ingested={{ Object.keys(metadata.ingested_columns || {}).length }}, computed={{ Object.keys(metadata.computed_columns || {}).length }}</p>
        </div>
      </div>
    </div>

    <!-- Data Table -->
    <div v-if="hasSelectedColumns">
      <div v-if="tableData.length > 0">
        <DataTable
          :data="tableData"
          :columns="tableColumns"
          :loading="loading"
          :searchable="true"
          search-placeholder="Search transactions..."
          :selectable="false"
          :resizable="true"
          :paginated="false"
        >
          <template #cell-actions="{ value, item }">
            <Button 
              @click="showTransactionJson(value)"
              variant="outline"
              size="sm"
              class="h-8 px-2"
            >
              View JSON
            </Button>
          </template>
        </DataTable>
      </div>
      <div v-else-if="!loading" class="text-center py-8 text-gray-500">
        <p>No transactions found for the selected columns.</p>
      </div>
      <div v-else class="text-center py-8">
        <p>Loading transactions...</p>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else class="text-center py-12">
      <Settings class="h-12 w-12 mx-auto text-muted-foreground mb-4" />
      <h3 class="text-lg font-semibold mb-2">No Columns Selected</h3>
      <p class="text-muted-foreground mb-4">
        Select columns from the metadata to start viewing transactions
      </p>
      <Button @click="showColumnSelector = true">
        <Settings class="h-4 w-4 mr-2" />
        Select Columns
      </Button>
    </div>

    <!-- JSON Modal -->
    <div v-if="showJsonModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] flex flex-col">
        <!-- Header -->
        <div class="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100">Transaction JSON</h3>
          <Button @click="closeJsonModal" variant="ghost" size="sm" class="h-8 w-8 p-0">
            <span class="text-lg leading-none">&times;</span>
          </Button>
        </div>
        
        <!-- Content -->
        <div class="flex-1 overflow-hidden">
          <div class="h-full p-4">
            <pre class="text-xs text-gray-600 dark:text-gray-300 bg-gray-50 dark:bg-gray-900 p-4 rounded-lg overflow-auto h-full whitespace-pre-wrap">{{ JSON.stringify(selectedTransactionJson, null, 2) }}</pre>
          </div>
        </div>
        
        <!-- Footer -->
        <div class="flex items-center justify-between p-4 border-t border-gray-200 dark:border-gray-700">
          <div class="text-sm text-gray-500 dark:text-gray-400">
            Transaction ID: {{ selectedTransactionJson?.id }}
          </div>
          <div class="flex gap-2">
            <Button @click="closeJsonModal" variant="outline" size="sm">
              Close
            </Button>
            <Button 
              @click="navigator.clipboard.writeText(JSON.stringify(selectedTransactionJson, null, 2))"
              variant="default"
              size="sm"
            >
              Copy JSON
            </Button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>