<script setup>
import Sidebar from '@/components/Sidebar.vue'
import AlertContainer from '@/components/AlertContainer.vue'
import { TooltipProvider } from '@/components/ui/tooltip'
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
