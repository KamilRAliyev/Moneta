import { createRouter, createWebHistory } from 'vue-router'
import Settings from '@/views/Settings.vue'
import Testing from '@/views/Testing.vue'

// Single source of truth for both navigation and routes
export const navigationItems = [
  {
    name: "Settings",
    path: "/",
    icon: "Settings",
    component: Settings
  },
  {
    name: "Statements",
    path: "/statements",
    icon: "FileText",
    component: () => import('@/views/Statements.vue')
  },
  {
    name: "Testing",
    path: "/testing",
    icon: "TestTube",
    component: Testing
  },
  {
    name: "Settings",
    path: "/settings", 
    icon: "Settings",
    component: Settings
  }
]

// Generate routes from navigation items
const routes = navigationItems.map(item => ({
  path: item.path,
  name: item.name,
  component: item.component
}))

// Create router instance
const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
