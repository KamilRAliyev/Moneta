<script setup>
import { onMounted } from 'vue'
import Sidebar from '@/components/Sidebar.vue'
import AlertContainer from '@/components/AlertContainer.vue'
import { TooltipProvider } from '@/components/ui/tooltip'
import { useTransactionsStore } from '@/stores/transactions.js'
import { useAlert } from '@/composables/useAlert.js'

// Initialize stores and composables
const transactionsStore = useTransactionsStore()
const { info, success, error } = useAlert()

onMounted(async () => {
  // Initialize transactions once on app mount
  console.log('App mounted - initializing transactions')
  info('Loading transactions...', { persistent: false })
  
  try {
    await transactionsStore.initializeTransactions()
    success(`Loaded ${transactionsStore.totalCount} transactions`)
  } catch (err) {
    error('Failed to load transactions')
    console.error('Transaction fetch error:', err)
  }
})
</script>

<template>
<TooltipProvider>
  <Sidebar>
    <div class="h-full overflow-auto">
      <router-view />
    </div>
  </Sidebar>
  <AlertContainer />
</TooltipProvider>
</template>

<style scoped>
</style>
