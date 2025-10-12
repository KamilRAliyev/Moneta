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
        title="Edit quote"
      >
        <Edit class="w-4 h-4" />
      </Button>
      <Button
        @click="$emit('remove')"
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
        v-model="localConfig.quote"
        @input="emitUpdate"
        placeholder="Enter quote text..."
        class="flex-1 min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 resize-none"
      ></textarea>
      
      <input
        v-model="localConfig.author"
        @input="emitUpdate"
        placeholder="Author (optional)"
        class="w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
      />
      
      <Button @click="toggleEdit" size="sm" variant="outline" class="h-7 text-xs self-end">
        Done
      </Button>
    </div>

    <!-- Display Mode -->
    <blockquote 
      v-else 
      class="flex-1 border-l-4 border-primary pl-4 italic"
    >
      <p class="text-base mb-2">{{ localConfig.quote || 'Click to edit quote...' }}</p>
      <footer v-if="localConfig.author" class="text-sm text-muted-foreground not-italic">
        — {{ localConfig.author }}
      </footer>
    </blockquote>
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
  quote: props.config.quote || '',
  author: props.config.author || ''
})

const editing = ref(false)

const toggleEdit = () => {
  editing.value = !editing.value
}

const emitUpdate = () => {
  emit('config-updated', { ...localConfig })
}

watch(() => props.config, (newConfig) => {
  Object.assign(localConfig, newConfig)
}, { deep: true })
</script>

