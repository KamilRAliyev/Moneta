<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useAlert } from '@/composables/useAlert.js'
import { useFormulas } from '@/composables/useFormulas.js'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

const { 
  success, 
  error, 
  warning, 
  info, 
  confirm, 
  showAlert, 
  dismissAll 
} = useAlert()

// Formulas composable
const { 
  state: formulasState,
  getCommands,
  getCategories,
  executeCommand,
  getAvailableFields,
  testDateInfer,
  testAmountToFloat,
  testMathOperation,
  initFormulas
} = useFormulas()

// Test data
const customAlert = {
  type: 'info',
  title: '',
  message: '',
  duration: 5000,
  persistent: false
}

const testBasicAlerts = () => {
  success('This is a success alert!')
  error('This is an error alert!')
  warning('This is a warning alert!')
  info('This is an info alert!')
}

const testPersistentAlerts = () => {
  error('This error alert will stay until manually dismissed', { persistent: true })
  warning('This warning alert will also stay', { persistent: true })
}

const testCustomDuration = () => {
  info('This alert will disappear in 2 seconds', { duration: 2000 })
  success('This alert will disappear in 10 seconds', { duration: 10000 })
}

const testConfirmation = async () => {
  const confirmed = await confirm('Are you sure you want to proceed with this action?', {
    confirmLabel: 'Yes, proceed',
    cancelLabel: 'No, cancel'
  })
  
  if (confirmed) {
    success('Action confirmed!')
  } else {
    info('Action cancelled')
  }
}

const testCustomAlert = () => {
  showAlert({
    type: customAlert.type,
    title: customAlert.title || undefined,
    message: customAlert.message,
    duration: customAlert.duration,
    persistent: customAlert.persistent,
    actions: [
      {
        label: 'Action 1',
        variant: 'default',
        action: () => success('Action 1 clicked!')
      },
      {
        label: 'Action 2',
        variant: 'outline',
        action: () => warning('Action 2 clicked!')
      }
    ]
  })
}

const testMultipleAlerts = () => {
  for (let i = 1; i <= 5; i++) {
    setTimeout(() => {
      info(`Alert number ${i}`)
    }, i * 500)
  }
}

const testLongMessage = () => {
  showAlert({
    type: 'warning',
    title: 'Long Message Test',
    message: 'This is a very long message that should wrap properly and not overflow the container. It contains multiple sentences to test how the alert component handles longer content. The alert should expand vertically to accommodate the text while maintaining proper spacing and readability.',
    persistent: true
  })
}

// Formulas test data
const formulasTest = reactive({
  selectedCommand: '',
  commandArgs: '',
  dateInput: '2024-01-15 14:30:00',
  amountInput: '$1,234.56',
  mathLeft: 100,
  mathRight: 25,
  mathOperation: 'add',
  lastResult: null,
  executing: false,
  // Chained commands test data
  chainedTest: {
    moneyIn: '$1,500.00',
    moneyOut: '$200.50',
    fee: '$5.95',
    result: null,
    executing: false
  },
  // Regex test data
  regexTest: {
    pattern: '\\d+',
    text: 'Price: $123.45',
    returnAll: false,
    groupIndex: 0,
    result: null,
    executing: false,
    // Preset examples
    examples: [
      { name: 'Extract Numbers', pattern: '\\d+', text: 'Price: $123.45', returnAll: false, groupIndex: 0 },
      { name: 'Extract Dollar Amount', pattern: '\\$(\\d+\\.\\d{2})', text: 'Total: $99.99', returnAll: false, groupIndex: 1 },
      { name: 'Extract Email', pattern: '[A-Za-z]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}', text: 'Contact: john@example.com', returnAll: false, groupIndex: 0 },
      { name: 'Find All Uppercase Words', pattern: '\\b[A-Z]{2,}\\b', text: 'The USA and UK are countries', returnAll: true, groupIndex: 0 },
      { name: 'Extract Date Parts', pattern: '(\\d{4})-(\\d{2})-(\\d{2})', text: 'Date: 2024-01-15', returnAll: false, groupIndex: 1 },
      { name: 'Find All Numbers', pattern: '\\d+', text: 'Numbers: 123, 456, 789', returnAll: true, groupIndex: 0 },
      { name: 'Extract Phone Number', pattern: '(\\d{3})-(\\d{3})-(\\d{4})', text: 'Call me at 555-123-4567', returnAll: false, groupIndex: 0 },
      { name: 'Find All Emails', pattern: '[A-Za-z]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}', text: 'Emails: john@example.com, jane@test.org', returnAll: true, groupIndex: 0 }
    ]
  }
})

// Initialize formulas on mount
onMounted(() => {
  initFormulas().catch(err => {
    error(`Failed to load formulas: ${err.message}`)
  })
})

// Formulas test functions
const testQuickCommands = async () => {
  formulasTest.executing = true
  try {
    const tests = [
      { name: 'date_infer', args: ['2024-01-15 2:30 PM'] },
      { name: 'amount_to_float', args: ['$1,234.56'] },
      { name: 'add', args: [100, 25] },
      { name: 'subtract', args: [100, 25] }
    ]

    for (const test of tests) {
      const result = await executeCommand(test.name, test.args)
      if (result.success) {
        success(`${test.name}: ${JSON.stringify(result.value)}`)
      } else {
        error(`${test.name} failed: ${result.error}`)
      }
    }
  } catch (err) {
    error(`Test failed: ${err.message}`)
  } finally {
    formulasTest.executing = false
  }
}

const testSelectedCommand = async () => {
  if (!formulasTest.selectedCommand) {
    warning('Please select a command first')
    return
  }

  formulasTest.executing = true
  try {
    let args = []
    if (formulasTest.commandArgs) {
      try {
        args = JSON.parse(`[${formulasTest.commandArgs}]`)
      } catch {
        args = [formulasTest.commandArgs] // Treat as single string argument
      }
    }

    const result = await executeCommand(formulasTest.selectedCommand, args)
    formulasTest.lastResult = result

    if (result.success) {
      success(`Result: ${JSON.stringify(result.value)}`, { duration: 8000 })
    } else {
      error(`Error: ${result.error}`)
    }
  } catch (err) {
    error(`Execution failed: ${err.message}`)
  } finally {
    formulasTest.executing = false
  }
}

const testDateParser = async () => {
  formulasTest.executing = true
  try {
    const result = await testDateInfer(formulasTest.dateInput)
    formulasTest.lastResult = result
    
    if (result.success) {
      success(`Parsed date: ${result.value}`, { duration: 8000 })
    } else {
      error(`Date parsing failed: ${result.error}`)
    }
  } catch (err) {
    error(`Date test failed: ${err.message}`)
  } finally {
    formulasTest.executing = false
  }
}

const testAmountParser = async () => {
  formulasTest.executing = true
  try {
    const result = await testAmountToFloat(formulasTest.amountInput)
    formulasTest.lastResult = result
    
    if (result.success) {
      success(`Parsed amount: ${result.value}`, { duration: 8000 })
    } else {
      error(`Amount parsing failed: ${result.error}`)
    }
  } catch (err) {
    error(`Amount test failed: ${err.message}`)
  } finally {
    formulasTest.executing = false
  }
}

const testMathOp = async () => {
  formulasTest.executing = true
  try {
    const result = await testMathOperation(
      formulasTest.mathOperation, 
      parseFloat(formulasTest.mathLeft), 
      parseFloat(formulasTest.mathRight)
    )
    formulasTest.lastResult = result
    
    if (result.success) {
      success(`${formulasTest.mathLeft} ${formulasTest.mathOperation} ${formulasTest.mathRight} = ${result.value}`, { duration: 8000 })
    } else {
      error(`Math operation failed: ${result.error}`)
    }
  } catch (err) {
    error(`Math test failed: ${err.message}`)
  } finally {
    formulasTest.executing = false
  }
}

const loadFormulasData = async () => {
  try {
    await initFormulas()
    success('Formulas data reloaded successfully')
  } catch (err) {
    error(`Failed to reload formulas: ${err.message}`)
  }
}

// Chained commands test functions
const testChainedCommands = async () => {
  formulasTest.chainedTest.executing = true
  formulasTest.chainedTest.result = null
  
  try {
    // Step 1: Convert all amounts to float
    const moneyInResult = await testAmountToFloat(formulasTest.chainedTest.moneyIn)
    const moneyOutResult = await testAmountToFloat(formulasTest.chainedTest.moneyOut)
    const feeResult = await testAmountToFloat(formulasTest.chainedTest.fee)
    
    if (!moneyInResult.success || !moneyOutResult.success || !feeResult.success) {
      error('Failed to parse one or more amounts')
      return
    }
    
    const moneyInFloat = moneyInResult.value
    const moneyOutFloat = moneyOutResult.value
    const feeFloat = feeResult.value
    
    // Step 2: Calculate net amount: money_in - money_out - fee
    const subtract1Result = await testMathOperation('subtract', moneyInFloat, moneyOutFloat)
    if (!subtract1Result.success) {
      error('Failed to subtract money_out from money_in')
      return
    }
    
    const netBeforeFee = subtract1Result.value
    const finalResult = await testMathOperation('subtract', netBeforeFee, feeFloat)
    
    if (!finalResult.success) {
      error('Failed to subtract fee from net amount')
      return
    }
    
    // Store the complete result
    formulasTest.chainedTest.result = {
      success: true,
      steps: [
        { step: 'Parse money_in', input: formulasTest.chainedTest.moneyIn, output: moneyInFloat },
        { step: 'Parse money_out', input: formulasTest.chainedTest.moneyOut, output: moneyOutFloat },
        { step: 'Parse fee', input: formulasTest.chainedTest.fee, output: feeFloat },
        { step: 'Subtract money_out', input: `${moneyInFloat} - ${moneyOutFloat}`, output: netBeforeFee },
        { step: 'Subtract fee', input: `${netBeforeFee} - ${feeFloat}`, output: finalResult.value }
      ],
      finalAmount: finalResult.value,
      formula: `amount = subtract(subtract(amount_to_float(money_in), amount_to_float(money_out)), amount_to_float(fee))`
    }
    
    success(`Chained calculation complete: ${formulasTest.chainedTest.moneyIn} - ${formulasTest.chainedTest.moneyOut} - ${formulasTest.chainedTest.fee} = ${finalResult.value}`, { duration: 10000 })
    
  } catch (err) {
    error(`Chained test failed: ${err.message}`)
    formulasTest.chainedTest.result = { success: false, error: err.message }
  } finally {
    formulasTest.chainedTest.executing = false
  }
}

const testAlternativeFormula = async () => {
  formulasTest.chainedTest.executing = true
  formulasTest.chainedTest.result = null
  
  try {
    // Alternative: If amount exists, use it; otherwise calculate from money_in - money_out - fee
    const amountResult = await testAmountToFloat(formulasTest.chainedTest.moneyIn) // Using moneyIn as "amount" field
    
    if (amountResult.success && amountResult.value !== null) {
      // Amount exists, use it directly
      formulasTest.chainedTest.result = {
        success: true,
        steps: [
          { step: 'Amount exists', input: formulasTest.chainedTest.moneyIn, output: amountResult.value }
        ],
        finalAmount: amountResult.value,
        formula: `amount = amount_to_float(amount)`,
        note: 'Amount field exists, using directly'
      }
      success(`Amount found: ${amountResult.value}`, { duration: 8000 })
    } else {
      // No amount, calculate from components
      await testChainedCommands()
    }
    
  } catch (err) {
    error(`Alternative formula test failed: ${err.message}`)
    formulasTest.chainedTest.result = { success: false, error: err.message }
  } finally {
    formulasTest.chainedTest.executing = false
  }
}

// Regex test functions
const testRegexCommand = async () => {
  formulasTest.regexTest.executing = true
  formulasTest.regexTest.result = null
  
  try {
    const result = await executeCommand('regex', [
      formulasTest.regexTest.pattern,
      formulasTest.regexTest.text
    ], {
      return_all: formulasTest.regexTest.returnAll,
      group_index: Number(formulasTest.regexTest.groupIndex) || 0
    })
    
    formulasTest.regexTest.result = result
    
    if (result.success) {
      const resultType = Array.isArray(result.value) ? 'array' : typeof result.value
      const resultPreview = Array.isArray(result.value) 
        ? `[${result.value.length} items]` 
        : JSON.stringify(result.value)
      
      success(`Regex match found (${resultType}): ${resultPreview}`, { duration: 8000 })
    } else {
      error(`Regex failed: ${result.error}`)
    }
  } catch (err) {
    error(`Regex test failed: ${err.message}`)
    formulasTest.regexTest.result = { success: false, error: err.message }
  } finally {
    formulasTest.regexTest.executing = false
  }
}

const loadRegexExample = (example) => {
  formulasTest.regexTest.pattern = example.pattern
  formulasTest.regexTest.text = example.text
  formulasTest.regexTest.returnAll = example.returnAll
  formulasTest.regexTest.groupIndex = example.groupIndex
  formulasTest.regexTest.result = null
}

const testAllRegexExamples = async () => {
  formulasTest.regexTest.executing = true
  
  try {
    const results = []
    
    for (const example of formulasTest.regexTest.examples) {
      const result = await executeCommand('regex', [example.pattern, example.text], {
        return_all: example.returnAll,
        group_index: Number(example.groupIndex) || 0
      })
      
      results.push({
        name: example.name,
        success: result.success,
        value: result.value,
        error: result.error
      })
    }
    
    // Show summary
    const successCount = results.filter(r => r.success).length
    const totalCount = results.length
    
    if (successCount === totalCount) {
      success(`All ${totalCount} regex examples passed!`, { duration: 5000 })
    } else {
      warning(`${successCount}/${totalCount} regex examples passed`, { duration: 5000 })
    }
    
    // Show individual results
    results.forEach(result => {
      if (result.success) {
        const preview = Array.isArray(result.value) 
          ? `[${result.value.length} items]` 
          : JSON.stringify(result.value)
        info(`${result.name}: ${preview}`)
      } else {
        error(`${result.name}: ${result.error}`)
      }
    })
    
  } catch (err) {
    error(`Regex examples test failed: ${err.message}`)
  } finally {
    formulasTest.regexTest.executing = false
  }
}

const clearRegexResult = () => {
  formulasTest.regexTest.result = null
}
</script>

<template>
  <div class="p-6">
    <div class="mb-6">
      <h1 class="text-2xl font-bold mb-2">Testing Panel</h1>
      <p class="text-sm text-muted-foreground">Test various components and features</p>
    </div>

    <!-- Alert Testing Section -->
    <Card class="mb-6">
      <CardHeader class="pb-4">
        <CardTitle class="text-lg">Alert System Testing</CardTitle>
        <CardDescription>Test different alert types and configurations</CardDescription>
      </CardHeader>
      <CardContent>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
          <Button @click="() => success('Success!')" variant="outline" size="sm" class="text-xs">
            Success
          </Button>
          <Button @click="() => error('Error!')" variant="outline" size="sm" class="text-xs">
            Error
          </Button>
          <Button @click="() => warning('Warning!')" variant="outline" size="sm" class="text-xs">
            Warning
          </Button>
          <Button @click="() => info('Info!')" variant="outline" size="sm" class="text-xs">
            Info
          </Button>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
          <Button @click="testBasicAlerts" size="sm" class="text-xs">
            All Basic Alerts
          </Button>
          <Button @click="testPersistentAlerts" size="sm" class="text-xs">
            Persistent Alerts
          </Button>
          <Button @click="testMultipleAlerts" size="sm" class="text-xs">
            Multiple Alerts
          </Button>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
          <Button @click="testConfirmation" variant="outline" size="sm" class="text-xs">
            Test Confirmation
          </Button>
          <Button @click="dismissAll" variant="destructive" size="sm" class="text-xs">
            Dismiss All
          </Button>
        </div>

        <!-- Quick Custom Alert -->
        <div class="mt-4 p-3 border rounded-md bg-muted/50">
          <div class="text-sm font-medium mb-2">Quick Custom Alert</div>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-2 mb-2">
            <Select v-model="customAlert.type">
              <SelectTrigger class="h-8 text-xs">
                <SelectValue placeholder="Type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="success">Success</SelectItem>
                <SelectItem value="error">Error</SelectItem>
                <SelectItem value="warning">Warning</SelectItem>
                <SelectItem value="info">Info</SelectItem>
              </SelectContent>
            </Select>
            <Input 
              v-model="customAlert.message"
              placeholder="Alert message"
              class="h-8 text-xs"
            />
          </div>
          <div class="flex items-center gap-2">
            <Button @click="testCustomAlert" size="sm" class="text-xs">
              Show Alert
            </Button>
            <label class="flex items-center gap-1 text-xs">
              <input 
                v-model="customAlert.persistent"
                type="checkbox"
                class="w-3 h-3"
              />
              Persistent
            </label>
          </div>
        </div>
      </CardContent>
    </Card>

    <!-- Formulas Testing Section -->
    <Card class="mb-6">
      <CardHeader class="pb-4">
        <CardTitle class="text-lg">Formulas System Testing</CardTitle>
        <CardDescription>Test formula commands and data transformation functions</CardDescription>
      </CardHeader>
      <CardContent>
        <!-- Quick Tests -->
        <div class="mb-6">
          <div class="flex items-center justify-between mb-3">
            <div class="text-sm font-medium">Quick Tests</div>
            <div class="text-xs text-muted-foreground">
              Commands: {{ formulasState.commands.length }}, 
              Categories: {{ formulasState.categories.length }},
              Fields: {{ formulasState.availableFields.length }}
            </div>
          </div>
          
          <div class="grid grid-cols-2 md:grid-cols-4 gap-3 mb-3">
            <Button 
              @click="testQuickCommands" 
              variant="outline" 
              size="sm" 
              class="text-xs"
              :disabled="formulasTest.executing"
            >
              {{ formulasTest.executing ? 'Testing...' : 'Test All' }}
            </Button>
            <Button 
              @click="loadFormulasData" 
              variant="outline" 
              size="sm" 
              class="text-xs"
            >
              Reload Data
            </Button>
            <Button 
              @click="() => info(`Available commands: ${formulasState.commands.map(c => c.name).join(', ')}`)" 
              variant="outline" 
              size="sm" 
              class="text-xs"
            >
              List Commands
            </Button>
            <Button 
              @click="() => info(`Categories: ${formulasState.categories.join(', ')}`)" 
              variant="outline" 
              size="sm" 
              class="text-xs"
            >
              List Categories
            </Button>
          </div>
          
          <!-- Loading/Error States -->
          <div v-if="formulasState.loading" class="text-sm text-blue-600 mb-2">
            Loading formulas data...
          </div>
          <div v-if="formulasState.error" class="text-sm text-red-600 mb-2">
            Error: {{ formulasState.error }}
          </div>
        </div>

        <!-- Individual Command Tests -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
          <!-- Date Parsing Test -->
          <div class="p-3 border rounded-md bg-muted/50">
            <div class="text-sm font-medium mb-2">Date Parsing Test</div>
            <div class="space-y-2">
              <Input 
                v-model="formulasTest.dateInput"
                placeholder="Enter date string"
                class="h-8 text-xs"
              />
              <Button 
                @click="testDateParser" 
                size="sm" 
                class="w-full text-xs"
                :disabled="formulasTest.executing"
              >
                Test date_infer
              </Button>
            </div>
          </div>

          <!-- Amount Parsing Test -->
          <div class="p-3 border rounded-md bg-muted/50">
            <div class="text-sm font-medium mb-2">Amount Parsing Test</div>
            <div class="space-y-2">
              <Input 
                v-model="formulasTest.amountInput"
                placeholder="Enter amount string"
                class="h-8 text-xs"
              />
              <Button 
                @click="testAmountParser" 
                size="sm" 
                class="w-full text-xs"
                :disabled="formulasTest.executing"
              >
                Test amount_to_float
              </Button>
            </div>
          </div>

          <!-- Math Operations Test -->
          <div class="p-3 border rounded-md bg-muted/50">
            <div class="text-sm font-medium mb-2">Math Operations Test</div>
            <div class="space-y-2">
              <div class="grid grid-cols-3 gap-1">
                <Input 
                  v-model.number="formulasTest.mathLeft"
                  type="number"
                  placeholder="Left"
                  class="h-8 text-xs"
                />
                <Select v-model="formulasTest.mathOperation">
                  <SelectTrigger class="h-8 text-xs">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="add">+</SelectItem>
                    <SelectItem value="subtract">-</SelectItem>
                    <SelectItem value="multiply">×</SelectItem>
                    <SelectItem value="divide">÷</SelectItem>
                  </SelectContent>
                </Select>
                <Input 
                  v-model.number="formulasTest.mathRight"
                  type="number"
                  placeholder="Right"
                  class="h-8 text-xs"
                />
              </div>
              <Button 
                @click="testMathOp" 
                size="sm" 
                class="w-full text-xs"
                :disabled="formulasTest.executing"
              >
                Calculate
              </Button>
            </div>
          </div>

          <!-- Custom Command Test -->
          <div class="p-3 border rounded-md bg-muted/50">
            <div class="text-sm font-medium mb-2">Custom Command Test</div>
            <div class="space-y-2">
              <Select v-model="formulasTest.selectedCommand">
                <SelectTrigger class="h-8 text-xs">
                  <SelectValue placeholder="Select command" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem 
                    v-for="command in formulasState.commands" 
                    :key="command.name"
                    :value="command.name"
                  >
                    {{ command.name }} ({{ command.category }})
                  </SelectItem>
                </SelectContent>
              </Select>
              <Input 
                v-model="formulasTest.commandArgs"
                placeholder="Arguments (comma-separated or JSON)"
                class="h-8 text-xs"
              />
              <Button 
                @click="testSelectedCommand" 
                size="sm" 
                class="w-full text-xs"
                :disabled="formulasTest.executing || !formulasTest.selectedCommand"
              >
                Execute Command
              </Button>
            </div>
          </div>
        </div>

        <!-- Last Result Display -->
        <div v-if="formulasTest.lastResult" class="p-3 border rounded-md bg-slate-50 dark:bg-slate-800">
          <div class="text-sm font-medium mb-2">Last Result</div>
          <div class="text-xs font-mono">
            <div class="mb-1">
              <span class="font-semibold">Success:</span> 
              <span :class="formulasTest.lastResult.success ? 'text-green-600' : 'text-red-600'">
                {{ formulasTest.lastResult.success }}
              </span>
            </div>
            <div v-if="formulasTest.lastResult.value !== null" class="mb-1">
              <span class="font-semibold">Value:</span> 
              <span class="text-blue-600">{{ JSON.stringify(formulasTest.lastResult.value) }}</span>
            </div>
            <div v-if="formulasTest.lastResult.error" class="mb-1">
              <span class="font-semibold">Error:</span> 
              <span class="text-red-600">{{ formulasTest.lastResult.error }}</span>
            </div>
          </div>
        </div>

        <!-- Command Examples -->
        <div v-if="formulasTest.selectedCommand && formulasState.commandsMap.get(formulasTest.selectedCommand)" class="mt-4 p-3 border rounded-md bg-blue-50 dark:bg-blue-950">
          <div class="text-sm font-medium mb-2">Selected Command Examples</div>
          <div class="text-xs space-y-1">
            <div v-for="example in formulasState.commandsMap.get(formulasTest.selectedCommand)?.examples || []" :key="example">
              <code class="text-blue-700 dark:text-blue-300">{{ example }}</code>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>

    <!-- Chained Commands Testing Section -->
    <Card class="mb-6">
      <CardHeader class="pb-4">
        <CardTitle class="text-lg">Chained Commands Testing</CardTitle>
        <CardDescription>Test complex formulas with multiple chained commands like money_in - money_out - fee</CardDescription>
      </CardHeader>
      <CardContent>
        <!-- Transaction Fields Input -->
        <div class="mb-6">
          <div class="text-sm font-medium mb-3">Transaction Fields</div>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <Label for="moneyIn" class="text-xs text-muted-foreground">Money In</Label>
              <Input 
                id="moneyIn"
                v-model="formulasTest.chainedTest.moneyIn"
                placeholder="e.g., $1,500.00"
                class="h-8 text-xs"
              />
            </div>
            <div>
              <Label for="moneyOut" class="text-xs text-muted-foreground">Money Out</Label>
              <Input 
                id="moneyOut"
                v-model="formulasTest.chainedTest.moneyOut"
                placeholder="e.g., $200.50"
                class="h-8 text-xs"
              />
            </div>
            <div>
              <Label for="fee" class="text-xs text-muted-foreground">Fee</Label>
              <Input 
                id="fee"
                v-model="formulasTest.chainedTest.fee"
                placeholder="e.g., $5.95"
                class="h-8 text-xs"
              />
            </div>
          </div>
        </div>

        <!-- Test Buttons -->
        <div class="mb-6">
          <div class="flex flex-wrap gap-3">
            <Button 
              @click="testChainedCommands" 
              size="sm" 
              class="text-xs"
              :disabled="formulasTest.chainedTest.executing"
            >
              {{ formulasTest.chainedTest.executing ? 'Calculating...' : 'Test Chained Formula' }}
            </Button>
            <Button 
              @click="testAlternativeFormula" 
              variant="outline" 
              size="sm" 
              class="text-xs"
              :disabled="formulasTest.chainedTest.executing"
            >
              Test Alternative (Amount First)
            </Button>
            <Button 
              @click="() => { formulasTest.chainedTest.result = null }" 
              variant="outline" 
              size="sm" 
              class="text-xs"
            >
              Clear Results
            </Button>
          </div>
        </div>

        <!-- Results Display -->
        <div v-if="formulasTest.chainedTest.result" class="space-y-4">
          <!-- Final Result -->
          <div class="p-4 border rounded-md bg-green-50 dark:bg-green-950">
            <div class="text-sm font-medium mb-2 text-green-800 dark:text-green-200">
              {{ formulasTest.chainedTest.result.success ? '✅ Calculation Complete' : '❌ Calculation Failed' }}
            </div>
            <div v-if="formulasTest.chainedTest.result.success" class="text-lg font-bold text-green-700 dark:text-green-300">
              Final Amount: {{ formulasTest.chainedTest.result.finalAmount }}
            </div>
            <div v-if="formulasTest.chainedTest.result.error" class="text-sm text-red-600">
              Error: {{ formulasTest.chainedTest.result.error }}
            </div>
          </div>

          <!-- Formula Used -->
          <div v-if="formulasTest.chainedTest.result.formula" class="p-3 border rounded-md bg-slate-50 dark:bg-slate-800">
            <div class="text-sm font-medium mb-2">Formula Used</div>
            <code class="text-xs text-blue-700 dark:text-blue-300">{{ formulasTest.chainedTest.result.formula }}</code>
            <div v-if="formulasTest.chainedTest.result.note" class="text-xs text-muted-foreground mt-1">
              {{ formulasTest.chainedTest.result.note }}
            </div>
          </div>

          <!-- Step-by-Step Results -->
          <div v-if="formulasTest.chainedTest.result.steps" class="p-3 border rounded-md bg-blue-50 dark:bg-blue-950">
            <div class="text-sm font-medium mb-3">Step-by-Step Execution</div>
            <div class="space-y-2">
              <div 
                v-for="(step, index) in formulasTest.chainedTest.result.steps" 
                :key="index"
                class="flex items-center justify-between p-2 bg-white dark:bg-slate-800 rounded text-xs"
              >
                <div class="font-medium">{{ step.step }}</div>
                <div class="text-muted-foreground">{{ step.input }} → {{ step.output }}</div>
              </div>
            </div>
          </div>
        </div>

        <!-- Example Scenarios -->
        <div class="mt-6 p-3 border rounded-md bg-yellow-50 dark:bg-yellow-950">
          <div class="text-sm font-medium mb-2">Example Scenarios</div>
          <div class="text-xs space-y-1 text-yellow-800 dark:text-yellow-200">
            <div><strong>Scenario 1:</strong> Money In: $1,500.00, Money Out: $200.50, Fee: $5.95 → Result: $1,293.55</div>
            <div><strong>Scenario 2:</strong> Money In: $(500.00), Money Out: $100.00, Fee: $10.00 → Result: -$610.00</div>
            <div><strong>Scenario 3:</strong> Money In: $2,000.00, Money Out: $(100.00), Fee: $50.00 → Result: $2,050.00</div>
          </div>
        </div>
      </CardContent>
    </Card>

    <!-- Regex Testing Section -->
    <Card class="mb-6">
      <CardHeader class="pb-4">
        <CardTitle class="text-lg">Regex Command Testing</CardTitle>
        <CardDescription>Test the regex command with custom patterns and text extraction</CardDescription>
      </CardHeader>
      <CardContent>
        <!-- Quick Tests -->
        <div class="mb-6">
          <div class="flex items-center justify-between mb-3">
            <div class="text-sm font-medium">Quick Tests</div>
            <div class="text-xs text-muted-foreground">
              Test regex patterns and text extraction
            </div>
          </div>
          
          <div class="grid grid-cols-2 md:grid-cols-3 gap-3 mb-3">
            <Button 
              @click="testRegexCommand" 
              variant="outline" 
              size="sm" 
              class="text-xs"
              :disabled="formulasTest.regexTest.executing"
            >
              {{ formulasTest.regexTest.executing ? 'Testing...' : 'Test Regex' }}
            </Button>
            <Button 
              @click="testAllRegexExamples" 
              variant="outline" 
              size="sm" 
              class="text-xs"
              :disabled="formulasTest.regexTest.executing"
            >
              Test All Examples
            </Button>
            <Button 
              @click="clearRegexResult" 
              variant="outline" 
              size="sm" 
              class="text-xs"
            >
              Clear Results
            </Button>
          </div>
        </div>

        <!-- Regex Input Form -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
          <!-- Pattern Input -->
          <div class="p-3 border rounded-md bg-muted/50">
            <div class="text-sm font-medium mb-2">Regex Pattern</div>
            <div class="space-y-2">
              <Textarea 
                v-model="formulasTest.regexTest.pattern"
                placeholder="Enter regex pattern (e.g., \d+, \$(.*), [A-Z]+)"
                class="h-16 text-xs font-mono"
                rows="3"
              />
              <div class="text-xs text-muted-foreground">
                Use standard regex syntax. Groups: (group), Quantifiers: +, *, ?, {n}
              </div>
            </div>
          </div>

          <!-- Text Input -->
          <div class="p-3 border rounded-md bg-muted/50">
            <div class="text-sm font-medium mb-2">Text to Search</div>
            <div class="space-y-2">
              <Textarea 
                v-model="formulasTest.regexTest.text"
                placeholder="Enter text to search in"
                class="h-16 text-xs"
                rows="3"
              />
              <div class="text-xs text-muted-foreground">
                The text that will be searched with the regex pattern
              </div>
            </div>
          </div>
        </div>

        <!-- Options -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          <div class="p-3 border rounded-md bg-muted/50">
            <div class="text-sm font-medium mb-2">Options</div>
            <div class="space-y-3">
              <div class="flex items-center space-x-2">
                <input 
                  v-model="formulasTest.regexTest.returnAll"
                  type="checkbox"
                  id="returnAll"
                  class="w-4 h-4"
                />
                <label for="returnAll" class="text-xs">Return all matches (not just first)</label>
              </div>
              <div class="space-y-1">
                <label for="groupIndex" class="text-xs text-muted-foreground">Group Index</label>
                <Input 
                  id="groupIndex"
                  v-model.number="formulasTest.regexTest.groupIndex"
                  type="number"
                  min="0"
                  placeholder="0"
                  class="h-8 text-xs"
                />
                <div class="text-xs text-muted-foreground">
                  0 = full match, 1+ = capture groups
                </div>
              </div>
            </div>
          </div>

          <!-- Preset Examples -->
          <div class="p-3 border rounded-md bg-muted/50">
            <div class="text-sm font-medium mb-2">Preset Examples</div>
            <div class="space-y-2 max-h-32 overflow-y-auto">
              <Button 
                v-for="example in formulasTest.regexTest.examples" 
                :key="example.name"
                @click="loadRegexExample(example)"
                variant="outline"
                size="sm"
                class="w-full text-xs justify-start h-8"
              >
                {{ example.name }}
              </Button>
            </div>
          </div>
        </div>

        <!-- Results Display -->
        <div v-if="formulasTest.regexTest.result" class="space-y-4">
          <!-- Result Summary -->
          <div class="p-4 border rounded-md" :class="formulasTest.regexTest.result.success ? 'bg-green-50 dark:bg-green-950' : 'bg-red-50 dark:bg-red-950'">
            <div class="text-sm font-medium mb-2" :class="formulasTest.regexTest.result.success ? 'text-green-800 dark:text-green-200' : 'text-red-800 dark:text-red-200'">
              {{ formulasTest.regexTest.result.success ? '✅ Regex Match Found' : '❌ Regex Failed' }}
            </div>
            
            <div v-if="formulasTest.regexTest.result.success" class="space-y-2">
              <div class="text-xs">
                <span class="font-semibold">Pattern:</span> 
                <code class="ml-1 text-blue-700 dark:text-blue-300">{{ formulasTest.regexTest.pattern }}</code>
              </div>
              <div class="text-xs">
                <span class="font-semibold">Text:</span> 
                <span class="ml-1">{{ formulasTest.regexTest.text }}</span>
              </div>
              <div class="text-xs">
                <span class="font-semibold">Options:</span> 
                <span class="ml-1">
                  return_all={{ formulasTest.regexTest.returnAll }}, 
                  group_index={{ formulasTest.regexTest.groupIndex }}
                </span>
              </div>
              <div class="text-xs">
                <span class="font-semibold">Result:</span> 
                <code class="ml-1 text-green-700 dark:text-green-300">
                  {{ Array.isArray(formulasTest.regexTest.result.value) 
                      ? `[${formulasTest.regexTest.result.value.length} items]` 
                      : JSON.stringify(formulasTest.regexTest.result.value) }}
                </code>
              </div>
            </div>
            
            <div v-if="!formulasTest.regexTest.result.success" class="text-sm text-red-600">
              Error: {{ formulasTest.regexTest.result.error }}
            </div>
          </div>

          <!-- Detailed Results -->
          <div v-if="formulasTest.regexTest.result.success && formulasTest.regexTest.result.value" class="p-3 border rounded-md bg-slate-50 dark:bg-slate-800">
            <div class="text-sm font-medium mb-2">Detailed Results</div>
            <div class="text-xs font-mono">
              <div v-if="Array.isArray(formulasTest.regexTest.result.value)">
                <div v-for="(item, index) in formulasTest.regexTest.result.value" :key="index" class="mb-1">
                  [{{ index }}]: {{ JSON.stringify(item) }}
                </div>
              </div>
              <div v-else>
                {{ JSON.stringify(formulasTest.regexTest.result.value) }}
              </div>
            </div>
          </div>
        </div>

        <!-- Regex Help -->
        <div class="mt-6 p-3 border rounded-md bg-blue-50 dark:bg-blue-950">
          <div class="text-sm font-medium mb-2">Regex Help</div>
          <div class="text-xs space-y-1 text-blue-800 dark:text-blue-200">
            <div><strong>Basic patterns:</strong> \d (digits), \w (word chars), \s (whitespace), . (any char)</div>
            <div><strong>Quantifiers:</strong> + (1+), * (0+), ? (0-1), {n} (exactly n), {n,m} (n to m)</div>
            <div><strong>Groups:</strong> (pattern) creates capture group, (?:pattern) non-capturing</div>
            <div><strong>Anchors:</strong> ^ (start), $ (end), \b (word boundary)</div>
            <div><strong>Character classes:</strong> [abc] (any of a,b,c), [a-z] (range), [^abc] (not a,b,c)</div>
          </div>
        </div>
      </CardContent>
    </Card>

    <!-- Future Testing Sections -->
    <Card>
      <CardHeader class="pb-4">
        <CardTitle class="text-lg">Other Component Tests</CardTitle>
        <CardDescription>More testing features will be added here</CardDescription>
      </CardHeader>
      <CardContent>
        <div class="text-center py-8 text-muted-foreground">
          <p class="text-sm">Additional testing panels will be added as new components are developed</p>
        </div>
      </CardContent>
    </Card>
  </div>
</template>
