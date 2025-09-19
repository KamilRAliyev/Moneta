<script setup>
import { useAlert } from '@/composables/useAlert'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { CheckCircle, XCircle, AlertTriangle, Info, X } from 'lucide-vue-next'

const { alerts, dismissAlert } = useAlert()

const getIcon = (type) => {
  const icons = {
    success: CheckCircle,
    error: XCircle,
    warning: AlertTriangle,
    info: Info
  }
  return icons[type] || Info
}

const getAlertVariant = (type) => {
  const variants = {
    success: 'default',
    error: 'destructive',
    warning: 'default',
    info: 'default'
  }
  return variants[type] || 'default'
}
</script>

<template>
  <div class="fixed top-4 right-4 z-50 space-y-2 max-w-sm">
    <TransitionGroup
      name="alert"
      tag="div"
      class="space-y-2"
    >
      <Alert
        v-for="alert in alerts"
        :key="alert.id"
        :variant="getAlertVariant(alert.type)"
        class="relative shadow-lg bg-black text-white border-0"
      >
        <component 
          :is="getIcon(alert.type)" 
          :class="[
            'h-4 w-4',
            alert.type === 'success' ? '!text-green-500' :
            alert.type === 'error' ? '!text-red-500' :
            alert.type === 'warning' ? '!text-yellow-500' :
            '!text-green-500'
          ]"
        />
        <div class="flex-1">
          <AlertTitle v-if="alert.title">{{ alert.title }}</AlertTitle>
          <AlertDescription>{{ alert.message }}</AlertDescription>
          
          <!-- Action buttons -->
          <div v-if="alert.actions?.length" class="mt-3 flex gap-2">
            <Button
              v-for="action in alert.actions"
              :key="action.label"
              :variant="action.variant || 'outline'"
              size="sm"
              @click="action.action"
            >
              {{ action.label }}
            </Button>
          </div>
        </div>
        
        <!-- Close button -->
        <Button
          v-if="!alert.persistent"
          variant="ghost"
          size="sm"
          class="absolute top-2 right-2 h-6 w-6 p-0"
          @click="dismissAlert(alert.id)"
        >
          <X class="h-3 w-3" />
        </Button>
      </Alert>
    </TransitionGroup>
  </div>
</template>

<style scoped>
.alert-enter-active,
.alert-leave-active {
  transition: all 0.3s ease;
}

.alert-enter-from {
  opacity: 0;
  transform: translateX(100%);
}

.alert-leave-to {
  opacity: 0;
  transform: translateX(100%);
}
</style>
