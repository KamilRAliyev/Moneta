<template>
  <div class="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
    <Card class="max-w-4xl w-full max-h-[90vh] overflow-hidden">
      <!-- Header -->
      <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-4">
        <CardTitle class="text-xl">
          Test Rule: {{ rule.name }}
        </CardTitle>
        <Button
          @click="$emit('close')"
          variant="ghost"
          size="icon"
        >
          <X class="w-4 h-4" />
        </Button>
      </CardHeader>

      <CardContent class="overflow-y-auto max-h-[calc(90vh-200px)] space-y-6">
        <!-- Rule Summary -->
        <Card>
          <CardHeader class="pb-3">
            <CardTitle class="text-base">Rule Summary</CardTitle>
          </CardHeader>
          <CardContent class="space-y-4">
            <div class="grid grid-cols-2 gap-4">
              <div>
                <Label class="text-sm text-muted-foreground">Target Field</Label>
                <code class="block mt-1 px-2 py-1 bg-muted rounded text-sm">{{ rule.target_field }}</code>
              </div>
              <div>
                <Label class="text-sm text-muted-foreground">Type</Label>
                <Badge variant="secondary" class="mt-1">{{ rule.rule_type }}</Badge>
              </div>
              <div class="col-span-2" v-if="rule.condition">
                <Label class="text-sm text-muted-foreground">Condition</Label>
                <code class="block mt-1 px-2 py-1 bg-muted rounded text-sm">{{ rule.condition }}</code>
              </div>
              <div class="col-span-2">
                <Label class="text-sm text-muted-foreground">Action</Label>
                <code class="block mt-1 px-2 py-1 bg-muted rounded text-sm">{{ rule.action }}</code>
              </div>
            </div>
          </CardContent>
        </Card>

        <!-- Data Source Selection -->
        <Card>
          <CardHeader class="pb-3">
            <CardTitle class="text-base">Test Data Source</CardTitle>
          </CardHeader>
          <CardContent class="space-y-4">
            <div class="flex space-x-4">
              <Button
                @click="setDataSource('manual')"
                :variant="dataSource === 'manual' ? 'default' : 'outline'"
                size="sm"
              >
                Manual Input
              </Button>
              <Button
                @click="setDataSource('transaction')"
                :variant="dataSource === 'transaction' ? 'default' : 'outline'"
                size="sm"
              >
                Real Transaction
              </Button>
            </div>
            
            <!-- Transaction Selector -->
            <div v-if="dataSource === 'transaction'" class="space-y-4">
              <div class="flex space-x-2">
                <div class="flex-1">
                  <Input
                    v-model="transactionSearchQuery"
                    placeholder="Search transactions..."
                    class="mb-2"
                    @input="filterTransactions"
                  />
                  <Select v-model="selectedTransactionId" @update:model-value="loadSelectedTransaction">
                    <SelectTrigger>
                      <SelectValue placeholder="Select a transaction to test against..." />
                    </SelectTrigger>
                    <SelectContent class="max-h-60">
                      <SelectItem 
                        v-for="transaction in filteredTransactions" 
                        :key="transaction.id" 
                        :value="transaction.id"
                      >
                        <div class="flex flex-col w-full">
                          <div class="flex items-center justify-between">
                            <span class="font-medium truncate">{{ getTransactionDisplayName(transaction) }}</span>
                            <span class="text-xs text-muted-foreground ml-2">
                              {{ formatDate(transaction.created_at) }}
                            </span>
                          </div>
                          <span class="text-xs text-muted-foreground truncate">
                            {{ transaction.statement.filename }}
                          </span>
                          <div class="flex flex-wrap gap-1 mt-1">
                            <Badge 
                              v-for="(value, key) in getTransactionPreview(transaction)" 
                              :key="key"
                              variant="outline"
                              class="text-xs"
                            >
                              {{ key }}: {{ value }}
                            </Badge>
                          </div>
                        </div>
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <Button 
                  @click="loadTransactions"
                  :disabled="loadingTransactions"
                  variant="outline"
                  size="sm"
                >
                  <RefreshCw class="w-4 h-4" :class="{ 'animate-spin': loadingTransactions }" />
                </Button>
              </div>
              
              <div v-if="selectedTransaction" class="p-3 bg-muted/50 rounded-md">
                <div class="text-sm">
                  <div class="font-medium mb-2">Selected Transaction:</div>
                  <div class="space-y-1 text-xs text-muted-foreground mb-3">
                    <div><strong>ID:</strong> {{ selectedTransaction.id }}</div>
                    <div><strong>Statement:</strong> {{ selectedTransaction.statement.filename }}</div>
                    <div><strong>Created:</strong> {{ formatDate(selectedTransaction.created_at) }}</div>
                  </div>
                  
                  <div>
                    <div class="flex items-center justify-between mb-2">
                      <h6 class="font-medium text-muted-foreground">Complete Transaction JSON:</h6>
                      <Button 
                        @click="copyToClipboard(JSON.stringify(selectedTransaction, null, 2))"
                        variant="outline"
                        size="sm"
                      >
                        <Copy class="w-4 h-4 mr-1" />
                        Copy
                      </Button>
                    </div>
                    <div class="bg-background p-2 rounded font-mono text-xs max-h-48 overflow-y-auto border">
                      <pre>{{ JSON.stringify(selectedTransaction, null, 2) }}</pre>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <!-- Sample Data Input -->
        <Card v-if="dataSource === 'manual'">
          <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-3">
            <CardTitle class="text-base">Manual Sample Data</CardTitle>
            <div class="flex space-x-2">
              <Button 
                @click="loadSampleData"
                variant="link"
                size="sm"
                class="h-auto p-0"
              >
                Load Sample
              </Button>
              <Button 
                @click="clearSampleData"
                variant="link"
                size="sm"
                class="h-auto p-0 text-destructive"
              >
                Clear
              </Button>
            </div>
          </CardHeader>
          <CardContent class="space-y-4">
            <Textarea
              v-model="sampleDataJson"
              rows="8"
              class="font-mono text-sm"
              placeholder='Enter sample transaction JSON, e.g.:
{
  "merchant": "Amazon",
  "amount": "25.99",
  "date": "2024-01-15",
  "description": "Online purchase"
}'
            />
            
            <!-- Field Suggestions -->
            <div class="space-y-2">
              <Label class="text-xs text-muted-foreground">Available fields:</Label>
              
              <div v-if="transactionFields.ingested && transactionFields.ingested.length > 0">
                <div class="text-xs text-muted-foreground mb-1">Ingested Fields:</div>
                <div class="flex flex-wrap gap-1">
                  <Badge
                    v-for="field in transactionFields.ingested"
                    :key="field.name"
                    @click="insertField(field.name)"
                    variant="outline"
                    class="cursor-pointer hover:bg-accent text-xs bg-green-50 border-green-200 text-green-700 hover:bg-green-100"
                    :title="getFieldTooltip(field)"
                  >
                    {{ field.name }}
                  </Badge>
                </div>
              </div>
              
              <div v-if="transactionFields.computed && transactionFields.computed.length > 0">
                <div class="text-xs text-muted-foreground mb-1">Computed Fields:</div>
                <div class="flex flex-wrap gap-1">
                  <Badge
                    v-for="field in transactionFields.computed"
                    :key="field.name"
                    @click="insertField(field.name)"
                    variant="outline"
                    class="cursor-pointer hover:bg-accent text-xs bg-green-50 border-green-200 text-green-700 hover:bg-green-100"
                    :title="getFieldTooltip(field)"
                  >
                    {{ field.name }}
                  </Badge>
                </div>
              </div>
              
              <div v-if="(!transactionFields.ingested || transactionFields.ingested.length === 0) && (!transactionFields.computed || transactionFields.computed.length === 0)">
                <div class="text-xs text-muted-foreground">
                  No fields available. Upload and process some transactions first.
                </div>
              </div>
            </div>

            <!-- JSON Validation Error -->
            <div v-if="jsonError" class="p-3 border border-destructive/50 bg-destructive/5 rounded-md">
              <p class="text-sm text-destructive flex items-center">
                <AlertCircle class="w-4 h-4 mr-2" />
                Invalid JSON: {{ jsonError }}
              </p>
            </div>
          </CardContent>
        </Card>

        <!-- Test Results -->
        <Card v-if="testResult">
          <CardHeader class="pb-3">
            <CardTitle class="text-base">Test Results</CardTitle>
          </CardHeader>
          <CardContent class="space-y-4">
            <div v-if="testResult.success" class="space-y-3">
              <!-- Condition Result -->
              <div class="flex items-center p-3 rounded-md border" 
                   :class="testResult.condition_matched ? 'bg-green-50 border-green-200' : 'bg-yellow-50 border-yellow-200'">
                <div class="flex-shrink-0">
                  <CheckCircle v-if="testResult.condition_matched" class="w-5 h-5 text-green-500" />
                  <AlertCircle v-else class="w-5 h-5 text-yellow-500" />
                </div>
                <div class="ml-3">
                  <p class="text-sm font-medium" :class="testResult.condition_matched ? 'text-green-700' : 'text-yellow-700'">
                    {{ testResult.condition_matched ? 'Condition Matched' : 'Condition Not Matched' }}
                  </p>
                  <p class="text-xs" :class="testResult.condition_matched ? 'text-green-600' : 'text-yellow-600'">
                    {{ rule.condition || 'No condition (always matches)' }}
                  </p>
                </div>
              </div>

              <!-- Action Result -->
              <div v-if="testResult.condition_matched" class="p-3 bg-blue-50 border border-blue-200 rounded-md">
                <div class="flex items-start">
                  <div class="flex-shrink-0">
                    <CheckCircle class="w-5 h-5 text-blue-500 mt-0.5" />
                  </div>
                  <div class="ml-3 flex-1">
                    <Label class="text-sm font-medium text-blue-700">Computed Value</Label>
                    <div class="mt-1 bg-background rounded p-2 font-mono text-sm border">
                      {{ formatValue(testResult.result_value) }}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Error Result -->
            <div v-else class="p-3 bg-destructive/5 border border-destructive/50 rounded-md">
              <div class="flex items-start">
                <div class="flex-shrink-0">
                  <XCircle class="w-5 h-5 text-destructive mt-0.5" />
                </div>
                <div class="ml-3">
                  <Label class="text-sm font-medium text-destructive">Rule Evaluation Error</Label>
                  <p class="text-sm text-destructive/80 mt-1">{{ testResult.error }}</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <!-- Loading -->
        <Card v-if="testing">
          <CardContent class="flex items-center justify-center py-8">
            <div class="animate-spin rounded-full h-6 w-6 border-2 border-primary border-t-transparent"></div>
            <span class="ml-3 text-muted-foreground">Testing rule...</span>
          </CardContent>
        </Card>
      </CardContent>

      <!-- Footer -->
      <CardFooter class="flex items-center justify-between bg-muted/30">
        <p class="text-sm text-muted-foreground">
          Enter sample transaction data and click "Run Test" to see how your rule behaves
        </p>
        
        <div class="flex items-center space-x-3">
          <Button 
            @click="$emit('close')"
            variant="outline"
          >
            Close
          </Button>
          <Button 
            @click="runTest"
            :disabled="!isValidJson || testing"
          >
            <TestTube class="w-4 h-4 mr-2" />
            Run Test
          </Button>
        </div>
      </CardFooter>
    </Card>
  </div>
</template>

<script>
import { ref, computed, toRefs, onMounted } from 'vue'
import { X, TestTube, CheckCircle, AlertCircle, XCircle, RefreshCw, Copy } from 'lucide-vue-next'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

export default {
  name: 'RuleTestDialog',
  components: {
    X,
    TestTube,
    CheckCircle,
    AlertCircle,
    XCircle,
    RefreshCw,
    Copy,
    Card,
    CardContent,
    CardDescription,
    CardFooter,
    CardHeader,
    CardTitle,
    Button,
    Badge,
    Label,
    Textarea,
    Input,
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue
  },
  props: {
    rule: {
      type: Object,
      required: true
    },
    transactionFields: {
      type: Array,
      default: () => []
    }
  },
  emits: ['close'],
  setup(props) {
    const { rule, transactionFields } = toRefs(props)
    
    // State
    const sampleDataJson = ref('')
    const jsonError = ref('')
    const testResult = ref(null)
    const testing = ref(false)
    
    // Transaction selector state
    const dataSource = ref('manual') // 'manual' or 'transaction'
    const availableTransactions = ref([])
    const selectedTransactionId = ref('')
    const selectedTransaction = ref(null)
    const loadingTransactions = ref(false)
    const transactionSearchQuery = ref('')
    const filteredTransactions = ref([])

    // Computed
    const isValidJson = computed(() => {
      if (!sampleDataJson.value.trim()) return false
      
      try {
        JSON.parse(sampleDataJson.value)
        jsonError.value = ''
        return true
      } catch (e) {
        jsonError.value = e.message
        return false
      }
    })

    // Methods
    const loadSampleData = () => {
      // Create sample data based on available fields
      const sampleData = {}
      
      const allFields = transactionFields.value.all || []
      
      if (allFields.length > 0) {
        // Add some common fields with sample values
        allFields.slice(0, 8).forEach(field => {
          // Use sample values from metadata if available
          if (field.sample_values && field.sample_values.length > 0) {
            sampleData[field.name] = field.sample_values[0]
          } else {
            // Fallback to common field names
            switch (field.name.toLowerCase()) {
              case 'merchant':
                sampleData[field.name] = 'Amazon'
                break
              case 'amount':
                sampleData[field.name] = '25.99'
                break
              case 'date':
                sampleData[field.name] = '2024-01-15'
                break
              case 'description':
                sampleData[field.name] = 'Online purchase'
                break
              case 'category':
                sampleData[field.name] = 'Shopping'
                break
              case 'type':
                sampleData[field.name] = 'debit'
                break
              default:
                sampleData[field.name] = 'sample_value'
            }
          }
        })
      } else {
        // Fallback sample data
        sampleData.merchant = 'Amazon'
        sampleData.amount = '25.99'
        sampleData.date = '2024-01-15'
        sampleData.description = 'Online purchase'
      }
      
      sampleDataJson.value = JSON.stringify(sampleData, null, 2)
    }

    const clearSampleData = () => {
      sampleDataJson.value = ''
      testResult.value = null
      jsonError.value = ''
    }

    const insertField = (fieldName) => {
      const textarea = document.querySelector('textarea[placeholder*="sample transaction"]')
      if (!textarea) return
      
      const start = textarea.selectionStart
      const end = textarea.selectionEnd
      const text = sampleDataJson.value
      
      const fieldJson = `"${fieldName}": "sample_value"`
      
      // If JSON is empty, start with basic structure
      if (!text.trim()) {
        sampleDataJson.value = `{\n  ${fieldJson}\n}`
      } else {
        // Try to insert the field appropriately
        try {
          const parsed = JSON.parse(text)
          // Only add if field doesn't already exist
          if (!(fieldName in parsed)) {
            parsed[fieldName] = 'sample_value'
            sampleDataJson.value = JSON.stringify(parsed, null, 2)
          }
        } catch {
          // If JSON is invalid, just append the field
          sampleDataJson.value = text + `\n"${fieldName}": "sample_value",`
        }
      }
      
      setTimeout(() => textarea.focus())
    }

    const runTest = async () => {
      if (!isValidJson.value) return
      
      try {
        testing.value = true
        testResult.value = null
        
        const sampleData = JSON.parse(sampleDataJson.value)
        
        // Ensure we have a complete rule object with all required fields
        const completeRule = {
          name: rule.value.name || 'Test Rule',
          description: rule.value.description || '',
          target_field: rule.value.target_field || 'test_field',
          condition: rule.value.condition || '',
          action: rule.value.action || '',
          rule_type: rule.value.rule_type || 'formula',
          priority: rule.value.priority || 100,
          active: rule.value.active !== undefined ? rule.value.active : true
        }
        
        const response = await fetch('/api/rules/test', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            rule: completeRule,
            sample_transaction: sampleData
          })
        })
        
        if (!response.ok) {
          const errorData = await response.json()
          throw new Error(errorData.detail || 'Failed to test rule')
        }
        
        testResult.value = await response.json()
        
      } catch (error) {
        testResult.value = {
          success: false,
          condition_matched: false,
          error: error.message
        }
      } finally {
        testing.value = false
      }
    }

    const formatValue = (value) => {
      if (value === null || value === undefined) {
        return 'null'
      }
      if (typeof value === 'string') {
        return `"${value}"`
      }
      if (typeof value === 'object') {
        return JSON.stringify(value, null, 2)
      }
      return String(value)
    }

    // Transaction selector methods
    const setDataSource = (source) => {
      dataSource.value = source
      if (source === 'transaction' && availableTransactions.value.length === 0) {
        loadTransactions()
      }
    }

    const loadTransactions = async () => {
      try {
        loadingTransactions.value = true
        const response = await fetch('/api/transactions/?limit=50')
        if (!response.ok) throw new Error('Failed to load transactions')
        const data = await response.json()
        availableTransactions.value = data.transactions
        filteredTransactions.value = data.transactions
      } catch (error) {
        console.error('Error loading transactions:', error)
      } finally {
        loadingTransactions.value = false
      }
    }

    const filterTransactions = () => {
      if (!transactionSearchQuery.value.trim()) {
        filteredTransactions.value = availableTransactions.value
        return
      }
      
      const query = transactionSearchQuery.value.toLowerCase()
      filteredTransactions.value = availableTransactions.value.filter(transaction => {
        const content = transaction.ingested_content || {}
        const searchableText = [
          content.merchant || '',
          content.description || '',
          content.amount || '',
          transaction.statement.filename || ''
        ].join(' ').toLowerCase()
        
        return searchableText.includes(query)
      })
    }

    const getTransactionPreview = (transaction) => {
      const content = transaction.ingested_content || {}
      const preview = {}
      
      // Show up to 3 key fields for preview
      const keyFields = ['merchant', 'amount', 'description', 'date', 'type']
      let count = 0
      
      for (const field of keyFields) {
        if (content[field] && count < 3) {
          preview[field] = String(content[field]).substring(0, 20)
          count++
        }
      }
      
      return preview
    }

    const loadSelectedTransaction = async (transactionId) => {
      if (!transactionId) return
      
      try {
        const response = await fetch(`/api/transactions/${transactionId}`)
        if (!response.ok) throw new Error('Failed to load transaction')
        const transaction = await response.json()
        selectedTransaction.value = transaction
        
        // Convert transaction data to JSON for testing
        const transactionData = {
          ...transaction.ingested_content,
          ...transaction.computed_content
        }
        sampleDataJson.value = JSON.stringify(transactionData, null, 2)
      } catch (error) {
        console.error('Error loading transaction:', error)
      }
    }

    const getTransactionDisplayName = (transaction) => {
      const content = transaction.ingested_content || {}
      const merchant = content.merchant || content.description || 'Unknown'
      const amount = content.amount || ''
      return `${merchant} ${amount ? `(${amount})` : ''}`.trim()
    }

    const formatDate = (dateString) => {
      return new Date(dateString).toLocaleDateString()
    }

    const copyToClipboard = async (text) => {
      try {
        await navigator.clipboard.writeText(text)
        // You could add a toast notification here if available
        console.log('JSON copied to clipboard')
      } catch (error) {
        console.error('Failed to copy to clipboard:', error)
      }
    }

    const getFieldTooltip = (field) => {
      const parts = []
      if (field.description) parts.push(field.description)
      if (field.sample_values && field.sample_values.length > 0) {
        parts.push(`Sample: ${field.sample_values.slice(0, 3).join(', ')}`)
      }
      return parts.join(' | ')
    }

    // Lifecycle
    onMounted(() => {
      loadSampleData()
    })

    return {
      sampleDataJson,
      jsonError,
      testResult,
      testing,
      isValidJson,
      loadSampleData,
      clearSampleData,
      insertField,
      runTest,
      formatValue,
      dataSource,
      availableTransactions,
      selectedTransactionId,
      selectedTransaction,
      loadingTransactions,
      transactionSearchQuery,
      filteredTransactions,
      setDataSource,
      loadTransactions,
      loadSelectedTransaction,
      getTransactionDisplayName,
      formatDate,
      filterTransactions,
      getTransactionPreview,
      copyToClipboard,
      getFieldTooltip
    }
  }
}
</script>
