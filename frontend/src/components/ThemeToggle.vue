<script setup>
import { onMounted } from 'vue'
import { Button } from '@/components/ui/button'
import { Sun, Moon } from 'lucide-vue-next'
import { useSettingsStore } from '@/stores/settings.js'

const settingsStore = useSettingsStore()

onMounted(() => {
  settingsStore.loadSettings()
})

defineProps({
  isCollapsed: {
    type: Boolean,
    default: false
  }
})
</script>

<template>
  <Button @click="settingsStore.toggleTheme" variant="ghost" :class="[
    'w-full justify-start',
    isCollapsed ? 'px-2' : 'px-3'
  ]">
    <Sun v-if="settingsStore.isDark" class="h-4 w-4" />
    <Moon v-else class="h-4 w-4" />
    <span v-if="!isCollapsed" class="ml-3">Theme</span>
  </Button>
</template>
