<template>
  <div 
    class="h-full flex flex-col p-4"
    :class="{ 'cursor-pointer hover:bg-accent/5 transition-colors rounded-lg': isEditMode }"
    @click="isEditMode ? $emit('configure') : undefined"
  >
    <!-- Widget Header -->
    <div v-if="isEditMode" class="flex items-center justify-between mb-2 flex-shrink-0" @click.stop>
      <select 
        v-model="localConfig.listType"
        @change="emitUpdate"
        class="h-7 rounded-md border border-input bg-background px-2 text-xs"
      >
        <option value="bullet">Bullet List</option>
        <option value="numbered">Numbered List</option>
      </select>
      
      <div class="flex items-center space-x-1">
        <Button
          @click="addItem"
          variant="ghost"
          size="sm"
          class="h-6 w-6 p-0"
          title="Add item"
        >
          <Plus class="w-4 h-4" />
        </Button>
        <Button
          @click="$emit('remove')"
          variant="ghost"
          size="sm"
          class="text-destructive hover:text-destructive h-6 w-6 p-0"
          title="Remove widget"
        >
          <X class="w-4 h-4" />
        </Button>
      </div>
    </div>

    <!-- List Items -->
    <div class="flex-1 overflow-auto">
      <component :is="localConfig.listType === 'numbered' ? 'ol' : 'ul'" :class="listClass">
        <li 
          v-for="(item, index) in localConfig.items" 
          :key="index"
          class="mb-2 flex items-start group"
        >
          <input 
            v-if="isEditMode"
            v-model="localConfig.items[index]"
            @input="emitUpdate"
            placeholder="List item..."
            class="flex-1 bg-transparent border-b border-transparent hover:border-input focus:border-input focus:outline-none text-sm py-1"
          />
          <span v-else class="flex-1 text-sm">{{ item }}</span>
          
          <Button
            v-if="isEditMode"
            @click="removeItem(index)"
            variant="ghost"
            size="sm"
            class="h-6 w-6 p-0 opacity-0 group-hover:opacity-100 transition-opacity ml-2"
          >
            <X class="w-3 h-3" />
          </Button>
        </li>
        <li v-if="localConfig.items.length === 0" class="text-sm text-muted-foreground italic">
          No items yet. Click + to add items.
        </li>
      </component>
    </div>
  </div>
</template>

<script setup>
import { reactive, computed, watch } from 'vue'
import { X, Plus } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'

const props = defineProps({
  config: {
    type: Object,
    default: () => ({})
  },
  isEditMode: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['config-updated', 'remove'])

const localConfig = reactive({
  listType: props.config.listType || 'bullet',
  items: props.config.items || ['Item 1', 'Item 2', 'Item 3']
})

const listClass = computed(() => {
  return localConfig.listType === 'numbered' 
    ? 'list-decimal list-inside' 
    : 'list-disc list-inside'
})

const addItem = () => {
  localConfig.items.push('')
  emitUpdate()
}

const removeItem = (index) => {
  localConfig.items.splice(index, 1)
  emitUpdate()
}

const emitUpdate = () => {
  emit('config-updated', { ...localConfig, items: [...localConfig.items] })
}

watch(() => props.config, (newConfig) => {
  Object.assign(localConfig, newConfig)
}, { deep: true })
</script>

