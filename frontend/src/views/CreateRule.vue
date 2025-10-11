<template>
  <div class="h-full flex flex-col">
    <!-- Header with Back Button -->
    <div class="bg-background border-b px-6 py-4 flex items-center space-x-4">
      <Button 
        @click="goBack"
        variant="ghost"
        size="sm"
        class="flex items-center space-x-2"
      >
        <ArrowLeft class="w-4 h-4" />
        <span>Back to Rules</span>
      </Button>
      
      <div class="flex-1">
        <h1 class="text-2xl font-bold">{{ isEdit ? 'Edit Rule' : 'Create New Rule' }}</h1>
        <p class="text-sm text-muted-foreground mt-1">
          {{ isEdit ? 'Update existing rule configuration' : 'Define a new rule for computing transaction field values' }}
        </p>
      </div>
      
      <div class="flex items-center space-x-3">
        <Button 
          @click="handleTest"
          variant="outline"
          size="sm"
        >
          <TestTube class="w-4 h-4 mr-2" />
          Test Rule
        </Button>
        <Button 
          @click="handleSave"
          :disabled="!isValid"
          size="sm"
        >
          <Save class="w-4 h-4 mr-2" />
          {{ isEdit ? 'Update Rule' : 'Create Rule' }}
        </Button>
      </div>
    </div>

    <!-- Main Content -->
    <div class="flex-1 overflow-y-auto">
      <div class="max-w-7xl mx-auto p-6 space-y-6">
        <!-- Rule Editor -->
        <Card>
          <CardContent class="p-6">
            <RuleEditor 
              :rule="localRule"
              :transaction-fields="transactionFields"
              :formula-commands="formulaCommands"
              @update:rule="updateRule"
              @test="handleTest"
            />
          </CardContent>
        </Card>

        <!-- Transaction Testing Section -->
        <Card>
          <CardHeader>
            <div class="flex items-center justify-between">
              <div>
                <CardTitle class="text-lg">Test with Transactions</CardTitle>
                <p class="text-sm text-muted-foreground mt-1">
                  Select transactions to test your rule and see computed results
                </p>
              </div>
              <div class="flex items-center space-x-3">
                <Button 
                  @click="runRuleOnSelected"
                  :disabled="selectedTransactions.length === 0 || !isValid || testingRule"
                  variant="default"
                  size="sm"
                >
                  <Play class="w-4 h-4 mr-2" :class="{ 'animate-spin': testingRule }"/>
                  {{ testingRule ? 'Testing...' : `Test Rule (${selectedTransactions.length})` }}
                </Button>
                <Button 
                  @click="refreshTransactions"
                  :disabled="loadingTransactions"
                  variant="outline"
                  size="sm"
                >
                  <RefreshCw class="w-4 h-4" :class="{ 'animate-spin': loadingTransactions }" />
                </Button>
              </div>
            </div>
          </CardHeader>

          <CardContent>
            <!-- Filters -->
            <div class="flex flex-wrap items-center gap-4 mb-4 p-4 bg-muted/50 rounded-lg">
              <div class="flex items-center space-x-2">
                <Label class="text-sm font-medium">Statement:</Label>
                <Select v-model="selectedStatement" @update:model-value="filterTransactions">
                  <SelectTrigger class="w-64">
                    <SelectValue placeholder="All statements" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All statements</SelectItem>
                    <SelectItem 
                      v-for="statement in availableStatements" 
                      :key="statement.id" 
                      :value="statement.id"
                    >
                      {{ statement.filename }}
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div class="flex items-center space-x-2">
                <Label class="text-sm font-medium">Search:</Label>
                <Input
                  v-model="searchQuery"
                  placeholder="Search transactions..."
                  class="w-64"
                  @input="filterTransactions"
                />
              </div>

              <div class="flex items-center space-x-2">
                <Checkbox 
                  :checked="showOnlyMatching"
                  @update:checked="toggleShowOnlyMatching"
                  id="show-matching"
                />
                <Label for="show-matching" class="text-sm">Show only condition matches</Label>
              </div>

              <div class="flex-1"></div>

              <div class="flex items-center space-x-2">
                <Button 
                  @click="selectAllVisible"
                  variant="outline"
                  size="sm"
                >
                  Select All ({{ filteredTransactions.length }})
                </Button>
                <Button 
                  @click="clearSelection"
                  variant="outline"
                  size="sm"
                >
                  Clear Selection
                </Button>
              </div>
            </div>

            <!-- Transaction Table -->
            <div class="border rounded-lg">
              <div v-if="loadingTransactions" class="flex items-center justify-center py-12">
                <div class="animate-spin rounded-full h-6 w-6 border-2 border-primary border-t-transparent"></div>
                <span class="ml-3 text-muted-foreground">Loading transactions...</span>
              </div>

              <div v-else-if="filteredTransactions.length === 0" class="flex flex-col items-center justify-center py-12 text-muted-foreground">
                <FileX class="w-8 h-8 mb-2 opacity-50" />
                <p>No transactions found</p>
                <p class="text-sm">Try adjusting your filters or load some transaction data</p>
              </div>

              <div v-else class="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead class="w-12">
                        <Checkbox 
                          :checked="allVisibleSelected"
                          :indeterminate="someVisibleSelected && !allVisibleSelected"
                          @update:checked="toggleAllVisible"
                        />
                      </TableHead>
                      <TableHead>Statement</TableHead>
                      <TableHead>Description</TableHead>
                      <TableHead>Amount</TableHead>
                      <TableHead>Date</TableHead>
                      <!-- Dynamic columns for referenced fields -->
                      <TableHead 
                        v-for="field in getReferencedFields.slice(0, 3)" 
                        :key="field"
                        class="bg-blue-50 dark:bg-blue-950"
                      >
                        <span class="text-xs font-mono">{{ field }}</span>
                      </TableHead>
                      <TableHead>Condition Match</TableHead>
                      <TableHead class="w-32">Current Value</TableHead>
                      <TableHead class="w-48 bg-green-50 dark:bg-green-950">
                        {{ localRule.target_field ? `computed_${localRule.target_field}` : 'Computed Result' }}
                      </TableHead>
                      <TableHead class="w-20">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    <TableRow 
                      v-for="transaction in paginatedTransactions" 
                      :key="transaction.id"
                      :class="{ 'bg-muted/20': selectedTransactions.includes(transaction.id) }"
                    >
                      <TableCell>
                        <Checkbox 
                          :checked="selectedTransactions.includes(transaction.id)"
                          @update:checked="toggleTransaction(transaction.id)"
                        />
                      </TableCell>
                      <TableCell class="font-medium">
                        <Badge variant="outline" class="text-xs">
                          {{ transaction.statement.filename.split('.').slice(0, -1).join('.') }}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <span class="truncate max-w-xs block" :title="getTransactionDescription(transaction)">
                          {{ getTransactionDescription(transaction) }}
                        </span>
                      </TableCell>
                      <TableCell>
                        <span class="font-mono">
                          {{ getTransactionAmount(transaction) }}
                        </span>
                      </TableCell>
                      <TableCell>
                        {{ getTransactionDate(transaction) }}
                      </TableCell>
                      <!-- Dynamic cells for referenced fields -->
                      <TableCell 
                        v-for="field in getReferencedFields.slice(0, 3)" 
                        :key="field"
                        class="bg-blue-50/50 dark:bg-blue-950/50"
                      >
                        <span class="font-mono text-xs truncate block max-w-32" :title="String(getFieldValue(transaction, field))">
                          {{ getFieldValue(transaction, field) }}
                        </span>
                      </TableCell>
                      <TableCell>
                        <Badge 
                          :variant="evaluateCondition(transaction) ? 'default' : 'secondary'"
                          class="text-xs"
                        >
                          {{ evaluateCondition(transaction) ? 'Match' : 'No Match' }}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div class="space-y-1">
                          <div v-if="getExistingComputedValue(transaction)">
                            <Badge 
                              variant="outline"
                              class="text-xs max-w-32 truncate"
                              :title="String(getExistingComputedValue(transaction))"
                            >
                              {{ getExistingComputedValue(transaction) }}
                            </Badge>
                            <span class="text-xs text-muted-foreground block">Already computed</span>
                          </div>
                          <span v-else class="text-xs text-muted-foreground">Not set</span>
                        </div>
                      </TableCell>
                      <TableCell class="bg-green-50/50 dark:bg-green-950/50">
                        <div class="space-y-1">
                          <div v-if="transaction.testResult">
                            <Badge 
                              :variant="transaction.testResult.success ? 'default' : 'destructive'"
                              class="text-xs max-w-40 truncate"
                              :title="transaction.testResult.success ? String(transaction.testResult.value) : transaction.testResult.error"
                            >
                              {{ transaction.testResult.success ? transaction.testResult.value : 'Error' }}
                            </Badge>
                          </div>
                          <span v-else class="text-xs text-muted-foreground">Not tested</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div class="flex items-center space-x-1">
                          <Button 
                            @click="testSingleTransaction(transaction)"
                            :disabled="!isValid || testingRule"
                            variant="outline"
                            size="sm"
                          >
                            <TestTube class="w-3 h-3" />
                          </Button>
                          <Button 
                            @click="viewTransactionJson(transaction)"
                            variant="ghost"
                            size="sm"
                            :title="'View JSON data'"
                          >
                            <Code class="w-3 h-3" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </div>

              <!-- Pagination -->
              <div v-if="filteredTransactions.length > pageSize" class="flex items-center justify-between p-4 border-t">
                <div class="text-sm text-muted-foreground">
                  Showing {{ ((currentPage - 1) * pageSize) + 1 }} to {{ Math.min(currentPage * pageSize, filteredTransactions.length) }} 
                  of {{ filteredTransactions.length }} transactions
                </div>
                <div class="flex items-center space-x-2">
                  <Button 
                    @click="currentPage = Math.max(1, currentPage - 1)"
                    :disabled="currentPage === 1"
                    variant="outline"
                    size="sm"
                  >
                    <ChevronLeft class="w-4 h-4" />
                  </Button>
                  <span class="text-sm">Page {{ currentPage }} of {{ totalPages }}</span>
                  <Button 
                    @click="currentPage = Math.min(totalPages, currentPage + 1)"
                    :disabled="currentPage === totalPages"
                    variant="outline"
                    size="sm"
                  >
                    <ChevronRight class="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>

    <!-- Test Dialog -->
    <RuleTestDialog
      v-if="showTestDialog"
      :rule="localRule"
      :transaction-fields="transactionFields"
      @close="closeTestDialog"
    />
    
    <!-- Transaction JSON Dialog -->
    <div v-if="showTransactionJson" class="fixed inset-0 bg-background/80 backdrop-blur-sm flex items-center justify-center p-4 z-50" @click.self="closeTransactionJson">
      <Card class="max-w-5xl w-full max-h-[90vh] overflow-hidden">
        <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle class="text-xl">Transaction Data Viewer</CardTitle>
          <Button 
            @click="closeTransactionJson"
            variant="ghost"
            size="icon"
          >
            <X class="w-4 h-4" />
          </Button>
        </CardHeader>
        
        <CardContent class="overflow-y-auto max-h-[calc(90vh-120px)]">
          <div v-if="selectedTransactionForJson" class="space-y-4">
            <!-- Transaction Info -->
            <div class="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
              <div>
                <h3 class="font-medium">{{ getTransactionDescription(selectedTransactionForJson) }}</h3>
                <p class="text-sm text-muted-foreground">
                  {{ selectedTransactionForJson.statement.filename }} • 
                  Created: {{ formatTransactionDate(selectedTransactionForJson.created_at) }}
                </p>
              </div>
              <Badge variant="outline" class="font-mono text-xs">
                ID: {{ selectedTransactionForJson.id.slice(-8) }}
              </Badge>
            </div>
            
            <!-- All JSON views at once -->
            <div class="space-y-4">
              <!-- Whole Transaction -->
              <div class="border rounded-lg overflow-hidden">
                <div class="flex items-center justify-between px-4 py-3 bg-muted/30 border-b">
                  <h4 class="text-sm font-semibold">🔍 Whole Transaction</h4>
                  <Button 
                    @click="copyToClipboard(getWholeTransactionJson())"
                    variant="outline"
                    size="sm"
                  >
                    <Copy class="w-3 h-3 mr-2" />
                    Copy
                  </Button>
                </div>
                <div class="p-4 bg-muted/10">
                  <div class="bg-muted p-4 rounded-lg font-mono text-xs max-h-64 overflow-y-auto border">
                    <pre>{{ getWholeTransactionJson() }}</pre>
                  </div>
                </div>
              </div>
              
              <!-- Raw/Ingested Values -->
              <div class="border rounded-lg overflow-hidden border-green-300 dark:border-green-700">
                <div class="flex items-center justify-between px-4 py-3 bg-green-50 dark:bg-green-950/30 border-b border-green-300 dark:border-green-700">
                  <h4 class="text-sm font-semibold text-green-800 dark:text-green-200">📥 Raw Ingested Values</h4>
                  <Button 
                    @click="copyToClipboard(getRawValuesJson())"
                    variant="outline"
                    size="sm"
                    class="border-green-300 dark:border-green-700"
                  >
                    <Copy class="w-3 h-3 mr-2" />
                    Copy
                  </Button>
                </div>
                <div class="p-4 bg-green-50/50 dark:bg-green-950/10">
                  <div class="bg-green-50 dark:bg-green-950/30 p-4 rounded-lg font-mono text-xs max-h-64 overflow-y-auto border border-green-200 dark:border-green-800">
                    <pre>{{ getRawValuesJson() }}</pre>
                  </div>
                </div>
              </div>
              
              <!-- Computed Values -->
              <div class="border rounded-lg overflow-hidden border-blue-300 dark:border-blue-700">
                <div class="flex items-center justify-between px-4 py-3 bg-blue-50 dark:bg-blue-950/30 border-b border-blue-300 dark:border-blue-700">
                  <h4 class="text-sm font-semibold text-blue-800 dark:text-blue-200">⚙️ Computed Values</h4>
                  <Button 
                    @click="copyToClipboard(getComputedValuesJson())"
                    variant="outline"
                    size="sm"
                    class="border-blue-300 dark:border-blue-700"
                  >
                    <Copy class="w-3 h-3 mr-2" />
                    Copy
                  </Button>
                </div>
                <div class="p-4 bg-blue-50/50 dark:bg-blue-950/10">
                  <div class="bg-blue-50 dark:bg-blue-950/30 p-4 rounded-lg font-mono text-xs max-h-64 overflow-y-auto border border-blue-200 dark:border-blue-800">
                    <pre>{{ getComputedValuesJson() }}</pre>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Checkbox } from '@/components/ui/checkbox'
import { Badge } from '@/components/ui/badge'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import RuleEditor from '@/components/rules/RuleEditor.vue'
import RuleTestDialog from '@/components/rules/RuleTestDialog.vue'
import { ArrowLeft, TestTube, Save, Play, RefreshCw, FileX, ChevronLeft, ChevronRight, Eye, Code, Copy, X } from 'lucide-vue-next'
import { useAlert } from '@/composables/useAlert'
import { getFilteredTransactions } from '@/api/transactionFiltering'
import { transactionsApi } from '@/api/transactions'
import api from '@/api/axios'

export default {
  name: 'CreateRule',
  components: {
    Button,
    Card,
    CardContent,
    CardHeader,
    CardTitle,
    Input,
    Label,
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
    Checkbox,
    Badge,
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
    RuleEditor,
    RuleTestDialog,
    ArrowLeft,
    TestTube,
    Save,
    Play,
    RefreshCw,
    FileX,
    ChevronLeft,
    ChevronRight,
    Eye,
    Code,
    Copy,
    X
  },
  setup() {
    const router = useRouter()
    const route = useRoute()
    const { showAlert } = useAlert()
    
    // State
    const localRule = ref({
      name: '',
      description: '',
      target_field: '',
      condition: '',
      action: '',
      rule_type: 'formula',
      priority: 100,
      active: true
    })
    const showTestDialog = ref(false)
    const transactionFields = ref([])
    const formulaCommands = ref([])
    const allRules = ref([])
    const isAutoNaming = ref(true) // Track if we're auto-naming
    const isAutoPriority = ref(true) // Track if we're auto-priority
    
    // Transaction testing state
    const transactions = ref([])
    const filteredTransactions = ref([])
    const selectedTransactions = ref([])
    const availableStatements = ref([])
    const selectedStatement = ref('all')
    const searchQuery = ref('')
    const showOnlyMatching = ref(false)
    const loadingTransactions = ref(false)
    const testingRule = ref(false)
    
    // Transaction JSON viewing
    const showTransactionJson = ref(false)
    const selectedTransactionForJson = ref(null)
    
    // Pagination
    const currentPage = ref(1)
    const pageSize = ref(20)

    // Computed
    const isEdit = computed(() => !!localRule.value.id)
    
    const isValid = computed(() => {
      const hasRequiredFields = localRule.value.name?.trim() && 
                               localRule.value.target_field?.trim() && 
                               localRule.value.action?.trim()
      
      return hasRequiredFields
    })
    
    // Transaction table computed properties
    const paginatedTransactions = computed(() => {
      // When using server-side filtering, transactions are already paginated
      // When using client-side filtering (condition matching), we need to paginate manually
      if (showOnlyMatching.value && localRule.value.condition?.trim()) {
        const start = (currentPage.value - 1) * pageSize.value
        const end = start + pageSize.value
        return filteredTransactions.value.slice(start, end)
      }
      return filteredTransactions.value
    })
    
    const totalPages = computed(() => {
      if (showOnlyMatching.value && localRule.value.condition?.trim()) {
        return Math.ceil(filteredTransactions.value.length / pageSize.value)
      }
      // For server-side pagination, we'd need to track total count from the API response
      // For now, assume we have one page of results
      return Math.max(1, Math.ceil(filteredTransactions.value.length / pageSize.value))
    })
    
    const allVisibleSelected = computed(() => {
      return paginatedTransactions.value.length > 0 && 
             paginatedTransactions.value.every(t => selectedTransactions.value.includes(t.id))
    })
    
    const someVisibleSelected = computed(() => {
      return paginatedTransactions.value.some(t => selectedTransactions.value.includes(t.id))
    })

    // Methods
    const goBack = () => {
      if (hasChanges()) {
        if (!confirm('You have unsaved changes. Are you sure you want to go back?')) {
          return
        }
      }
      router.push('/rules')
    }

    const hasChanges = () => {
      // Simple check for changes - could be made more sophisticated
      return localRule.value.name?.trim() || 
             localRule.value.target_field?.trim() || 
             localRule.value.action?.trim() ||
             localRule.value.condition?.trim() ||
             localRule.value.description?.trim()
    }

    const updateRule = (updatedRule) => {
      localRule.value = { ...updatedRule }
    }
    
    const loadAllRules = async () => {
      try {
        const response = await api.get('/rules')
        allRules.value = response.data || []
      } catch (error) {
        console.error('Error loading rules:', error)
        allRules.value = []
      }
    }
    
    const getNextPriority = () => {
      if (allRules.value.length === 0) return 100
      const maxPriority = Math.max(...allRules.value.map(r => r.priority || 0))
      return maxPriority + 10
    }
    
    const getNextRuleNumber = (targetField) => {
      if (!targetField) return 1
      const rulesWithSameTarget = allRules.value.filter(r => 
        r.target_field === targetField
      )
      return rulesWithSameTarget.length + 1
    }
    
    const autoPopulateName = (targetField) => {
      if (!targetField || !isAutoNaming.value) return
      const ruleNumber = getNextRuleNumber(targetField)
      localRule.value.name = `${targetField} #${ruleNumber}`
    }
    
    const autoPopulatePriority = () => {
      if (isAutoPriority.value) {
        localRule.value.priority = getNextPriority()
      }
    }
    
    const ensureComputedPrefix = (fieldName) => {
      if (!fieldName) return ''
      if (fieldName.startsWith('computed_')) return fieldName
      return `computed_${fieldName}`
    }

    const handleSave = async () => {
      if (!isValid.value) return
      
      try {
        const ruleData = { ...localRule.value }
        
        // Ensure computed_ prefix on target field
        ruleData.target_field = ensureComputedPrefix(ruleData.target_field)
        
        // Clean up empty fields
        if (!ruleData.condition?.trim()) {
          ruleData.condition = null
        }
        if (!ruleData.description?.trim()) {
          ruleData.description = null
        }
        
        const isEditMode = isEdit.value
        
        const response = isEditMode 
          ? await api.put(`/rules/${ruleData.id}`, ruleData)
          : await api.post('/rules', ruleData)
        
        const savedRule = response.data
        
        showAlert({
          type: 'success',
          message: isEditMode ? '✅ Rule updated successfully!' : '✅ Rule created successfully!',
          duration: 3000
        })
        
        // Navigate back to rules list
        setTimeout(() => router.push('/rules'), 500)
        
      } catch (error) {
        showAlert({
          type: 'error',
          title: 'Error Saving Rule',
          message: error.response?.data?.detail || error.message,
          persistent: true
        })
      }
    }

    const handleTest = () => {
      showTestDialog.value = true
    }

    const closeTestDialog = () => {
      showTestDialog.value = false
    }

    const loadTransactionFields = async () => {
      try {
        const response = await api.get('/formulas/fields')
        const data = response.data
        
        // Store both ingested and computed fields separately for better organization
        transactionFields.value = {
          ingested: data.ingested_fields || [],
          computed: data.computed_fields || [],
          all: [...(data.ingested_fields || []), ...(data.computed_fields || [])]
        }
      } catch (error) {
        console.error('Error loading transaction fields:', error)
        // Fallback to empty structure
        transactionFields.value = {
          ingested: [],
          computed: [],
          all: []
        }
      }
    }

    const loadFormulaCommands = async () => {
      try {
        const response = await api.get('/formulas/commands')
        formulaCommands.value = response.data
      } catch (error) {
        console.error('Error loading formula commands:', error)
      }
    }

    const loadRule = async (ruleId) => {
      try {
        const response = await api.get(`/rules/${ruleId}`)
        const rule = response.data
        localRule.value = { ...rule }
        // When editing, disable auto-naming and auto-priority
        isAutoNaming.value = false
        isAutoPriority.value = false
      } catch (error) {
        showAlert({
          type: 'error',
          title: 'Error Loading Rule',
          message: error.response?.data?.detail || error.message,
          persistent: true
        })
        router.push('/rules')
      }
    }

    // This onMounted block is replaced by the enhanced one below

    // Transaction methods
    const loadTransactions = async () => {
      try {
        loadingTransactions.value = true
        
        // Build filter parameters for server-side filtering
        const params = {
          ...(selectedStatement.value !== 'all' && { statementId: selectedStatement.value }),
          ...(searchQuery.value && { search: searchQuery.value })
        }
        
        // If showing only matching transactions, load all and filter client-side for condition matching
        // Otherwise use server-side pagination
        if (showOnlyMatching.value && localRule.value.condition?.trim()) {
          // Load more records for condition filtering (client-side)
          params.limit = 1000 // Load more for client-side filtering
        } else {
          // Use server-side pagination
          params.skip = (currentPage.value - 1) * pageSize.value
          params.limit = pageSize.value
        }
        
        const result = await getFilteredTransactions(params)
        
        if (showOnlyMatching.value && localRule.value.condition?.trim()) {
          // Client-side condition filtering for now
          const matchingTransactions = result.transactions.filter(t => evaluateCondition(t))
          filteredTransactions.value = matchingTransactions
        } else {
          filteredTransactions.value = result.transactions || []
        }
        
        // Reset page if needed
        if (currentPage.value > 1 && filteredTransactions.value.length === 0) {
          currentPage.value = 1
          await loadTransactions()
          return
        }
        
      } catch (error) {
        showAlert({
          type: 'error',
          title: 'Error Loading Transactions',
          message: error.response?.data?.detail || error.message
        })
        filteredTransactions.value = []
      } finally {
        loadingTransactions.value = false
      }
    }
    
    const loadStatements = async () => {
      try {
        const response = await api.get('/statements')
        const data = response.data
        availableStatements.value = data.statements || []
      } catch (error) {
        console.error('Error loading statements:', error)
        availableStatements.value = []
      }
    }
    
    const filterTransactions = async () => {
      currentPage.value = 1
      await loadTransactions()
    }
    
    const refreshTransactions = async () => {
      selectedTransactions.value = []
      await loadTransactions()
    }
    
    const toggleShowOnlyMatching = async (checked) => {
      showOnlyMatching.value = checked
      await filterTransactions()
    }
    
    // Selection methods
    const toggleTransaction = (transactionId) => {
      const index = selectedTransactions.value.indexOf(transactionId)
      if (index > -1) {
        selectedTransactions.value.splice(index, 1)
      } else {
        selectedTransactions.value.push(transactionId)
      }
    }
    
    const toggleAllVisible = (checked) => {
      if (checked) {
        const visibleIds = paginatedTransactions.value.map(t => t.id)
        visibleIds.forEach(id => {
          if (!selectedTransactions.value.includes(id)) {
            selectedTransactions.value.push(id)
          }
        })
      } else {
        const visibleIds = paginatedTransactions.value.map(t => t.id)
        selectedTransactions.value = selectedTransactions.value.filter(id => !visibleIds.includes(id))
      }
    }
    
    const selectAllVisible = () => {
      const visibleIds = paginatedTransactions.value.map(t => t.id)
      visibleIds.forEach(id => {
        if (!selectedTransactions.value.includes(id)) {
          selectedTransactions.value.push(id)
        }
      })
    }
    
    const clearSelection = () => {
      selectedTransactions.value = []
    }
    
    // Rule testing methods
    const evaluateCondition = (transaction) => {
      if (!localRule.value.condition?.trim()) return true
      
      try {
        // Simple evaluation - would need to implement proper rule evaluation
        // For now, just return true for demonstration
        // In production, this would use the same evaluation logic as the backend
        return true
      } catch (error) {
        console.error('Error evaluating condition:', error)
        return false
      }
    }
    
    const runRuleOnSelected = async () => {
      if (selectedTransactions.value.length === 0 || !isValid.value) return
      
      try {
        testingRule.value = true
        
        // Test rule on selected transactions
        const results = await Promise.allSettled(
          selectedTransactions.value.map(async (transactionId) => {
            try {
              const transaction = filteredTransactions.value.find(t => t.id === transactionId)
              if (!transaction) throw new Error('Transaction not found')
              
              const response = await api.post('/rules/test', {
                rule: localRule.value,
                sample_transaction: transaction.ingested_content
              })
              
              const result = response.data
              console.log('Bulk test API Response for', transactionId, ':', result) // Debug log
              console.log('  - success:', result.success)
              console.log('  - result_value:', result.result_value)
              console.log('  - error:', result.error)
              console.log('  - sent data:', transaction.ingested_content)
              
              return { 
                transactionId, 
                success: result.success, 
                value: result.result_value,
                error: result.error 
              }
            } catch (error) {
              return { transactionId, success: false, error: error.message }
            }
          })
        )
        
        // Update transaction results - use array spread to trigger reactivity
        console.log('DEBUG: Processing results:', results)
        filteredTransactions.value = filteredTransactions.value.map(transaction => {
          const result = results.find(r => 
            r.status === 'fulfilled' && r.value.transactionId === transaction.id
          )
          
          if (result) {
            console.log('DEBUG: Adding testResult to transaction', transaction.id, result.value)
            return {
              ...transaction,
              testResult: result.value
            }
          }
          
          return transaction
        })
        console.log('DEBUG: Updated filteredTransactions:', filteredTransactions.value.map(t => ({id: t.id, testResult: t.testResult})))
        
        const successCount = results.filter(r => r.status === 'fulfilled' && r.value.success).length
        const errorCount = results.length - successCount
        
        if (errorCount === 0) {
          showAlert({
            type: 'success',
            message: `✅ Rule tested on ${results.length} transactions. All ${successCount} tests successful!`,
            duration: 4000
          })
        } else {
          showAlert({
            type: 'warning',
            title: 'Bulk Rule Test Completed',
            message: `📊 Tested ${results.length} transactions\n✅ Successful: ${successCount}\n❌ Failed: ${errorCount}\n\nCheck individual transaction results in the table below.`,
            duration: 8000
          })
        }
        
      } catch (error) {
        showAlert({
          type: 'error',
          title: 'Bulk Rule Test Error',
          message: `❌ Failed to test rule on selected transactions\n🚨 Error: ${error.message}`,
          persistent: true
        })
      } finally {
        testingRule.value = false
      }
    }
    
    const testSingleTransaction = async (transaction) => {
      if (!isValid.value) return
      
      try {
        const response = await api.post('/rules/test', {
          rule: localRule.value,
          sample_transaction: transaction.ingested_content
        })
        
        const result = response.data
        console.log('API Response:', result) // Debug log
        
        const testResult = {
          success: result.success,
          value: result.result_value,
          error: result.error
        }
        
        // Update the transaction in the array to trigger reactivity
        const index = filteredTransactions.value.findIndex(t => t.id === transaction.id)
        if (index !== -1) {
          filteredTransactions.value[index] = {
            ...filteredTransactions.value[index],
            testResult
          }
        }
        
        if (result.success) {
          showAlert({
            type: 'success',
            message: `✅ Rule tested on transaction ${transaction.id.slice(-8)} | 📊 Result: ${localRule.value.target_field} = ${result.result_value} | 🎯 Condition: ${result.condition_matched ? 'Matched' : 'Not matched'}`,
            duration: 4000
          })
        } else {
          showAlert({
            type: 'error',
            title: 'Rule Test Failed',
            message: `❌ Transaction: ${transaction.id.slice(-8)}\n🚨 Error: ${result.error || 'Unknown error'}\n🎯 Target Field: ${localRule.value.target_field}`,
            persistent: true
          })
        }
        
      } catch (error) {
        console.log('Test error:', error) // Debug log
        
        const testResult = {
          success: false,
          error: error.message
        }
        
        // Update the transaction in the array to trigger reactivity
        const index = filteredTransactions.value.findIndex(t => t.id === transaction.id)
        if (index !== -1) {
          filteredTransactions.value[index] = {
            ...filteredTransactions.value[index],
            testResult
          }
        }
        
        showAlert({
          type: 'error',
          title: 'Rule Test Error', 
          message: `❌ Failed to test rule\n🚨 Error: ${error.message}\n🎯 Transaction: ${transaction.id.slice(-8)}`,
          persistent: true
        })
      }
    }
    
    // Utility methods for transaction display
    const getTransactionDescription = (transaction) => {
      const content = transaction.ingested_content || {}
      return content.description || content.merchant || content.payee || 'No description'
    }
    
    const getTransactionAmount = (transaction) => {
      const content = transaction.ingested_content || {}
      return content.amount || content.debit || content.credit || 'N/A'
    }
    
    const getTransactionDate = (transaction) => {
      const content = transaction.ingested_content || {}
      const dateValue = content.date || content.transaction_date || content.posted_date
      if (dateValue) {
        try {
          return new Date(dateValue).toLocaleDateString()
        } catch (e) {
          return dateValue
        }
      }
      return 'N/A'
    }
    
    const getExistingComputedValue = (transaction) => {
      if (!transaction.computed_content || !localRule.value?.target_field) {
        return null
      }
      
      const computedContent = transaction.computed_content
      const targetField = localRule.value.target_field
      
      // Check if the target field already has a computed value
      const existingValue = computedContent[targetField]
      if (existingValue !== null && existingValue !== undefined && existingValue !== '') {
        return existingValue
      }
      
      return null
    }
    
    // Extract field names referenced in rule's condition and action
    const getReferencedFields = computed(() => {
      const fields = new Set()
      const ruleText = `${localRule.value.condition || ''} ${localRule.value.action || ''}`
      
      // Extract field names that might be referenced
      // This is a simple regex that looks for word characters not followed by (
      const fieldMatches = ruleText.match(/\b([a-z_][a-z0-9_]*)\b(?!\s*\()/gi)
      
      if (fieldMatches) {
        fieldMatches.forEach(field => {
          // Filter out common keywords and keep potential field names
          const keywords = ['and', 'or', 'not', 'in', 'is', 'true', 'false', 'null', 'if', 'else', 'return']
          if (!keywords.includes(field.toLowerCase())) {
            fields.add(field)
          }
        })
      }
      
      return Array.from(fields)
    })
    
    const getFieldValue = (transaction, fieldName) => {
      // Check ingested content first
      if (transaction.ingested_content?.[fieldName] !== undefined) {
        return transaction.ingested_content[fieldName]
      }
      // Then check computed content
      if (transaction.computed_content?.[fieldName] !== undefined) {
        return transaction.computed_content[fieldName]
      }
      return 'N/A'
    }
    
    // Transaction JSON viewing methods
    const viewTransactionJson = (transaction) => {
      selectedTransactionForJson.value = transaction
      showTransactionJson.value = true
    }
    
    const closeTransactionJson = () => {
      showTransactionJson.value = false
      selectedTransactionForJson.value = null
    }
    
    const getWholeTransactionJson = () => {
      if (!selectedTransactionForJson.value) return '{}'
      return JSON.stringify(selectedTransactionForJson.value, null, 2)
    }
    
    const getRawValuesJson = () => {
      if (!selectedTransactionForJson.value) return '{}'
      
      // If statement_filename is not in ingested_content (old transactions), add it
      const ingestedContent = selectedTransactionForJson.value.ingested_content || {}
      const rawValues = ingestedContent.statement_filename 
        ? ingestedContent 
        : {
            statement_filename: selectedTransactionForJson.value.statement?.filename || 'unknown',
            ...ingestedContent
          }
      
      return JSON.stringify(rawValues, null, 2)
    }
    
    const getComputedValuesJson = () => {
      if (!selectedTransactionForJson.value) return '{}'
      return JSON.stringify(selectedTransactionForJson.value.computed_content || {}, null, 2)
    }
    
    const copyToClipboard = async (jsonString) => {
      try {
        await navigator.clipboard.writeText(jsonString)
        showAlert({
          type: 'success',
          message: '✅ JSON copied to clipboard',
          duration: 2000
        })
      } catch (error) {
        showAlert({
          type: 'error',
          message: '❌ Failed to copy JSON to clipboard'
        })
      }
    }
    
    const copyTransactionJson = async () => {
      if (!selectedTransactionForJson.value) return
      
      try {
        await navigator.clipboard.writeText(JSON.stringify(selectedTransactionForJson.value, null, 2))
        showAlert({
          type: 'success',
          message: '✅ Transaction JSON copied to clipboard',
          duration: 2000
        })
      } catch (error) {
        showAlert({
          type: 'error',
          message: '❌ Failed to copy JSON to clipboard'
        })
      }
    }
    
    const formatTransactionDate = (dateString) => {
      try {
        return new Date(dateString).toLocaleString()
      } catch (e) {
        return dateString
      }
    }
    
    // Watchers
    watch([currentPage], () => {
      loadTransactions()
    })
    
    // Debounced watch for search and statement filters
    let filterTimeout = null
    watch([searchQuery, selectedStatement], () => {
      if (filterTimeout) clearTimeout(filterTimeout)
      filterTimeout = setTimeout(() => {
        filterTransactions()
      }, 300)
    })
    
    // Watch target_field changes to auto-populate name and add computed_ prefix
    watch(() => localRule.value.target_field, (newValue, oldValue) => {
      if (!newValue) return
      
      // Remove computed_ prefix if user types it (we'll add it on save)
      let cleanValue = newValue
      if (newValue.startsWith('computed_')) {
        cleanValue = newValue.replace(/^computed_/, '')
        localRule.value.target_field = cleanValue
        return
      }
      
      // Auto-populate name based on target field
      if (isAutoNaming.value && newValue !== oldValue) {
        autoPopulateName(cleanValue)
      }
    })
    
    // Watch name changes to disable auto-naming if user manually edits
    watch(() => localRule.value.name, (newValue, oldValue) => {
      if (oldValue && newValue !== oldValue && isAutoNaming.value) {
        const expectedName = `${localRule.value.target_field} #${getNextRuleNumber(localRule.value.target_field)}`
        if (newValue !== expectedName) {
          isAutoNaming.value = false
        }
      }
    })
    
    // Watch priority changes to disable auto-priority if user manually edits
    watch(() => localRule.value.priority, (newValue, oldValue) => {
      if (oldValue && newValue !== oldValue && isAutoPriority.value) {
        const expectedPriority = getNextPriority()
        if (newValue !== expectedPriority) {
          isAutoPriority.value = false
        }
      }
    })
    
    // Lifecycle
    onMounted(async () => {
      await Promise.all([
        loadTransactionFields(),
        loadFormulaCommands(),
        loadStatements(),
        loadTransactions(),
        loadAllRules()
      ])

      // Check if we're editing an existing rule
      const ruleId = route.params.id
      if (ruleId) {
        await loadRule(ruleId)
      } else {
        // For new rules, auto-populate priority
        autoPopulatePriority()
        
        // Check for target field from query params
        const targetField = route.query.target_field
        if (targetField && targetField !== 'all') {
          // Remove computed_ prefix if present in query param
          const cleanTarget = targetField.replace(/^computed_/, '')
          localRule.value.target_field = cleanTarget
          // Auto-populate name based on target field
          autoPopulateName(cleanTarget)
        }
      }
    })

    // Handle browser back button
    window.addEventListener('beforeunload', (e) => {
      if (hasChanges()) {
        e.preventDefault()
        e.returnValue = ''
      }
    })

    return {
      localRule,
      showTestDialog,
      isEdit,
      isValid,
      transactionFields,
      formulaCommands,
      allRules,
      isAutoNaming,
      isAutoPriority,
      // Transaction table state
      transactions,
      filteredTransactions,
      selectedTransactions,
      availableStatements,
      selectedStatement,
      searchQuery,
      showOnlyMatching,
      loadingTransactions,
      testingRule,
      showTransactionJson,
      selectedTransactionForJson,
      paginatedTransactions,
      currentPage,
      pageSize,
      totalPages,
      allVisibleSelected,
      someVisibleSelected,
      getReferencedFields,
      // Methods
      goBack,
      updateRule,
      loadAllRules,
      getNextPriority,
      getNextRuleNumber,
      autoPopulateName,
      autoPopulatePriority,
      ensureComputedPrefix,
      handleSave,
      handleTest,
      closeTestDialog,
      loadTransactions,
      filterTransactions,
      refreshTransactions,
      toggleShowOnlyMatching,
      toggleTransaction,
      toggleAllVisible,
      selectAllVisible,
      clearSelection,
      evaluateCondition,
      runRuleOnSelected,
      testSingleTransaction,
      getTransactionDescription,
      getTransactionAmount,
      getTransactionDate,
      getExistingComputedValue,
      getFieldValue,
      viewTransactionJson,
      closeTransactionJson,
      getWholeTransactionJson,
      getRawValuesJson,
      getComputedValuesJson,
      copyToClipboard,
      copyTransactionJson,
      formatTransactionDate
    }
  }
}
</script>
