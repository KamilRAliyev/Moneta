import { ref, reactive } from 'vue'
import api from '@/api/axios.js'
import { useAlert } from '@/composables/useAlert.js'

// Global formulas state
const formulasState = reactive({
  commands: [],
  categories: [],
  commandsMap: new Map(),
  availableFields: [],
  loading: false,
  error: null
})

export function useFormulas() {
  const { success, error: showError } = useAlert()
  
  // Get all available commands
  const getCommands = async () => {
    formulasState.loading = true
    formulasState.error = null
    
    try {
      const response = await api.get('/formulas/commands')
      formulasState.commands = response.data
      
      // Create a map for quick lookups
      formulasState.commandsMap.clear()
      response.data.forEach(cmd => {
        formulasState.commandsMap.set(cmd.name, cmd)
      })
      
      return response.data
    } catch (err) {
      formulasState.error = err.response?.data?.detail || 'Failed to fetch commands'
      throw err
    } finally {
      formulasState.loading = false
    }
  }
  
  // Get command categories
  const getCategories = async () => {
    try {
      const response = await api.get('/formulas/commands/categories')
      formulasState.categories = response.data.categories || []
      return response.data
    } catch (err) {
      formulasState.error = err.response?.data?.detail || 'Failed to fetch categories'
      throw err
    }
  }
  
  // Get specific command details
  const getCommand = async (commandName) => {
    try {
      const response = await api.get(`/formulas/commands/${commandName}`)
      return response.data
    } catch (err) {
      const errorMsg = err.response?.data?.detail || `Failed to fetch command: ${commandName}`
      formulasState.error = errorMsg
      throw err
    }
  }
  
  // Execute a command with arguments
  const executeCommand = async (commandName, args = [], kwargs = {}) => {
    try {
      const response = await api.post(`/formulas/commands/${commandName}/execute`, {
        command_name: commandName,
        args,
        kwargs
      })
      
      return response.data
    } catch (err) {
      const errorMsg = err.response?.data?.detail || `Failed to execute command: ${commandName}`
      formulasState.error = errorMsg
      throw err
    }
  }
  
  // Get available transaction fields
  const getAvailableFields = async () => {
    try {
      const response = await api.get('/formulas/fields')
      formulasState.availableFields = [
        ...(response.data.ingested_fields || []),
        ...(response.data.computed_fields || [])
      ]
      return response.data
    } catch (err) {
      formulasState.error = err.response?.data?.detail || 'Failed to fetch available fields'
      throw err
    }
  }
  
  // Test a formula (placeholder for now)
  const testFormula = async (formula, sampleData = {}) => {
    try {
      const response = await api.post('/formulas/test', {
        formula,
        sample_data: sampleData
      })
      return response.data
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Failed to test formula'
      formulasState.error = errorMsg
      throw err
    }
  }
  
  // Initialize formulas data
  const initFormulas = async () => {
    try {
      await Promise.all([
        getCommands(),
        getCategories(),
        getAvailableFields()
      ])
      success('Formulas data loaded successfully')
    } catch (err) {
      showError(`Failed to initialize formulas: ${err.message}`)
      throw err
    }
  }
  
  // Helper functions for UI
  const getCommandsByCategory = (category) => {
    return formulasState.commands.filter(cmd => cmd.category === category)
  }
  
  const getCommandExamples = (commandName) => {
    const command = formulasState.commandsMap.get(commandName)
    return command?.examples || []
  }
  
  const getCommandParameters = (commandName) => {
    const command = formulasState.commandsMap.get(commandName)
    return command?.parameters || []
  }
  
  // Test specific commands with sample data
  const testDateInfer = async (dateString) => {
    return await executeCommand('date_infer', [dateString])
  }
  
  const testAmountToFloat = async (amountString) => {
    return await executeCommand('amount_to_float', [amountString])
  }
  
  const testMathOperation = async (operation, left, right) => {
    const validOps = ['add', 'subtract', 'multiply', 'divide']
    if (!validOps.includes(operation)) {
      throw new Error(`Invalid operation: ${operation}`)
    }
    return await executeCommand(operation, [left, right])
  }
  
  // Build formula suggestions based on available fields
  const getFormulaSuggestions = () => {
    const suggestions = []
    const fields = formulasState.availableFields
    
    // Date parsing suggestions
    const dateFields = fields.filter(f => 
      f.name.toLowerCase().includes('date') || 
      f.sample_values?.some(v => typeof v === 'string' && /\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}/.test(v))
    )
    dateFields.forEach(field => {
      suggestions.push({
        formula: `parsed_date = date_infer(${field.name})`,
        description: `Parse ${field.name} field as date`,
        category: 'date'
      })
    })
    
    // Amount conversion suggestions  
    const amountFields = fields.filter(f => 
      f.name.toLowerCase().includes('amount') || 
      f.name.toLowerCase().includes('money') ||
      f.sample_values?.some(v => typeof v === 'string' && /[\$€£¥]/.test(v))
    )
    amountFields.forEach(field => {
      suggestions.push({
        formula: `${field.name}_float = amount_to_float(${field.name})`,
        description: `Convert ${field.name} to numeric value`,
        category: 'numeric'
      })
    })
    
    // Math operation suggestions
    const numericFields = amountFields.map(f => `amount_to_float(${f.name})`)
    if (numericFields.length >= 2) {
      suggestions.push({
        formula: `net_amount = subtract(${numericFields[0]}, ${numericFields[1]})`,
        description: 'Calculate net amount by subtracting values',
        category: 'math'
      })
    }
    
    return suggestions
  }
  
  // Clear error state
  const clearError = () => {
    formulasState.error = null
  }
  
  // Debug function to check the actual URL being used
  const debugAPICall = async () => {
    console.log('=== Debug API Call ===')
    const { useSettingsStore } = await import('@/stores/settings.js')
    const settingsStore = useSettingsStore()
    console.log('Settings Store Backend URL:', settingsStore.backendUrl)
    console.log('API Config:', api.defaults)
    
    try {
      const response = await api.get('/formulas/commands')
      console.log('Success! Response:', response.status)
      return response.data
    } catch (err) {
      console.error('Failed request details:')
      console.error('- URL:', err.config?.url)
      console.error('- Base URL:', err.config?.baseURL)
      console.error('- Full URL:', err.config?.baseURL + err.config?.url)
      console.error('- Error:', err.response?.status, err.response?.statusText)
      throw err
    }
  }
  
  return {
    // State
    state: formulasState,
    
    // Core API methods
    getCommands,
    getCategories, 
    getCommand,
    executeCommand,
    getAvailableFields,
    testFormula,
    initFormulas,
    
    // Helper methods
    getCommandsByCategory,
    getCommandExamples,
    getCommandParameters,
    
    // Test methods
    testDateInfer,
    testAmountToFloat,
    testMathOperation,
    
    // Utility methods
    getFormulaSuggestions,
    clearError
  }
}
