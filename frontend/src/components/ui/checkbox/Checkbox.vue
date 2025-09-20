<template>
  <button
    ref="buttonRef"
    type="button"
    role="checkbox"
    :aria-checked="checked"
    :aria-required="required"
    :data-state="checked ? 'checked' : 'unchecked'"
    :data-disabled="disabled ? '' : undefined"
    :disabled="disabled"
    :class="cn(
      'peer h-4 w-4 shrink-0 rounded-sm border border-primary ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 data-[state=checked]:bg-primary data-[state=checked]:text-primary-foreground',
      className
    )"
    @click="toggle"
  >
    <svg
      v-if="checked"
      class="h-4 w-4"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      stroke-width="2"
      stroke-linecap="round"
      stroke-linejoin="round"
    >
      <polyline points="20,6 9,17 4,12" />
    </svg>
    <span v-if="indeterminate" class="h-4 w-4 flex items-center justify-center">
      <svg
        class="h-3 w-3"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
      >
        <line x1="5" y1="12" x2="19" y2="12" />
      </svg>
    </span>
  </button>
</template>

<script setup>
import { ref, computed } from 'vue'
import { cn } from '@/lib/utils'

const props = defineProps({
  checked: {
    type: [Boolean, String],
    default: false
  },
  disabled: {
    type: Boolean,
    default: false
  },
  required: {
    type: Boolean,
    default: false
  },
  indeterminate: {
    type: Boolean,
    default: false
  },
  className: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['update:checked', 'change'])

const buttonRef = ref()

const isChecked = computed(() => {
  if (props.indeterminate) return 'indeterminate'
  return props.checked === true || props.checked === 'true'
})

const toggle = () => {
  if (props.disabled) return
  
  const newValue = !props.checked
  emit('update:checked', newValue)
  emit('change', newValue)
}
</script>

