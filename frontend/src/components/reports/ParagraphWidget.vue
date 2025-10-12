<template>
  <div 
    class="h-full flex flex-col p-4"
    :class="{ 'cursor-pointer hover:bg-accent/5 transition-colors rounded-lg': isEditMode }"
    @click="isEditMode ? $emit('configure') : undefined"
  >
    <!-- Widget Header -->
    <div v-if="isEditMode" class="flex items-center justify-end mb-2 flex-shrink-0" @click.stop>
      <Button
        @click="toggleEdit"
        variant="ghost"
        size="sm"
        class="h-6 w-6 p-0"
        title="Edit paragraph"
      >
        <Edit class="w-4 h-4" />
      </Button>
      <Button
        @click.stop="$emit('remove')"
        variant="ghost"
        size="sm"
        class="text-destructive hover:text-destructive h-6 w-6 p-0 ml-1"
        title="Remove widget"
      >
        <X class="w-4 h-4" />
      </Button>
    </div>

    <!-- Edit Mode -->
    <div v-if="editing" class="flex-1 flex flex-col space-y-2" @click.stop>
      <textarea
        v-model="localConfig.text"
        @input="emitUpdate"
        placeholder="Enter paragraph text..."
        class="flex-1 min-h-[100px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 resize-none"
      ></textarea>
      
      <div class="flex items-center justify-between">
        <div class="flex items-center space-x-2">
          <select 
            v-model="localConfig.fontSize"
            @change="emitUpdate"
            class="h-8 rounded-md border border-input bg-background px-2 text-xs"
          >
            <option value="sm">Small</option>
            <option value="base">Normal</option>
            <option value="lg">Large</option>
          </select>
          
          <select 
            v-model="localConfig.align"
            @change="emitUpdate"
            class="h-8 rounded-md border border-input bg-background px-2 text-xs"
          >
            <option value="left">Left</option>
            <option value="center">Center</option>
            <option value="right">Right</option>
          </select>
        </div>
        
        <Button @click="toggleEdit" size="sm" variant="outline" class="h-7 text-xs">
          Done
        </Button>
      </div>
    </div>

    <!-- Display Mode -->
    <div 
      v-else 
      :class="[
        'flex-1 whitespace-pre-wrap',
        getFontSizeClass(),
        getAlignClass()
      ]"
    >
      {{ localConfig.text || 'Click to edit paragraph...' }}
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, watch } from 'vue'
import { X, Edit } from 'lucide-vue-next'
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
  text: props.config.text || '',
  fontSize: props.config.fontSize || 'base',
  align: props.config.align || 'left'
})

const editing = ref(false)

const toggleEdit = () => {
  editing.value = !editing.value
}

const emitUpdate = () => {
  emit('config-updated', { ...localConfig })
}

const getFontSizeClass = () => {
  switch (localConfig.fontSize) {
    case 'sm': return 'text-sm'
    case 'lg': return 'text-lg'
    default: return 'text-base'
  }
}

const getAlignClass = () => {
  switch (localConfig.align) {
    case 'center': return 'text-center'
    case 'right': return 'text-right'
    default: return 'text-left'
  }
}

watch(() => props.config, (newConfig) => {
  Object.assign(localConfig, newConfig)
}, { deep: true })
</script>

