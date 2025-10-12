<template>
  <div class="h-full flex flex-col py-1">
    <!-- Edit Mode Controls -->
    <div v-if="isEditMode" class="flex items-center justify-between mb-1 flex-shrink-0">
      <div class="flex items-center space-x-2">
        <Label class="text-sm">Heading Level:</Label>
        <Select v-model="localConfig.level" @update:modelValue="saveConfig">
          <SelectTrigger class="w-24 h-8">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="h1">H1</SelectItem>
            <SelectItem value="h2">H2</SelectItem>
            <SelectItem value="h3">H3</SelectItem>
          </SelectContent>
        </Select>
      </div>
      <Button
        @click.stop="$emit('remove')"
        variant="ghost"
        size="sm"
        class="text-destructive hover:text-destructive"
        title="Remove widget"
      >
        <X class="w-4 h-4" />
      </Button>
    </div>

    <!-- Heading Content -->
    <div class="flex-1 flex items-center">
      <component
        :is="localConfig.level || 'h2'"
        v-if="!isEditMode"
        :class="headingClass"
        class="text-foreground"
      >
        {{ localConfig.text || 'Heading' }}
      </component>
      <div
        v-else
        ref="editableDiv"
        :contenteditable="isEditMode"
        @blur="onBlur"
        @keydown.enter.prevent="onEnter"
        :class="headingClass"
        class="text-foreground outline-none focus:ring-2 focus:ring-primary rounded px-2 -mx-2"
      >
        {{ localConfig.text || 'Heading' }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
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

const editableDiv = ref(null)
const localConfig = reactive({ 
  level: props.config.level || 'h2',
  text: props.config.text || 'Heading'
})

const headingClass = computed(() => {
  switch (localConfig.level) {
    case 'h1':
      return 'text-3xl font-bold'
    case 'h2':
      return 'text-2xl font-semibold'
    case 'h3':
      return 'text-xl font-medium'
    default:
      return 'text-2xl font-semibold'
  }
})

const onBlur = (event) => {
  localConfig.text = event.target.innerText.trim() || 'Heading'
  saveConfig()
}

const onEnter = () => {
  editableDiv.value?.blur()
}

const saveConfig = () => {
  emit('config-updated', { ...localConfig })
}

onMounted(() => {
  if (props.isEditMode && editableDiv.value) {
    nextTick(() => {
      // Set cursor at end of text
      const range = document.createRange()
      const sel = window.getSelection()
      range.selectNodeContents(editableDiv.value)
      range.collapse(false)
      sel.removeAllRanges()
      sel.addRange(range)
    })
  }
})
</script>

<style scoped>
[contenteditable]:focus {
  outline: none;
}

[contenteditable]:empty:before {
  content: 'Enter heading text...';
  color: hsl(var(--muted-foreground));
}
</style>

