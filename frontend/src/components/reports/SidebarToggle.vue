<template>
  <button
    @click="$emit('toggle')"
    :class="[
      'fixed top-1/2 -translate-y-1/2 z-40',
      'bg-card border border-border rounded-l-lg shadow-lg',
      'p-2 transition-all duration-300 hover:bg-accent',
      'flex items-center justify-center',
      isOpen ? 'right-[400px]' : 'right-0'
    ]"
    :title="isOpen ? 'Close sidebar' : 'Open sidebar'"
  >
    <component
      :is="isOpen ? ChevronRight : ChevronLeft"
      :class="['w-5 h-5 text-foreground transition-transform duration-300']"
    />
  </button>
</template>

<script setup>
import { ChevronLeft, ChevronRight } from 'lucide-vue-next'

defineProps({
  isOpen: {
    type: Boolean,
    default: false
  }
})

defineEmits(['toggle'])
</script>
