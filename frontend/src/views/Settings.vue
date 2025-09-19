<script setup>
import { ref, onMounted } from 'vue'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { healthService } from '@/api/health.js'
import { useSettingsStore } from '@/stores/settings.js'
import { useAlert } from '@/composables/useAlert.js'

const settingsStore = useSettingsStore()
const { success, error, info } = useAlert()
const testResult = ref(null)
const isTesting = ref(false)

const testConnection = async () => {
  isTesting.value = true
  testResult.value = null
  
  try {
    const result = await healthService.checkHealth(settingsStore.backendUrl)
    testResult.value = {
      success: result.status === 'connected',
      data: result.data,
      error: result.error,
      timestamp: result.timestamp
    }
  } catch (error) {
    testResult.value = {
      success: false,
      error: error.message,
      timestamp: new Date().toISOString()
    }
  } finally {
    isTesting.value = false
  }
}

const saveSettings = () => {
  settingsStore.saveSettings()
  success('Settings saved successfully!')
}

onMounted(() => {
  // Settings are already loaded by the store
})
</script>

<template>
  <div class="p-8 max-w-4xl mx-auto">
    <h1 class="text-3xl font-bold mb-8">Settings</h1>
    
    <div class="space-y-6">
      <!-- Backend Configuration -->
      <Card>
        <CardHeader>
          <CardTitle>Backend Configuration</CardTitle>
          <CardDescription>
            Configure your backend server connection settings
          </CardDescription>
        </CardHeader>
        <CardContent class="space-y-4">
          <div class="space-y-2">
            <Label for="backend-url">Backend URL</Label>
            <Input 
              id="backend-url"
              v-model="settingsStore.backendUrl"
              placeholder="http://localhost:9999"
              type="url"
            />
          </div>
          
          <div class="flex gap-2">
            <Button @click="testConnection" :disabled="isTesting">
              {{ isTesting ? 'Testing...' : 'Test Connection' }}
            </Button>
            <Button @click="saveSettings" variant="outline">
              Save Settings
            </Button>
          </div>
        </CardContent>
      </Card>

      <!-- Processing Settings -->
      <Card>
        <CardHeader>
          <CardTitle>Processing Settings</CardTitle>
          <CardDescription>
            Configure how statements are processed after upload
          </CardDescription>
        </CardHeader>
        <CardContent class="space-y-4">
          <div class="flex items-center space-x-2">
            <input
              id="auto-process"
              v-model="settingsStore.autoProcess"
              @change="settingsStore.setAutoProcess(settingsStore.autoProcess)"
              type="checkbox"
              class="h-4 w-4 text-primary focus:ring-primary border-gray-300 rounded"
            />
            <Label for="auto-process" class="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
              Auto-process statements after upload
            </Label>
          </div>
          <p class="text-sm text-muted-foreground">
            When enabled, statements will be automatically processed to extract transactions immediately after upload.
          </p>
        </CardContent>
      </Card>

      <!-- Test Results -->
      <Card v-if="testResult">
        <CardHeader>
          <CardTitle>Connection Test Results</CardTitle>
        </CardHeader>
        <CardContent>
          <Alert :class="testResult.success ? 'border-green-500' : 'border-red-500'">
            <AlertDescription>
              <div class="space-y-2">
                <div class="font-semibold">
                  Status: {{ testResult.success ? '✅ Connected' : '❌ Failed' }}
                </div>
                <div class="text-sm text-muted-foreground">
                  Tested at: {{ new Date(testResult.timestamp).toLocaleString() }}
                </div>
                
                <div v-if="testResult.data" class="mt-4">
                  <h4 class="font-medium mb-2">Backend Health Data:</h4>
                  <div class="bg-muted p-3 rounded text-sm font-mono">
                    <div>Status: {{ testResult.data.status }}</div>
                    <div>Server Time: {{ testResult.data.server_time }}</div>
                    <div>Python Version: {{ testResult.data.python_version }}</div>
                    <div>System: {{ testResult.data.system }}</div>
                    <div>Hostname: {{ testResult.data.hostname }}</div>
                    <div>Process ID: {{ testResult.data.process_id }}</div>
                    <div>App Version: {{ testResult.data.app_version }}</div>
                  </div>
                </div>
                
                <div v-if="testResult.error" class="mt-4">
                  <h4 class="font-medium mb-2 text-red-600">Error:</h4>
                  <div class="bg-red-50 p-3 rounded text-sm text-red-800">
                    {{ testResult.error }}
                  </div>
                </div>
              </div>
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    </div>
  </div>
</template>
