import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { statementsApi } from '@/api/statements.js'
import { useAlert } from '@/composables/useAlert.js'
import { useSettingsStore } from '@/stores/settings.js'

export const useStatementsStore = defineStore('statements', () => {
  const { success, error, warning } = useAlert()
  const settingsStore = useSettingsStore()
  
  // State
  const statements = ref([])
  const loading = ref(false)
  const uploadProgress = ref(0)
  const totalCount = ref(0)
  const currentPage = ref(0)
  const pageSize = ref(50)
  
  // Getters
  const processedStatements = computed(() => 
    statements.value.filter(stmt => stmt.processed)
  )
  
  const unprocessedStatements = computed(() => 
    statements.value.filter(stmt => !stmt.processed)
  )
  
  const hasStatements = computed(() => statements.value.length > 0)
  
  // Actions
  async function fetchStatements(page = 0, limit = 50) {
    loading.value = true
    try {
      const skip = page * limit
      const response = await statementsApi.getStatements({ skip, limit })
      
      statements.value = response.statements
      totalCount.value = response.total
      currentPage.value = page
      pageSize.value = limit
      
      return response
    } catch (err) {
      error('Failed to fetch statements', { persistent: true })
      throw err
    } finally {
      loading.value = false
    }
  }
  
  async function uploadStatement(file) {
    loading.value = true
    uploadProgress.value = 0
    
    try {
      const response = await statementsApi.uploadStatement(file)
      
      // Add to statements list
      const newStatement = {
        id: response.statement_id,
        filename: response.filename,
        file_hash: response.file_hash,
        mime_type: response.mime_type,
        processed: response.processed,
        columns: null,
        created_at: response.created_at
      }
      
      statements.value.unshift(newStatement)
      totalCount.value += 1
      uploadProgress.value = 100
      
      // Auto-process if enabled
      if (settingsStore.autoProcess) {
        try {
          await processStatement(newStatement.id)
        } catch (processError) {
          // Don't fail the upload if auto-processing fails
          console.warn('Auto-processing failed:', processError)
        }
      }
      
      success(`Statement "${file.name}" uploaded successfully`)
      return response
    } catch (err) {
      if (err.response?.status === 409) {
        warning(`Statement "${file.name}" already exists`)
      } else {
        error(`Failed to upload "${file.name}"`)
      }
      throw err
    } finally {
      loading.value = false
      setTimeout(() => uploadProgress.value = 0, 2000)
    }
  }
  
  async function uploadMultipleStatements(files) {
    loading.value = true
    uploadProgress.value = 0
    
    try {
      const response = await statementsApi.uploadMultipleStatements(files)
      
      // Add successful uploads to statements list
      const uploadedStatements = []
      response.results.successful_uploads.forEach(upload => {
        const newStatement = {
          id: upload.statement_id,
          filename: upload.filename,
          file_hash: upload.file_hash,
          mime_type: upload.mime_type,
          processed: false,
          columns: null,
          created_at: upload.created_at
        }
        statements.value.unshift(newStatement)
        uploadedStatements.push(newStatement)
      })
      
      totalCount.value += response.results.successful_count
      uploadProgress.value = 100
      
      // Auto-process if enabled
      if (settingsStore.autoProcess && uploadedStatements.length > 0) {
        try {
          // Process all uploaded statements
          for (const statement of uploadedStatements) {
            try {
              await processStatement(statement.id)
            } catch (processError) {
              console.warn(`Auto-processing failed for ${statement.filename}:`, processError)
            }
          }
        } catch (error) {
          console.warn('Auto-processing failed for some statements:', error)
        }
      }
      
      // Show results
      if (response.results.successful_count > 0) {
        success(`${response.results.successful_count} statements uploaded successfully`)
      }
      
      if (response.results.failed_count > 0) {
        error(`${response.results.failed_count} files failed to upload`)
      }
      
      if (response.results.duplicate_count > 0) {
        warning(`${response.results.duplicate_count} duplicate files skipped`)
      }
      
      return response
    } catch (err) {
      error('Failed to upload statements')
      throw err
    } finally {
      loading.value = false
      setTimeout(() => uploadProgress.value = 0, 2000)
    }
  }
  
  async function processStatement(statementId) {
    const statement = statements.value.find(s => s.id === statementId)
    if (!statement) return
    
    try {
      const response = await statementsApi.processStatement(statementId)
      
      // Update statement in store
      statement.processed = true
      
      const duplicatesSkipped = response.transactions_processed - response.transactions_created
      const message = duplicatesSkipped > 0 
        ? `Statement "${statement.filename}" processed successfully. ${response.transactions_created} transactions created, ${duplicatesSkipped} duplicates skipped.`
        : `Statement "${statement.filename}" processed successfully. ${response.transactions_created} transactions created.`
      
      success(message)
      return response
    } catch (err) {
      error(`Failed to process statement "${statement.filename}"`)
      throw err
    }
  }
  
  async function reprocessStatement(statementId) {
    const statement = statements.value.find(s => s.id === statementId)
    if (!statement) return
    
    try {
      // Reset processed status before reprocessing
      statement.processed = false
      
      const response = await statementsApi.processStatement(statementId)
      
      // Update statement in store
      statement.processed = true
      
      const duplicatesSkipped = response.transactions_processed - response.transactions_created
      const message = duplicatesSkipped > 0 
        ? `Statement "${statement.filename}" reprocessed successfully. ${response.transactions_created} transactions created, ${duplicatesSkipped} duplicates skipped.`
        : `Statement "${statement.filename}" reprocessed successfully. ${response.transactions_created} transactions created.`
      
      success(message)
      return response
    } catch (err) {
      error(`Failed to reprocess statement "${statement.filename}"`)
      throw err
    }
  }
  
  async function deleteStatement(statementId) {
    const statement = statements.value.find(s => s.id === statementId)
    if (!statement) return
    
    try {
      await statementsApi.deleteStatement(statementId)
      
      // Remove from store
      const index = statements.value.findIndex(s => s.id === statementId)
      if (index !== -1) {
        statements.value.splice(index, 1)
        totalCount.value -= 1
      }
      
      success(`Statement "${statement.filename}" deleted successfully`)
    } catch (err) {
      error(`Failed to delete statement "${statement.filename}"`)
      throw err
    }
  }
  
  async function getStatementTransactions(statementId) {
    try {
      const response = await statementsApi.getStatementTransactions(statementId)
      return response
    } catch (err) {
      error('Failed to fetch statement transactions')
      throw err
    }
  }
  
  function clearStatements() {
    statements.value = []
    totalCount.value = 0
    currentPage.value = 0
  }
  
  return {
    // State
    statements,
    loading,
    uploadProgress,
    totalCount,
    currentPage,
    pageSize,
    
    // Getters
    processedStatements,
    unprocessedStatements,
    hasStatements,
    
    // Actions
    fetchStatements,
    uploadStatement,
    uploadMultipleStatements,
    processStatement,
    reprocessStatement,
    deleteStatement,
    getStatementTransactions,
    clearStatements
  }
})
