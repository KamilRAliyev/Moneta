<template>
  <div class="h-full flex flex-col">
    <!-- Header -->
    <div class="bg-background border-b px-6 py-4 flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold">Computed Field Rules</h1>
        <p class="text-sm text-muted-foreground mt-1">
          Manage rules for computing transaction field values based on conditions and formulas
        </p>
      </div>
      <div class="flex items-center space-x-3">
        <div class="relative w-48">
          <Input
            v-model="targetFieldInput"
            placeholder="Select or create computed field..."
            class="pr-8"
            @focus="showTargetFieldDropdown = true"
            @blur="handleTargetFieldBlur"
            @input="handleTargetFieldInput"
          />
          <Button
            v-if="targetFieldInput && targetFieldInput !== 'all'"
            @click="clearTargetField"
            variant="ghost"
            size="icon"
            class="absolute right-0 top-0 h-full w-8 px-0"
          >
            <X class="w-3 h-3" />
          </Button>
          
          <!-- Dropdown for suggestions -->
          <div
            v-if="showTargetFieldDropdown && (targetFieldSuggestions.length > 0 || targetFieldInput)"
            class="absolute z-50 w-full mt-1 bg-popover border rounded-md shadow-md max-h-60 overflow-y-auto"
          >
            <div
              @click="selectTargetField('all')"
              class="px-3 py-2 hover:bg-accent cursor-pointer text-sm border-b"
              :class="{ 'bg-accent': selectedTargetField === 'all' }"
            >
              <span class="font-medium">All Target Fields</span>
              <span class="text-muted-foreground text-xs block">Show all rules</span>
            </div>
            
            <div v-if="targetFieldSuggestions.length > 0" class="border-b">
              <div class="px-3 py-1 text-xs text-muted-foreground bg-muted/50">
                Existing Fields
              </div>
              <div
                v-for="field in targetFieldSuggestions"
                :key="field"
                @click="selectTargetField(field)"
                class="px-3 py-2 hover:bg-accent cursor-pointer text-sm"
                :class="{ 'bg-accent': selectedTargetField === field }"
              >
                {{ field }}
              </div>
            </div>
            
            <div v-if="targetFieldInput && !targetFields.includes(targetFieldInput) && targetFieldInput !== 'all'" class="border-t">
              <div class="px-3 py-1 text-xs text-muted-foreground bg-muted/50">
                Create New
              </div>
              <div
                @click="selectTargetField(targetFieldInput)"
                class="px-3 py-2 hover:bg-accent cursor-pointer text-sm"
              >
                <span class="font-medium">Create:</span> 
                <code class="ml-1 text-primary">{{ targetFieldInput }}</code>
              </div>
            </div>
          </div>
        </div>
        <Button @click="openCreateRuleDialog">
          <Plus class="w-4 h-4 mr-2" />
          New Rule
        </Button>
        <div class="flex items-center gap-2">
          <Checkbox 
            v-model="forceReprocess" 
            id="force-reprocess"
            :disabled="loading"
          />
          <Label for="force-reprocess" class="text-sm">Force Reprocess</Label>
        </div>
        <Button @click="executeRules" :disabled="loading" variant="secondary">
          <Play class="w-4 h-4 mr-2" />
          Execute Rules
        </Button>
        <Button @click="showTransactionPreview = !showTransactionPreview" variant="outline">
          <Eye class="w-4 h-4 mr-2" />
          Preview Transactions
        </Button>
      </div>
    </div>

    <div class="flex-1 flex overflow-hidden">
      <!-- Left Panel - Rules List -->
      <Card class="w-1/3 rounded-none border-r border-t-0">
        <CardHeader>
          <CardTitle class="text-base">Rules</CardTitle>
          <p class="text-xs text-muted-foreground">
            {{ filteredRules.length }} rules (sorted by priority)
          </p>
        </CardHeader>
        
        <CardContent class="flex-1 overflow-y-auto p-0">
          <div v-if="loading" class="p-4 text-center text-muted-foreground">
            Loading rules...
          </div>
          
          <div v-else-if="filteredRules.length === 0" class="p-4 text-center text-muted-foreground">
            <FileX class="w-8 h-8 mx-auto mb-2 opacity-50" />
            No rules found
          </div>
          
          <div v-else>
              <div 
                v-for="(rule, index) in filteredRules" 
                :key="rule.id"
                draggable="true"
                @dragstart="handleDragStart($event, rule, index)"
                @dragend="handleDragEnd"
                @dragover="handleDragOver"
                @drop="handleDrop($event, rule, index)"
                @click="selectRule(rule)"
                class="p-4 border-b cursor-pointer transition-colors hover:bg-muted/50 group relative"
                :class="{ 
                  'bg-muted border-primary': selectedRule?.id === rule.id,
                  'opacity-50': draggedRule?.id === rule.id
                }"
              >
                <!-- Drag Handle -->
                <div class="absolute left-1 top-1/2 transform -translate-y-1/2 opacity-0 group-hover:opacity-100 transition-opacity cursor-move">
                  <GripVertical class="w-4 h-4 text-muted-foreground hover:text-foreground" />
                </div>
              <div class="flex items-start justify-between">
                <div class="flex-1 min-w-0">
                  <div class="flex items-center">
                    <span class="text-sm font-medium truncate">{{ rule.name }}</span>
                    <Badge 
                      :variant="rule.active ? 'default' : 'secondary'" 
                      class="ml-2 text-xs"
                    >
                      {{ rule.active ? 'Active' : 'Inactive' }}
                    </Badge>
                  </div>
                  
                  <div class="flex items-center mt-1 space-x-2">
                    <Badge variant="outline" class="text-xs">
                      {{ rule.target_field }}
                    </Badge>
                    <span class="text-xs text-muted-foreground">
                      Priority: {{ rule.priority }}
                    </span>
                  </div>
                  
                  <div class="flex items-center mt-2 space-x-2">
                    <Badge 
                      :variant="getRuleTypeVariant(rule.rule_type)"
                      class="text-xs"
                    >
                      {{ getRuleTypeLabel(rule.rule_type) }}
                    </Badge>
                    
                    <span v-if="rule.condition" class="text-xs text-muted-foreground italic">
                      "{{ truncateText(rule.condition, 30) }}"
                    </span>
                    <span v-else class="text-xs text-muted-foreground">
                      No condition (always applies)
                    </span>
                  </div>
                </div>
                
                <div class="flex items-center space-x-1 ml-2">
                  <Button 
                    @click.stop="editRule(rule)"
                    variant="ghost"
                    size="icon"
                    class="h-8 w-8"
                  >
                    <Edit class="w-4 h-4" />
                  </Button>
                  <Button 
                    @click.stop="deleteRule(rule)"
                    variant="ghost"
                    size="icon"
                    class="h-8 w-8"
                  >
                    <Trash2 class="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <!-- Right Panel - Rule Editor -->
      <Card class="flex-1 rounded-none border-l-0 border-t-0">
        <div v-if="!selectedRule" class="flex-1 flex items-center justify-center text-muted-foreground h-96">
          <div class="text-center">
            <Settings class="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p class="text-lg font-medium mb-2">Select a rule to edit</p>
            <p class="text-sm">Choose a rule from the left panel or create a new one</p>
          </div>
        </div>

        <div v-else class="flex flex-col h-full">
          <!-- Rule Editor Header -->
          <CardHeader>
            <div class="flex items-center justify-between">
              <CardTitle>{{ selectedRule.name }}</CardTitle>
              <div class="flex items-center space-x-2">
                <Button 
                  @click="testRule"
                  variant="outline"
                  size="sm"
                >
                  <TestTube class="w-4 h-4 mr-1" />
                  Test Rule
                </Button>
                <Button 
                  @click="saveRule"
                  size="sm"
                  :disabled="!hasUnsavedChanges"
                >
                  <Save class="w-4 h-4 mr-1" />
                  Save
                </Button>
              </div>
            </div>
          </CardHeader>

          <!-- Rule Editor Form -->
          <CardContent class="flex-1 overflow-y-auto">
            <div class="space-y-6">
              <!-- Transaction Reference Section -->
              <Card>
                <CardHeader class="pb-3">
                  <CardTitle class="text-base">Transaction Reference</CardTitle>
                  <p class="text-sm text-muted-foreground">
                    Select a transaction to reference while building your rule
                  </p>
                </CardHeader>
                <CardContent class="space-y-4">
                  <div class="flex space-x-2">
                    <div class="flex-1">
                      <Input
                        v-model="ruleTransactionSearchQuery"
                        placeholder="Search transactions..."
                        class="mb-2"
                        @input="filterRuleTransactions"
                      />
                      <Select v-model="selectedRuleTransactionId" @update:model-value="loadSelectedRuleTransaction">
                        <SelectTrigger>
                          <SelectValue placeholder="Select a transaction to reference..." />
                        </SelectTrigger>
                        <SelectContent class="max-h-60">
                          <SelectItem 
                            v-for="transaction in filteredRuleTransactions" 
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
                      @click="loadRuleTransactions"
                      :disabled="loadingRuleTransactions"
                      variant="outline"
                      size="sm"
                    >
                      <RefreshCw class="w-4 h-4" :class="{ 'animate-spin': loadingRuleTransactions }" />
                    </Button>
                  </div>
                  
                  <!-- Selected Transaction Preview -->
                  <div v-if="selectedRuleTransaction" class="p-3 bg-muted/50 rounded-md">
                    <div class="flex items-center justify-between mb-2">
                      <h6 class="font-medium text-sm">Selected Transaction:</h6>
                      <Button 
                        @click="copyToClipboard(JSON.stringify(selectedRuleTransaction, null, 2))"
                        variant="outline"
                        size="sm"
                      >
                        <Copy class="w-4 h-4 mr-1" />
                        Copy JSON
                      </Button>
                    </div>
                    <div class="text-xs text-muted-foreground mb-2">
                      <div><strong>ID:</strong> {{ selectedRuleTransaction.id }}</div>
                      <div><strong>Statement:</strong> {{ selectedRuleTransaction.statement.filename }}</div>
                      <div><strong>Created:</strong> {{ formatDate(selectedRuleTransaction.created_at) }}</div>
                    </div>
                    
                    <div class="space-y-2">
                      <div>
                        <h6 class="font-medium text-xs text-muted-foreground mb-1">Ingested Content:</h6>
                        <div class="bg-background p-2 rounded font-mono text-xs max-h-32 overflow-y-auto border">
                          <pre>{{ JSON.stringify(selectedRuleTransaction.ingested_content, null, 2) }}</pre>
                        </div>
                      </div>
                      <div v-if="selectedRuleTransaction.computed_content">
                        <h6 class="font-medium text-xs text-muted-foreground mb-1">Computed Content:</h6>
                        <div class="bg-background p-2 rounded font-mono text-xs max-h-32 overflow-y-auto border">
                          <pre>{{ JSON.stringify(selectedRuleTransaction.computed_content, null, 2) }}</pre>
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <!-- Rule Editor -->
              <RuleEditor 
                v-if="selectedRule"
                :key="selectedRule.id"
                :rule="selectedRule"
                :transaction-fields="transactionFields"
                :formula-commands="formulaCommands"
                :reference-transaction="selectedRuleTransaction"
                @update:rule="updateSelectedRule"
                @test="testRule"
              />
            </div>
          </CardContent>
        </div>
      </Card>
    </div>

    <!-- Create/Edit Rule Dialog -->
    <RuleDialog
      v-if="showRuleDialog"
      :rule="dialogRule"
      :transaction-fields="transactionFields"
      :formula-commands="formulaCommands"
      @save="handleRuleSave"
      @close="closeRuleDialog"
    />

    <!-- Test Rule Dialog -->
    <RuleTestDialog
      v-if="showTestDialog"
      :rule="testDialogRule"
      :transaction-fields="transactionFields"
      @close="closeTestDialog"
    />

    <!-- Transaction Preview Panel -->
    <div v-if="showTransactionPreview" class="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
      <Card class="max-w-6xl w-full max-h-[90vh] overflow-hidden">
        <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-4">
          <CardTitle class="text-xl">Transaction Preview</CardTitle>
          <Button @click="showTransactionPreview = false" variant="ghost" size="icon">
            <X class="w-4 h-4" />
          </Button>
        </CardHeader>
        
        <CardContent class="overflow-y-auto max-h-[calc(90vh-200px)]">
          <div v-if="loadingTransactions" class="flex items-center justify-center py-8">
            <div class="animate-spin rounded-full h-6 w-6 border-2 border-primary border-t-transparent"></div>
            <span class="ml-3 text-muted-foreground">Loading transactions...</span>
          </div>
          
          <div v-else-if="previewTransactions.length === 0" class="text-center py-8 text-muted-foreground">
            <FileX class="w-8 h-8 mx-auto mb-2 opacity-50" />
            No transactions found
          </div>
          
          <div v-else class="space-y-4">
            <div class="flex items-center justify-between">
              <p class="text-sm text-muted-foreground">
                Showing {{ previewTransactions.length }} transactions
              </p>
              <Button @click="loadPreviewTransactions" variant="outline" size="sm">
                <RefreshCw class="w-4 h-4 mr-2" :class="{ 'animate-spin': loadingTransactions }" />
                Refresh
              </Button>
            </div>
            
            <div class="grid gap-4">
              <div 
                v-for="transaction in previewTransactions" 
                :key="transaction.id"
                class="p-4 border rounded-lg hover:bg-muted/50 transition-colors"
              >
                <div class="flex items-start justify-between mb-2">
                  <div class="flex-1">
                    <h4 class="font-medium">{{ getTransactionDisplayName(transaction) }}</h4>
                    <p class="text-sm text-muted-foreground">
                      {{ transaction.statement.filename }} • {{ formatDate(transaction.created_at) }}
                    </p>
                  </div>
                  <Button 
                    @click="testWithTransaction(transaction)"
                    variant="outline"
                    size="sm"
                  >
                    <TestTube class="w-4 h-4 mr-1" />
                    Test Rule
                  </Button>
                </div>
                
                <div class="space-y-4 text-sm">
                  <div>
                    <div class="flex items-center justify-between mb-2">
                      <h5 class="font-medium text-muted-foreground">Complete Transaction Data</h5>
                      <Button 
                        @click="copyToClipboard(JSON.stringify(transaction, null, 2))"
                        variant="outline"
                        size="sm"
                      >
                        <Copy class="w-4 h-4 mr-1" />
                        Copy JSON
                      </Button>
                    </div>
                    <div class="bg-muted/50 p-3 rounded font-mono text-xs max-h-96 overflow-y-auto">
                      <pre>{{ JSON.stringify(transaction, null, 2) }}</pre>
                    </div>
                  </div>
                  
                  <div class="grid grid-cols-2 gap-4">
                    <div>
                      <h5 class="font-medium text-muted-foreground mb-2">Ingested Content</h5>
                      <div class="bg-muted/50 p-2 rounded font-mono text-xs max-h-48 overflow-y-auto">
                        <pre>{{ JSON.stringify(transaction.ingested_content, null, 2) }}</pre>
                      </div>
                    </div>
                    <div>
                      <h5 class="font-medium text-muted-foreground mb-2">Computed Content</h5>
                      <div class="bg-muted/50 p-2 rounded font-mono text-xs max-h-48 overflow-y-auto">
                        <pre>{{ JSON.stringify(transaction.computed_content, null, 2) }}</pre>
                      </div>
                    </div>
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
import { useRouter } from 'vue-router'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Checkbox } from '@/components/ui/checkbox'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { useAlert } from '@/composables/useAlert'
import RuleEditor from '@/components/rules/RuleEditor.vue'
import RuleDialog from '@/components/rules/RuleDialog.vue'
import RuleTestDialog from '@/components/rules/RuleTestDialog.vue'

// Icons
import { Plus, Play, Edit, Trash2, Settings, FileX, TestTube, Save, GripVertical, X, Eye, RefreshCw, Copy } from 'lucide-vue-next'

export default {
  name: 'ComputedFieldRules',
  components: {
    Badge,
    Button,
    Card,
    CardContent,
    CardHeader,
    CardTitle,
    Checkbox,
    Input,
    Label,
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
    RuleEditor,
    RuleDialog,
    RuleTestDialog,
    Plus,
    Play,
    Edit,
    Trash2,
    Settings,
    FileX,
    TestTube,
    Save,
    GripVertical,
    X,
    Eye,
    RefreshCw,
    Copy
  },
  setup() {
    const router = useRouter()
    const { showAlert } = useAlert()
    
    // State
    const loading = ref(false)
    const rules = ref([])
    const selectedRule = ref(null)
    const forceReprocess = ref(false)
    
    const selectedTargetField = ref('all')
    const targetFieldInput = ref('All Target Fields')
    const showTargetFieldDropdown = ref(false)
    const transactionFields = ref([])
    const formulaCommands = ref([])
    const targetFields = ref([])
    const hasUnsavedChanges = ref(false)
    
    // Dialog state
    const showRuleDialog = ref(false)
    const dialogRule = ref(null)
    const showTestDialog = ref(false)
    const testDialogRule = ref(null)
    
    // Transaction preview state
    const showTransactionPreview = ref(false)
    const previewTransactions = ref([])
    const loadingTransactions = ref(false)
    
    // Rule transaction reference state
    const ruleTransactions = ref([])
    const filteredRuleTransactions = ref([])
    const selectedRuleTransactionId = ref('')
    const selectedRuleTransaction = ref(null)
    const ruleTransactionSearchQuery = ref('')
    const loadingRuleTransactions = ref(false)

    // Computed
    const filteredRules = computed(() => {
      if (!selectedTargetField.value || selectedTargetField.value === 'all') return rules.value
      return rules.value.filter(rule => rule.target_field === selectedTargetField.value)
    })

    const targetFieldSuggestions = computed(() => {
      if (!targetFieldInput.value || targetFieldInput.value === 'All Target Fields') {
        return targetFields.value
      }
      return targetFields.value.filter(field => 
        field.toLowerCase().includes(targetFieldInput.value.toLowerCase())
      )
    })

    // Drag and drop state
    const draggedRule = ref(null)
    const draggedIndex = ref(-1)
    
    const handleDragStart = (e, rule, index) => {
      draggedRule.value = rule
      draggedIndex.value = index
      e.dataTransfer.effectAllowed = 'move'
      e.dataTransfer.setData('text/html', e.target.outerHTML)
      e.target.classList.add('dragging')
    }
    
    const handleDragEnd = (e) => {
      e.target.classList.remove('dragging')
      draggedRule.value = null
      draggedIndex.value = -1
    }
    
    const handleDragOver = (e) => {
      e.preventDefault()
      e.dataTransfer.dropEffect = 'move'
    }
    
    const handleDrop = async (e, targetRule, targetIndex) => {
      e.preventDefault()
      
      if (draggedIndex.value === -1 || draggedIndex.value === targetIndex) {
        return
      }
      
      await reorderRules(draggedIndex.value, targetIndex)
    }

    // Target field dropdown methods
    const selectTargetField = (field) => {
      selectedTargetField.value = field
      targetFieldInput.value = field === 'all' ? 'All Target Fields' : field
      showTargetFieldDropdown.value = false
    }

    const handleTargetFieldInput = (event) => {
      const value = event.target.value
      targetFieldInput.value = value
      
      // Update selected field based on input
      if (value === 'All Target Fields' || value === '') {
        selectedTargetField.value = 'all'
      } else if (targetFields.value.includes(value)) {
        selectedTargetField.value = value
      } else {
        // New field name - use it directly
        selectedTargetField.value = value
      }
      
      showTargetFieldDropdown.value = true
    }

    const handleTargetFieldBlur = () => {
      // Delay hiding to allow clicks on dropdown items
      setTimeout(() => {
        showTargetFieldDropdown.value = false
      }, 200)
    }

    const clearTargetField = () => {
      targetFieldInput.value = 'All Target Fields'
      selectedTargetField.value = 'all'
      showTargetFieldDropdown.value = false
    }

    // Methods
    const loadRules = async () => {
      try {
        loading.value = true
        const response = await fetch('/api/rules')
        if (!response.ok) throw new Error('Failed to load rules')
        rules.value = await response.json()
        
        // Extract unique target fields
        targetFields.value = [...new Set(rules.value.map(rule => rule.target_field))].sort()
      } catch (error) {
        showAlert('Error loading rules: ' + error.message, 'error')
      } finally {
        loading.value = false
      }
    }

    const loadTransactionFields = async () => {
      try {
        const response = await fetch('/api/formulas/fields')
        if (!response.ok) throw new Error('Failed to load transaction fields')
        const data = await response.json()
        
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
        const response = await fetch('/api/formulas/commands')
        if (!response.ok) throw new Error('Failed to load formula commands')
        formulaCommands.value = await response.json()
      } catch (error) {
        console.error('Error loading formula commands:', error)
      }
    }

    const selectRule = (rule) => {
      if (hasUnsavedChanges.value) {
        if (!confirm('You have unsaved changes. Discard them?')) {
          return
        }
      }
      selectedRule.value = { ...rule }
      hasUnsavedChanges.value = false
      
      // Load transactions for rule reference
      if (ruleTransactions.value.length === 0) {
        loadRuleTransactions()
      }
    }

    const reorderRules = async (oldIndex, newIndex) => {
      try {
        const rulesArray = [...filteredRules.value]
        const movedRule = rulesArray[oldIndex]
        
        // Calculate new priority based on position
        let newPriority
        if (newIndex === 0) {
          // Move to first position - priority lower than current first
          newPriority = rulesArray[0].priority - 10
        } else if (newIndex === rulesArray.length - 1) {
          // Move to last position - priority higher than current last
          newPriority = rulesArray[rulesArray.length - 1].priority + 10
        } else {
          // Move to middle - priority between neighbors
          const prevRule = rulesArray[newIndex - (newIndex > oldIndex ? 0 : 1)]
          const nextRule = rulesArray[newIndex + (newIndex > oldIndex ? 1 : 0)]
          newPriority = Math.round((prevRule.priority + nextRule.priority) / 2)
        }
        
        // Ensure priority is positive
        if (newPriority <= 0) newPriority = 1
        
        // Update the rule via API
        const response = await fetch(`/api/rules/${movedRule.id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            ...movedRule,
            priority: newPriority
          })
        })
        
        if (!response.ok) {
          throw new Error('Failed to update rule priority')
        }
        
        // Reload rules to get updated order
        await loadRules()
        
        showAlert(`Rule "${movedRule.name}" priority updated to ${newPriority}`, 'success', { duration: 2000 })
        
      } catch (error) {
        showAlert('Error reordering rules: ' + error.message, 'error')
        // Reload to reset order
        await loadRules()
      }
    }

    const updateSelectedRule = (updatedRule) => {
      selectedRule.value = updatedRule
      hasUnsavedChanges.value = true
    }

    const openCreateRuleDialog = () => {
      // Use the current input value as target field if it's not 'all'
      let targetField = ''
      if (selectedTargetField.value && selectedTargetField.value !== 'all') {
        targetField = selectedTargetField.value
      }
      
      // Navigate to CreateRule page with target_field query param
      router.push({ 
        path: '/rules/create',
        query: targetField ? { target_field: targetField } : {}
      })
    }

    const editRule = (rule) => {
      // Navigate to EditRule page with rule id
      router.push(`/rules/edit/${rule.id}`)
    }

    const closeRuleDialog = () => {
      showRuleDialog.value = false
      dialogRule.value = null
    }

    const handleRuleSave = async (ruleData) => {
      try {
        const isEdit = !!ruleData.id
        const url = isEdit ? `/api/rules/${ruleData.id}` : '/api/rules'
        const method = isEdit ? 'PUT' : 'POST'
        
        const response = await fetch(url, {
          method,
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(ruleData)
        })
        
        if (!response.ok) {
          const errorData = await response.json()
          throw new Error(errorData.detail || 'Failed to save rule')
        }
        
        const savedRule = await response.json()
        
        if (isEdit) {
          const index = rules.value.findIndex(r => r.id === savedRule.id)
          if (index !== -1) rules.value[index] = savedRule
          if (selectedRule.value?.id === savedRule.id) {
            selectedRule.value = { ...savedRule }
            hasUnsavedChanges.value = false
          }
        } else {
          rules.value.push(savedRule)
        }
        
        closeRuleDialog()
        showAlert(isEdit ? 'Rule updated successfully' : 'Rule created successfully', 'success')
        
        // Update target fields list
        targetFields.value = [...new Set(rules.value.map(rule => rule.target_field))].sort()
        
      } catch (error) {
        showAlert('Error saving rule: ' + error.message, 'error')
      }
    }

    const deleteRule = async (rule) => {
      if (!confirm(`Are you sure you want to delete the rule "${rule.name}"?`)) {
        return
      }
      
      try {
        const response = await fetch(`/api/rules/${rule.id}`, {
          method: 'DELETE'
        })
        
        if (!response.ok) throw new Error('Failed to delete rule')
        
        rules.value = rules.value.filter(r => r.id !== rule.id)
        if (selectedRule.value?.id === rule.id) {
          selectedRule.value = null
          hasUnsavedChanges.value = false
        }
        
        showAlert('Rule deleted successfully', 'success')
        
        // Update target fields list
        targetFields.value = [...new Set(rules.value.map(rule => rule.target_field))].sort()
        
      } catch (error) {
        showAlert('Error deleting rule: ' + error.message, 'error')
      }
    }

    const testRule = () => {
      testDialogRule.value = selectedRule.value || dialogRule.value
      showTestDialog.value = true
    }

    const closeTestDialog = () => {
      showTestDialog.value = false
      testDialogRule.value = null
    }

    const saveRule = async () => {
      if (!selectedRule.value || !hasUnsavedChanges.value) return
      
      try {
        const response = await fetch(`/api/rules/${selectedRule.value.id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(selectedRule.value)
        })
        
        if (!response.ok) {
          const errorData = await response.json()
          throw new Error(errorData.detail || 'Failed to save rule')
        }
        
        const savedRule = await response.json()
        
        // Update the rule in the rules list
        const index = rules.value.findIndex(r => r.id === savedRule.id)
        if (index !== -1) {
          rules.value[index] = savedRule
        }
        
        // Update the selected rule
        selectedRule.value = { ...savedRule }
        hasUnsavedChanges.value = false
        
        showAlert('✅ Rule saved successfully', 'success')
        
      } catch (error) {
        showAlert('❌ Error saving rule: ' + error.message, 'error')
      }
    }

    const executeRules = async () => {
      if (!confirm('Execute all active rules against transactions? This will compute field values.')) {
        return
      }
      
      try {
        loading.value = true
        showAlert('Executing rules... This may take a few seconds.', 'info', { duration: 3000 })
        
        const requestBody = {
          dry_run: false,
          force_reprocess: forceReprocess.value
        }
        
        if (selectedTargetField.value && selectedTargetField.value !== 'all') {
          requestBody.target_fields = [selectedTargetField.value]
        }
        
        const response = await fetch('/api/rules/execute', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(requestBody)
        })
        
        if (!response.ok) throw new Error('Failed to execute rules')
        
        const result = await response.json()
        
        if (result.success) {
          const processedCount = result.processed_transactions || 0
          const updatedFields = Object.keys(result.updated_fields || {})
          const updatedCount = Object.values(result.updated_fields || {}).reduce((sum, count) => sum + count, 0)
          
          const message = `✅ Rule execution completed!\n\n📊 Results:\n• Processed: ${processedCount} transactions\n• Updated: ${updatedCount} field values\n• Fields affected: ${updatedFields.length > 0 ? updatedFields.join(', ') : 'None'}`
          showAlert(message, 'success', { duration: 8000 })
          
          // Reload rules to show updated data
          await loadRules()
        } else {
          const errorMessage = result.errors && result.errors.length > 0 
            ? result.errors.join('\n')
            : 'Unknown error occurred during rule execution'
          showAlert(`⚠️ Rule execution completed with errors:\n\n${errorMessage}`, 'warning', { duration: 10000 })
        }
        
      } catch (error) {
        showAlert(`❌ Error executing rules: ${error.message}`, 'error', { duration: 8000 })
      } finally {
        loading.value = false
      }
    }

    // Utility methods
    const getRuleTypeLabel = (ruleType) => {
      const labels = {
        formula: 'Formula',
        model_mapping: 'Model',
        value_assignment: 'Value'
      }
      return labels[ruleType] || ruleType
    }

    const getRuleTypeVariant = (ruleType) => {
      const variants = {
        formula: 'default',
        model_mapping: 'secondary',
        value_assignment: 'outline'
      }
      return variants[ruleType] || 'default'
    }

    const truncateText = (text, maxLength) => {
      if (text.length <= maxLength) return text
      return text.substring(0, maxLength) + '...'
    }

    const getTransactionPreview = (transaction) => {
      if (!transaction) return {}
      
      const preview = {}
      
      // Add some key fields from ingested_content
      if (transaction.ingested_content) {
        const ingested = transaction.ingested_content
        if (ingested.amount) preview.amount = ingested.amount
        if (ingested.description) preview.description = ingested.description
        if (ingested.date) preview.date = ingested.date
        if (ingested.type) preview.type = ingested.type
      }
      
      // Add some key fields from computed_content
      if (transaction.computed_content) {
        const computed = transaction.computed_content
        Object.keys(computed).forEach(key => {
          if (computed[key] !== null && computed[key] !== undefined) {
            preview[key] = computed[key]
          }
        })
      }
      
      return preview
    }

    // Lifecycle
    onMounted(() => {
      loadRules()
      loadTransactionFields()
      loadFormulaCommands()
    })

    // Watch for unsaved changes warning
    watch(hasUnsavedChanges, (hasChanges) => {
      if (hasChanges) {
        window.addEventListener('beforeunload', beforeUnload)
      } else {
        window.removeEventListener('beforeunload', beforeUnload)
      }
    })

    const beforeUnload = (e) => {
      e.preventDefault()
      e.returnValue = ''
    }

    // Transaction preview methods
    const loadPreviewTransactions = async () => {
      try {
        loadingTransactions.value = true
        const response = await fetch('/api/transactions/?limit=20')
        if (!response.ok) throw new Error('Failed to load transactions')
        const data = await response.json()
        previewTransactions.value = data.transactions
      } catch (error) {
        showAlert('Error loading transactions: ' + error.message, 'error')
      } finally {
        loadingTransactions.value = false
      }
    }

    const testWithTransaction = (transaction) => {
      if (!selectedRule.value) {
        showAlert('Please select a rule first', 'warning')
        return
      }
      
      // Set the transaction data in the test dialog
      testDialogRule.value = selectedRule.value
      showTestDialog.value = true
      
      // The test dialog will handle loading the transaction data
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
        showAlert('JSON copied to clipboard', 'success', { duration: 2000 })
      } catch (error) {
        showAlert('Failed to copy to clipboard', 'error')
      }
    }

    // Rule transaction reference methods
    const loadRuleTransactions = async () => {
      try {
        loadingRuleTransactions.value = true
        const response = await fetch('/api/transactions/?limit=50')
        if (!response.ok) throw new Error('Failed to load transactions')
        const data = await response.json()
        ruleTransactions.value = data.transactions
        filteredRuleTransactions.value = data.transactions
      } catch (error) {
        showAlert('Error loading transactions: ' + error.message, 'error')
      } finally {
        loadingRuleTransactions.value = false
      }
    }

    const filterRuleTransactions = () => {
      if (!ruleTransactionSearchQuery.value.trim()) {
        filteredRuleTransactions.value = ruleTransactions.value
        return
      }
      
      const query = ruleTransactionSearchQuery.value.toLowerCase()
      filteredRuleTransactions.value = ruleTransactions.value.filter(transaction => {
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

    const loadSelectedRuleTransaction = async (transactionId) => {
      if (!transactionId) {
        selectedRuleTransaction.value = null
        return
      }
      
      try {
        const response = await fetch(`/api/transactions/${transactionId}`)
        if (!response.ok) throw new Error('Failed to load transaction')
        const transaction = await response.json()
        selectedRuleTransaction.value = transaction
      } catch (error) {
        showAlert('Error loading transaction: ' + error.message, 'error')
      }
    }

    return {
      loading,
      rules,
      filteredRules,
      selectedRule,
      selectedTargetField,
      targetFields,
      targetFieldInput,
      showTargetFieldDropdown,
      targetFieldSuggestions,
      transactionFields,
      formulaCommands,
      hasUnsavedChanges,
      showRuleDialog,
      dialogRule,
      showTestDialog,
      testDialogRule,
      draggedRule,
      selectRule,
      updateSelectedRule,
      openCreateRuleDialog,
      editRule,
      closeRuleDialog,
      handleRuleSave,
      deleteRule,
      testRule,
      closeTestDialog,
      saveRule,
      executeRules,
      getRuleTypeLabel,
      getRuleTypeVariant,
      truncateText,
      handleDragStart,
      handleDragEnd,
      handleDragOver,
      handleDrop,
      selectTargetField,
      handleTargetFieldInput,
      handleTargetFieldBlur,
      clearTargetField,
      showTransactionPreview,
      previewTransactions,
      loadingTransactions,
      loadPreviewTransactions,
      testWithTransaction,
      getTransactionDisplayName,
      formatDate,
      copyToClipboard,
      ruleTransactions,
      filteredRuleTransactions,
      selectedRuleTransactionId,
      selectedRuleTransaction,
      ruleTransactionSearchQuery,
      loadingRuleTransactions,
      loadRuleTransactions,
      filterRuleTransactions,
      loadSelectedRuleTransaction,
      getTransactionPreview,
      forceReprocess
    }
  }
}
</script>

<style scoped>
.dragging {
  opacity: 0.5;
  transform: rotate(2deg);
}

[draggable="true"]:hover {
  cursor: grab;
}

[draggable="true"]:active {
  cursor: grabbing;
}
</style>
