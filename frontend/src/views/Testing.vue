<script setup>
import { useAlert } from '@/composables/useAlert.js'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

const { 
  success, 
  error, 
  warning, 
  info, 
  confirm, 
  showAlert, 
  dismissAll 
} = useAlert()

// Test data
const customAlert = {
  type: 'info',
  title: '',
  message: '',
  duration: 5000,
  persistent: false
}

const testBasicAlerts = () => {
  success('This is a success alert!')
  error('This is an error alert!')
  warning('This is a warning alert!')
  info('This is an info alert!')
}

const testPersistentAlerts = () => {
  error('This error alert will stay until manually dismissed', { persistent: true })
  warning('This warning alert will also stay', { persistent: true })
}

const testCustomDuration = () => {
  info('This alert will disappear in 2 seconds', { duration: 2000 })
  success('This alert will disappear in 10 seconds', { duration: 10000 })
}

const testConfirmation = async () => {
  const confirmed = await confirm('Are you sure you want to proceed with this action?', {
    confirmLabel: 'Yes, proceed',
    cancelLabel: 'No, cancel'
  })
  
  if (confirmed) {
    success('Action confirmed!')
  } else {
    info('Action cancelled')
  }
}

const testCustomAlert = () => {
  showAlert({
    type: customAlert.type,
    title: customAlert.title || undefined,
    message: customAlert.message,
    duration: customAlert.duration,
    persistent: customAlert.persistent,
    actions: [
      {
        label: 'Action 1',
        variant: 'default',
        action: () => success('Action 1 clicked!')
      },
      {
        label: 'Action 2',
        variant: 'outline',
        action: () => warning('Action 2 clicked!')
      }
    ]
  })
}

const testMultipleAlerts = () => {
  for (let i = 1; i <= 5; i++) {
    setTimeout(() => {
      info(`Alert number ${i}`)
    }, i * 500)
  }
}

const testLongMessage = () => {
  showAlert({
    type: 'warning',
    title: 'Long Message Test',
    message: 'This is a very long message that should wrap properly and not overflow the container. It contains multiple sentences to test how the alert component handles longer content. The alert should expand vertically to accommodate the text while maintaining proper spacing and readability.',
    persistent: true
  })
}
</script>

<template>
  <div class="p-6">
    <div class="mb-6">
      <h1 class="text-2xl font-bold mb-2">Testing Panel</h1>
      <p class="text-sm text-muted-foreground">Test various components and features</p>
    </div>

    <!-- Alert Testing Section -->
    <Card class="mb-6">
      <CardHeader class="pb-4">
        <CardTitle class="text-lg">Alert System Testing</CardTitle>
        <CardDescription>Test different alert types and configurations</CardDescription>
      </CardHeader>
      <CardContent>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
          <Button @click="() => success('Success!')" variant="outline" size="sm" class="text-xs">
            Success
          </Button>
          <Button @click="() => error('Error!')" variant="outline" size="sm" class="text-xs">
            Error
          </Button>
          <Button @click="() => warning('Warning!')" variant="outline" size="sm" class="text-xs">
            Warning
          </Button>
          <Button @click="() => info('Info!')" variant="outline" size="sm" class="text-xs">
            Info
          </Button>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
          <Button @click="testBasicAlerts" size="sm" class="text-xs">
            All Basic Alerts
          </Button>
          <Button @click="testPersistentAlerts" size="sm" class="text-xs">
            Persistent Alerts
          </Button>
          <Button @click="testMultipleAlerts" size="sm" class="text-xs">
            Multiple Alerts
          </Button>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
          <Button @click="testConfirmation" variant="outline" size="sm" class="text-xs">
            Test Confirmation
          </Button>
          <Button @click="dismissAll" variant="destructive" size="sm" class="text-xs">
            Dismiss All
          </Button>
        </div>

        <!-- Quick Custom Alert -->
        <div class="mt-4 p-3 border rounded-md bg-muted/50">
          <div class="text-sm font-medium mb-2">Quick Custom Alert</div>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-2 mb-2">
            <Select v-model="customAlert.type">
              <SelectTrigger class="h-8 text-xs">
                <SelectValue placeholder="Type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="success">Success</SelectItem>
                <SelectItem value="error">Error</SelectItem>
                <SelectItem value="warning">Warning</SelectItem>
                <SelectItem value="info">Info</SelectItem>
              </SelectContent>
            </Select>
            <Input 
              v-model="customAlert.message"
              placeholder="Alert message"
              class="h-8 text-xs"
            />
          </div>
          <div class="flex items-center gap-2">
            <Button @click="testCustomAlert" size="sm" class="text-xs">
              Show Alert
            </Button>
            <label class="flex items-center gap-1 text-xs">
              <input 
                v-model="customAlert.persistent"
                type="checkbox"
                class="w-3 h-3"
              />
              Persistent
            </label>
          </div>
        </div>
      </CardContent>
    </Card>

    <!-- Future Testing Sections -->
    <Card>
      <CardHeader class="pb-4">
        <CardTitle class="text-lg">Other Component Tests</CardTitle>
        <CardDescription>More testing features will be added here</CardDescription>
      </CardHeader>
      <CardContent>
        <div class="text-center py-8 text-muted-foreground">
          <p class="text-sm">Additional testing panels will be added as new components are developed</p>
        </div>
      </CardContent>
    </Card>
  </div>
</template>
