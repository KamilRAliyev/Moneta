<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Button } from '@/components/ui/button'
import ThemeToggle from '@/components/ThemeToggle.vue'
import HealthMonitor from '@/components/HealthMonitor.vue'
import { navigationItems } from '@/router/router.js'
import { Home, CreditCard, BarChart3, Settings, TestTube, FileText, ChevronLeft, ChevronRight, FileCog } from 'lucide-vue-next'

const router = useRouter()
const route = useRoute()
const isCollapsed = ref(false)

const toggleSidebar = () => {
  isCollapsed.value = !isCollapsed.value
}

const navigateTo = (path) => {
  router.push(path)
}

const isActiveRoute = (path) => {
  return route.path === path
}

const getIcon = (iconName) => {
  const icons = {
    Home,
    CreditCard,
    BarChart3,
    Settings,
    TestTube,
    FileText, 
    FileCog
  }
  return icons[iconName] || Home
}
</script>

<template>
  <div class="flex h-screen">
    <!-- Sidebar -->
    <div :class="[
      'bg-card border-r transition-all duration-300 flex flex-col',
      isCollapsed ? 'w-16' : 'w-64'
    ]">
      <!-- Header -->
      <div class="p-4 border-b">
        <div class="flex items-center justify-between">
          <div v-if="!isCollapsed" class="text-lg font-semibold">Moneta</div>
          <Button @click="toggleSidebar" variant="ghost" size="icon">
            <ChevronLeft v-if="!isCollapsed" class="h-4 w-4" />
            <ChevronRight v-else class="h-4 w-4" />
          </Button>
        </div>
      </div>

      <!-- Navigation -->
      <nav class="flex-1 p-4 space-y-2">
        <div v-for="item in navigationItems" :key="item.path" class="flex items-center">
          <Button 
            @click="navigateTo(item.path)"
            :variant="isActiveRoute(item.path) ? 'secondary' : 'ghost'"
            :class="[
              'w-full justify-start',
              isCollapsed ? 'px-2' : 'px-3',
              isActiveRoute(item.path) ? 'bg-accent' : ''
            ]"
          >
            <component :is="getIcon(item.icon)" class="h-4 w-4" />
            <span v-if="!isCollapsed" class="ml-3">{{ item.name }}</span>
          </Button>
        </div>
      </nav>

      <!-- Health Monitor -->
      <div class="p-4 border-t">
        <HealthMonitor :is-collapsed="isCollapsed" />
      </div>

      <!-- Theme Toggle -->
      <div class="p-4 border-t">
        <ThemeToggle :is-collapsed="isCollapsed" />
      </div>
    </div>

    <!-- Main Content -->
    <div class="flex-1 bg-background">
      <slot />
    </div>
  </div>
</template>