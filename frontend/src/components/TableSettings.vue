<script setup>
import { computed } from 'vue'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import { useSettingsStore } from '@/stores/settings.js'
import { Settings, RotateCcw } from 'lucide-vue-next'

const settingsStore = useSettingsStore()

const pageSizeOptions = [
  { value: 25, label: '25 per page' },
  { value: 50, label: '50 per page' },
  { value: 100, label: '100 per page' },
  { value: 200, label: '200 per page' },
  { value: 500, label: '500 per page' },
  { value: 1000, label: '1000 per page' }
]

const currentPageSize = computed(() => settingsStore.tablePagination.pageSize)

const handlePageSizeChange = (value) => {
  const pageSize = parseInt(value)
  settingsStore.setPageSize(pageSize)
}

const resetSettings = () => {
  settingsStore.setPageSize(50)
  settingsStore.setCurrentPage(1)
}
</script>

<template>
  <Card class="mb-6">
    <CardHeader class="pb-4">
      <div class="flex items-center justify-between">
        <div>
          <CardTitle class="text-lg flex items-center gap-2">
            <Settings class="h-5 w-5" />
            Table Settings
          </CardTitle>
          <CardDescription>
            Configure how transactions are displayed
          </CardDescription>
        </div>
        <Button
          variant="outline"
          size="sm"
          @click="resetSettings"
        >
          <RotateCcw class="h-4 w-4 mr-2" />
          Reset
        </Button>
      </div>
    </CardHeader>
    <CardContent>
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <!-- Additional settings can be added here -->
        <div class="space-y-2">
          <Label>Display Options</Label>
          <div class="text-sm text-muted-foreground">
            More settings coming soon...
          </div>
        </div>
        
        <div class="space-y-2">
          <Label>Performance</Label>
          <div class="text-sm text-muted-foreground">
            {{ currentPageSize >= 500 ? 'Large dataset mode' : 'Standard mode' }}
          </div>
        </div>
        
        <div class="space-y-2">
          <Label>Current Settings</Label>
          <div class="text-sm text-muted-foreground">
            {{ currentPageSize }} items per page
          </div>
        </div>
      </div>
    </CardContent>
  </Card>
</template>
