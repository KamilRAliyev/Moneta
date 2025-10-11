<template>
  <div 
    ref="toolbarRef"
    :style="toolbarStyle"
    class="fixed bg-card border rounded-lg shadow-lg p-4 z-50 min-w-[300px]"
    @mousedown="startDrag"
  >
    <!-- Drag Handle -->
    <div class="flex items-center justify-between mb-3 cursor-move border-b pb-2">
      <div class="flex items-center space-x-2">
        <GripVertical class="w-4 h-4 text-muted-foreground" />
        <span class="text-sm font-medium">Report Controls</span>
      </div>
      <Button @click="toggleCollapsed" variant="ghost" size="sm" class="h-6 w-6 p-0">
        <component :is="isCollapsed ? ChevronDown : ChevronUp" class="w-4 h-4" />
      </Button>
    </div>

    <!-- Toolbar Content -->
    <div v-if="!isCollapsed" class="space-y-3">
      <!-- Report Name -->
      <div v-if="reportName">
        <Label class="text-xs text-muted-foreground">Report</Label>
        <div class="text-sm font-medium">{{ reportName }}</div>
      </div>

      <!-- Mode Toggle -->
      <Button
        @click="$emit('toggle-mode')"
        :variant="isEditMode ? 'default' : 'outline'"
        class="w-full"
        size="sm"
      >
        <component :is="isEditMode ? Edit : Lock" class="w-4 h-4 mr-2" />
        {{ isEditMode ? 'Edit Mode' : 'Lock Mode' }}
      </Button>

      <!-- Widget Actions (Edit Mode) -->
      <div v-if="isEditMode" class="space-y-2">
        <Label class="text-xs text-muted-foreground">Add Widget</Label>
        <div class="grid grid-cols-3 gap-2">
          <Button @click="$emit('add-widget', 'chart')" variant="outline" size="sm">
            <BarChart3 class="w-4 h-4 mr-1" />
            Chart
          </Button>
          <Button @click="$emit('add-widget', 'stats')" variant="outline" size="sm">
            <Activity class="w-4 h-4 mr-1" />
            Stats
          </Button>
          <Button @click="$emit('add-widget', 'heading')" variant="outline" size="sm">
            <Heading class="w-4 h-4 mr-1" />
            Heading
          </Button>
          <Button @click="$emit('add-widget', 'divider')" variant="outline" size="sm">
            <Minus class="w-4 h-4 mr-1" />
            Divider
          </Button>
          <Button @click="$emit('add-widget', 'table')" variant="outline" size="sm">
            <Table2 class="w-4 h-4 mr-1" />
            Table
          </Button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { GripVertical, ChevronDown, ChevronUp, Lock, Edit, BarChart3, Activity, Table2, Heading, Minus } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'

const props = defineProps({
  isEditMode: {
    type: Boolean,
    default: false
  },
  reportName: {
    type: String,
    default: ''
  },
  widgetCount: {
    type: Number,
    default: 0
  },
  memory: {
    type: String,
    default: '0'
  }
})

defineEmits(['toggle-mode', 'add-widget'])

const toolbarRef = ref(null)
const isCollapsed = ref(false)
const isDragging = ref(false)
const position = ref({ x: 20, y: 100 }) // Default position
const dragOffset = ref({ x: 0, y: 0 })

const toolbarStyle = computed(() => ({
  left: `${position.value.x}px`,
  top: `${position.value.y}px`,
  cursor: isDragging.value ? 'grabbing' : 'grab'
}))

const startDrag = (e) => {
  // Only drag if clicking on the header area
  if (!e.target.closest('.cursor-move')) return
  
  isDragging.value = true
  dragOffset.value = {
    x: e.clientX - position.value.x,
    y: e.clientY - position.value.y
  }
  
  document.addEventListener('mousemove', onDrag)
  document.addEventListener('mouseup', stopDrag)
}

const onDrag = (e) => {
  if (!isDragging.value) return
  
  position.value = {
    x: e.clientX - dragOffset.value.x,
    y: e.clientY - dragOffset.value.y
  }
  
  savePosition()
}

const stopDrag = () => {
  isDragging.value = false
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', stopDrag)
}

const toggleCollapsed = () => {
  isCollapsed.value = !isCollapsed.value
  savePosition()
}

const savePosition = () => {
  try {
    localStorage.setItem('moneta_toolbar_position', JSON.stringify({
      x: position.value.x,
      y: position.value.y,
      collapsed: isCollapsed.value
    }))
  } catch (err) {
    console.warn('Failed to save toolbar position:', err)
  }
}

const loadPosition = () => {
  try {
    const saved = localStorage.getItem('moneta_toolbar_position')
    if (saved) {
      const data = JSON.parse(saved)
      position.value = { x: data.x, y: data.y }
      isCollapsed.value = data.collapsed || false
    }
  } catch (err) {
    console.warn('Failed to load toolbar position:', err)
  }
}

onMounted(() => {
  loadPosition()
})

onUnmounted(() => {
  stopDrag()
})
</script>

