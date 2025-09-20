import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { transactionsApi } from '@/api/transactions.js'
import { useAlert } from '@/composables/useAlert.js'

export const useTransactionsStore = defineStore('transactions', () => {
  const { success, error, warning } = useAlert()
  
  // State
  const transactions = ref([])
  const loading = ref(false)
  const backgroundLoading = ref(false)
  const totalCount = ref(0)
  const lastFetchTime = ref(null)
  const searchQuery = ref('')
  const searchResults = ref([])
  const searchTotal = ref(0)
  const selectedStatementId = ref(null)
  
  
  // Getters
  const hasTransactions = computed(() => transactions.value.length > 0)
  
  const transactionsByStatement = computed(() => {
    const grouped = {}
    transactions.value.forEach(transaction => {
      const statementId = transaction.statement_id
      if (!grouped[statementId]) {
        grouped[statementId] = []
      }
      grouped[statementId].push(transaction)
    })
    return grouped
  })
  
  const processedTransactions = computed(() => 
    transactions.value.filter(t => t.computed_content !== null)
  )
  
  const unprocessedTransactions = computed(() => 
    transactions.value.filter(t => t.computed_content === null)
  )
  
  const transactionsWithAmount = computed(() => 
    transactions.value.filter(t => 
      t.ingested_content?.amount && 
      !isNaN(parseFloat(t.ingested_content.amount))
    )
  )
  
  const totalAmount = computed(() => {
    return transactionsWithAmount.value.reduce((sum, transaction) => {
      const amount = parseFloat(transaction.ingested_content.amount) || 0
      return sum + amount
    }, 0)
  })
  
  const averageAmount = computed(() => {
    const validAmounts = transactionsWithAmount.value
    if (validAmounts.length === 0) return 0
    return totalAmount.value / validAmounts.length
  })
  
  const transactionsByDate = computed(() => {
    const grouped = {}
    transactions.value.forEach(transaction => {
      const date = transaction.ingested_content?.date
      if (date) {
        if (!grouped[date]) {
          grouped[date] = []
        }
        grouped[date].push(transaction)
      }
    })
    return grouped
  })
  
  const uniqueStatements = computed(() => {
    const statementIds = new Set(transactions.value.map(t => t.statement_id))
    return Array.from(statementIds)
  })
  
  // Actions
  async function fetchTransactions(statementId = null) {
    loading.value = true
    try {
      // Fetch ALL transactions by using pagination
      let allTransactions = []
      let skip = 0
      const limit = 100000 // API max limit
      let hasMore = true
      
      while (hasMore) {
        const response = await transactionsApi.getTransactions({ 
          skip, 
          limit,
          statement_id: statementId 
        })
        
        allTransactions.push(...response.transactions)
        
        // Check if we have more pages
        hasMore = response.transactions.length === limit && 
                  skip + limit < response.total
        
        skip += limit
        
        // Safety check
        if (skip > 1000000) {
          console.warn('Reached maximum batch limit while fetching transactions')
          break
        }
      }
      
      transactions.value = allTransactions
      totalCount.value = allTransactions.length
      selectedStatementId.value = statementId
      lastFetchTime.value = new Date()
      
      return { transactions: allTransactions, total: allTransactions.length }
    } catch (err) {
      error('Failed to fetch transactions', { persistent: true })
      throw err
    } finally {
      loading.value = false
    }
  }
  
  async function fetchAllTransactions() {
    backgroundLoading.value = true
    try {
      let allTransactions = []
      let skip = 0
      const limit = 100000 // API max limit
      let hasMore = true
      
      // Fetch all transactions in batches
      while (hasMore) {
        const response = await transactionsApi.getTransactions({ 
          skip, 
          limit 
        })
        
        allTransactions.push(...response.transactions)
        
        // Check if we have more pages
        hasMore = response.transactions.length === limit && 
                  skip + limit < response.total
        
        skip += limit
        
        // Safety check to prevent infinite loops
        if (skip > 1000000) { // Max 1,000,000 transactions
          console.warn('Reached maximum batch limit while fetching all transactions')
          break
        }
      }
      
      transactions.value = allTransactions
      totalCount.value = allTransactions.length
      lastFetchTime.value = new Date()
      
      console.log(`Fetched ${allTransactions.length} transactions in background`)
      
      return allTransactions
    } catch (err) {
      console.error('Failed to fetch all transactions in background:', err)
      error('Background fetch failed - transactions may be outdated')
      throw err
    } finally {
      backgroundLoading.value = false
    }
  }
  
  async function fetchTransaction(transactionId) {
    try {
      const response = await transactionsApi.getTransaction(transactionId)
      
      // Update or add transaction in store
      const index = transactions.value.findIndex(t => t.id === transactionId)
      if (index !== -1) {
        transactions.value[index] = response
      } else {
        transactions.value.push(response)
      }
      
      return response
    } catch (err) {
      error('Failed to fetch transaction')
      throw err
    }
  }
  
  async function deleteTransaction(transactionId) {
    try {
      await transactionsApi.deleteTransaction(transactionId)
      
      // Remove from store
      const index = transactions.value.findIndex(t => t.id === transactionId)
      if (index !== -1) {
        transactions.value.splice(index, 1)
        totalCount.value -= 1
      }
      
      success('Transaction deleted successfully')
    } catch (err) {
      error('Failed to delete transaction')
      throw err
    }
  }
  
  async function searchTransactions(query) {
    if (!query.trim()) {
      searchResults.value = []
      searchTotal.value = 0
      searchQuery.value = ''
      return { transactions: [], total: 0 }
    }
    
    try {
      // Search ALL transactions with large limit
      const response = await transactionsApi.searchTransactions(query, { skip: 0, limit: 100000 })
      
      searchResults.value = response.transactions
      searchTotal.value = response.total
      searchQuery.value = query
      
      return response
    } catch (err) {
      error('Failed to search transactions')
      throw err
    }
  }
  
  async function getStatementTransactions(statementId) {
    try {
      // Get ALL transactions for a statement with large limit
      const response = await transactionsApi.getStatementTransactions(statementId, { skip: 0, limit: 100000 })
      return response
    } catch (err) {
      error('Failed to fetch statement transactions')
      throw err
    }
  }
  
  function clearSearch() {
    searchResults.value = []
    searchTotal.value = 0
    searchQuery.value = ''
  }
  
  function clearTransactions() {
    transactions.value = []
    totalCount.value = 0
    lastFetchTime.value = null
    clearSearch()
  }
  
  function refreshTransactions() {
    return fetchTransactions(selectedStatementId.value)
  }

  // Filtered transactions methods
  async function fetchFilteredTransactions({ columns, skip = 0, limit = 100 } = {}) {
    loading.value = true
    try {
      const response = await transactionsApi.getFilteredTransactions({ 
        columns, 
        skip, 
        limit 
      })
      
      // For filtered transactions, we don't store them in the main transactions array
      // They are returned directly for display purposes
      return response
    } catch (err) {
      error('Failed to fetch filtered transactions', { persistent: true })
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchFilteredTransactionsWithPagination({ 
    columns, 
    skip = 0, 
    limit = 100 
  } = {}) {
    backgroundLoading.value = true
    try {
      const response = await transactionsApi.getFilteredTransactions({ 
        columns, 
        skip, 
        limit 
      })
      
      return response
    } catch (err) {
      error('Failed to fetch filtered transactions', { persistent: true })
      throw err
    } finally {
      backgroundLoading.value = false
    }
  }

  // Metadata methods
  async function fetchTransactionMetadata() {
    try {
      const response = await transactionsApi.getTransactionMetadata()
      return response
    } catch (err) {
      error('Failed to fetch transaction metadata', { persistent: true })
      throw err
    }
  }
  
  
  return {
    // State
    transactions,
    loading,
    backgroundLoading,
    totalCount,
    lastFetchTime,
    searchQuery,
    searchResults,
    searchTotal,
    selectedStatementId,
    
    // Getters
    hasTransactions,
    transactionsByStatement,
    processedTransactions,
    unprocessedTransactions,
    transactionsWithAmount,
    totalAmount,
    averageAmount,
    transactionsByDate,
    uniqueStatements,
    
    // Actions
    fetchTransactions,
    fetchAllTransactions,
    fetchTransaction,
    deleteTransaction,
    searchTransactions,
    getStatementTransactions,
    clearSearch,
    clearTransactions,
    refreshTransactions,
    fetchFilteredTransactions,
    fetchFilteredTransactionsWithPagination,
    fetchTransactionMetadata
  }
})
