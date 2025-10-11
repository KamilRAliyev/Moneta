<template>
  <div class="h-full flex flex-col">
    <!-- Widget Header -->
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-lg font-semibold text-foreground">{{ config.label || 'Filter' }}</h3>
      <div class="flex items-center space-x-2">
        <Button
          v-if="isEditMode"
          @click="toggleConfig"
          variant="ghost"
          size="sm"
          :title="showConfig ? 'Hide config' : 'Show config'"
        >
          <Settings class="w-4 h-4" />
        </Button>
        <Button
          v-if="isEditMode"
          @click="$emit('remove')"
          variant="ghost"
          size="sm"
          class="text-destructive hover:text-destructive"
          title="Remove widget"
        >
          <X class="w-4 h-4" />
        </Button>
      </div>
    </div>

    <!-- Configuration Panel -->
    <Card v-if="showConfig && isEditMode" class="mb-4">
      <CardContent class="p-4">
        <div class="space-y-4">
          <div>
            <Label class="block text-sm font-medium mb-1">Label</Label>
            <Input
              v-model="localConfig.label"
              type="text"
            />
          </div>
          
          <div>
            <Label class="block text-sm font-medium mb-1">Options (one per line)</Label>
            <Textarea
              v-model="optionsText"
              rows="4"
              placeholder="Option 1&#10;Option 2&#10;Option 3"
            />
          </div>
          
          <div>
            <Label class="block text-sm font-medium mb-1">Filter Type</Label>
            <Select v-model="localConfig.filter_type">
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="month">Month</SelectItem>
                <SelectItem value="category">Category</SelectItem>
                <SelectItem value="account">Account</SelectItem>
                <SelectItem value="statement">Statement</SelectItem>
                <SelectItem value="custom">Custom</SelectItem>
              </SelectContent>
            </Select>
          </div>
          
          <div v-if="localConfig.filter_type === 'custom'">
            <Label class="block text-sm font-medium mb-1">Field Name</Label>
            <Input
              v-model="localConfig.field_name"
              type="text"
              placeholder="e.g., account_type"
            />
          </div>
          
          <div class="flex items-center space-x-2">
            <Button @click="saveConfig">
              Save
            </Button>
            <Button @click="cancelConfig" variant="outline">
              Cancel
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>

    <!-- Dropdown Content -->
    <div class="flex-1 flex flex-col justify-center">
      <div class="space-y-4">
        <div>
          <Label class="block text-sm font-medium mb-2">
            {{ config.label || 'Select Filter' }}
          </Label>
          <Select v-model="selectedValue" @update:modelValue="onValueChange">
            <SelectTrigger>
              <SelectValue placeholder="All" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="">All</SelectItem>
              <SelectItem 
                v-for="option in config.options" 
                :key="option" 
                :value="option"
              >
                {{ option }}
              </SelectItem>
            </SelectContent>
          </Select>
        </div>
        
        <div v-if="selectedValue" class="text-sm text-muted-foreground">
          <span class="font-medium">Selected:</span> {{ selectedValue }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { Settings, X } from 'lucide-vue-next'
import { reportsApi } from '@/api/reports'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'

// Props
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

// Emits
const emit = defineEmits(['config-updated', 'remove', 'value-changed'])

// Reactive data
const showConfig = ref(false)
const selectedValue = ref('')
const localConfig = reactive({ ...props.config })

// Computed properties
const optionsText = computed({
  get: () => localConfig.options ? localConfig.options.join('\n') : '',
  set: (value) => {
    localConfig.options = value.split('\n').filter(option => option.trim() !== '')
  }
})

// Methods
const toggleConfig = () => {
  showConfig.value = !showConfig.value
}

const saveConfig = () => {
  // Ensure we have default values
  if (!localConfig.filter_type) {
    localConfig.filter_type = 'month'
  }
  if (!localConfig.field_name && localConfig.filter_type === 'custom') {
    localConfig.field_name = 'custom_field'
  }
  
  emit('config-updated', { ...localConfig })
  showConfig.value = false
}

const cancelConfig = () => {
  // Reset to original config
  Object.assign(localConfig, props.config)
  showConfig.value = false
}

const onValueChange = () => {
  emit('value-changed', selectedValue.value)
}

// Methods
const loadOptionsFromData = async () => {
  try {
    const response = await reportsApi.getReportData('dummy') // We'll get metadata from any report
    const metadata = response.data.metadata
    
    if (localConfig.filter_type === 'category' && metadata.categories) {
      localConfig.options = metadata.categories
    } else if (localConfig.filter_type === 'account' && metadata.accounts) {
      localConfig.options = metadata.accounts
    } else if (localConfig.filter_type === 'month') {
      // Generate month options based on date range
      const dateRange = metadata.date_range
      if (dateRange && dateRange.start && dateRange.end) {
        localConfig.options = generateMonthOptions(dateRange.start, dateRange.end)
      }
    }
  } catch (error) {
    console.error('Failed to load options from data:', error)
  }
}

const generateMonthOptions = (startDate, endDate) => {
  const options = []
  const start = new Date(startDate)
  const end = new Date(endDate)
  
  const current = new Date(start.getFullYear(), start.getMonth(), 1)
  while (current <= end) {
    options.push(current.toLocaleDateString('en-US', { year: 'numeric', month: 'long' }))
    current.setMonth(current.getMonth() + 1)
  }
  
  return options
}

// Initialize with default config if needed
if (!localConfig.options) {
  localConfig.options = ['Option 1', 'Option 2', 'Option 3']
}
if (!localConfig.filter_type) {
  localConfig.filter_type = 'month'
}

// Watchers
watch(() => props.config, (newConfig) => {
  Object.assign(localConfig, newConfig)
}, { deep: true })

watch(() => localConfig.filter_type, () => {
  loadOptionsFromData()
})

// Lifecycle
onMounted(() => {
  loadOptionsFromData()
})
</script>
