<template>
  <div class="h-full flex flex-col justify-center py-1">
    <!-- Edit Mode Controls -->
    <div v-if="isEditMode" class="flex items-center justify-between mb-1">
      <div class="flex items-center space-x-2">
        <Label class="text-sm">Thickness:</Label>
        <Select v-model="localConfig.thickness" @update:modelValue="saveConfig">
          <SelectTrigger class="w-24 h-8">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="thin">Thin</SelectItem>
            <SelectItem value="medium">Medium</SelectItem>
            <SelectItem value="thick">Thick</SelectItem>
          </SelectContent>
        </Select>
      </div>
      <Button
        @click="$emit('remove')"
        variant="ghost"
        size="sm"
        class="text-destructive hover:text-destructive"
        title="Remove widget"
      >
        <X class="w-4 h-4" />
      </Button>
    </div>

    <!-- Divider Line -->
    <div 
      :class="[
        'w-full rounded-full bg-border',
        thicknessClass
      ]"
    ></div>
  </div>
</template>

<script setup>
import { reactive, computed } from 'vue'
import { X } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

const props = defineProps({
  config: {
    type: Object,
    required: true
  },
  isEditMode: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['config-updated', 'remove'])

const localConfig = reactive({ 
  thickness: props.config.thickness || 'thin'
})

const thicknessClass = computed(() => {
  switch (localConfig.thickness) {
    case 'thin':
      return 'h-px'
    case 'medium':
      return 'h-0.5'
    case 'thick':
      return 'h-1'
    default:
      return 'h-px'
  }
})

const saveConfig = () => {
  emit('config-updated', { ...localConfig })
}
</script>

