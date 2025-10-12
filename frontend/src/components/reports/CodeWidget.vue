<template>
  <div 
    class="h-full flex flex-col p-4"
    :class="{ 'cursor-pointer hover:bg-accent/5 transition-colors rounded-lg': isEditMode }"
    @click="isEditMode ? $emit('configure') : undefined"
  >
    <!-- Widget Header -->
    <div v-if="isEditMode" class="flex items-center justify-between mb-2 flex-shrink-0" @click.stop>
      <select 
        v-model="localConfig.language"
        @change="emitUpdate"
        class="h-7 rounded-md border border-input bg-background px-2 text-xs"
      >
        <option value="javascript">JavaScript</option>
        <option value="python">Python</option>
        <option value="json">JSON</option>
        <option value="sql">SQL</option>
        <option value="html">HTML</option>
        <option value="css">CSS</option>
        <option value="bash">Bash</option>
        <option value="plaintext">Plain Text</option>
      </select>
      
      <div class="flex items-center space-x-1">
        <Button
          @click="copyCode"
          variant="ghost"
          size="sm"
          class="h-6 px-2 text-xs"
          title="Copy code"
        >
          <Copy class="w-3 h-3 mr-1" />
          {{ copied ? 'Copied!' : 'Copy' }}
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

    <!-- Code Editor/Display -->
    <div class="flex-1 flex flex-col overflow-hidden" @click.stop>
      <textarea 
        v-if="isEditMode"
        v-model="localConfig.code"
        @input="emitUpdate"
        placeholder="Enter code..."
        class="flex-1 font-mono text-xs bg-gray-900 text-gray-100 rounded-md p-3 border border-gray-700 focus:outline-none focus:ring-2 focus:ring-ring resize-none overflow-auto"
        spellcheck="false"
      ></textarea>
      
      <pre v-else class="flex-1 font-mono text-xs bg-gray-900 text-gray-100 rounded-md p-3 border border-gray-700 overflow-auto"><code>{{ localConfig.code || '// No code yet' }}</code></pre>
      
      <div class="mt-2 text-xs text-muted-foreground">
        Language: {{ localConfig.language }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, watch } from 'vue'
import { X, Copy } from 'lucide-vue-next'
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
  code: props.config.code || '',
  language: props.config.language || 'javascript'
})

const copied = ref(false)

const copyCode = () => {
  navigator.clipboard.writeText(localConfig.code)
  copied.value = true
  setTimeout(() => {
    copied.value = false
  }, 2000)
}

const emitUpdate = () => {
  emit('config-updated', { ...localConfig })
}

watch(() => props.config, (newConfig) => {
  Object.assign(localConfig, newConfig)
}, { deep: true })
</script>

