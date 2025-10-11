import { createRouter, createWebHistory } from 'vue-router'
import Settings from '@/views/Settings.vue'
import Testing from '@/views/Testing.vue'

// Single source of truth for both navigation and routes
export const navigationItems = [
  {
    name: "Dashboard",
    path: "/",
    icon: "DashBoard",
    component: Settings
  },
  {
    name: "Statements",
    path: "/statements",
    icon: "FileText",
    component: () => import('@/views/Statements.vue')
  },
  {
    name: "Transactions",
    path: "/transactions",
    icon: "CreditCard",
    component: () => import('@/views/Transactions.vue')
  },
  {
    name: "Computed Field Rules",
    path: "/rules",
    icon: "FileCog",
    component: () => import('@/views/ComputedFieldRules.vue')
  },
  {
    name: "Reports",
    path: "/reports",
    icon: "BarChart3",
    component: () => import('@/views/Reports.vue')
  },
  {
    name: "Settings",
    path: "/settings", 
    icon: "Settings",
    component: Settings
  },
  {
    name: "Testing",
    path: "/testing",
    icon: "TestTube",
    component: Testing
  },
]

// Generate routes from navigation items
const routes = [
  ...navigationItems.map(item => ({
    path: item.path,
    name: item.name,
    component: item.component
  })),
  // Additional routes not in navigation
  {
    path: '/rules/create',
    name: 'CreateRule',
    component: () => import('@/views/CreateRule.vue')
  },
  {
    path: '/rules/edit/:id',
    name: 'EditRule',
    component: () => import('@/views/CreateRule.vue')
  },
  {
    path: '/reports',
    name: 'Reports',
    component: () => import('@/views/Reports.vue')
  }
]

// Create router instance
const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
