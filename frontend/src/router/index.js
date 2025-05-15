import { createRouter, createWebHistory } from 'vue-router'
import SleeperImport from '../components/SleeperImport.vue'

// ... existing imports ...

const routes = [
  // ... existing routes ...
  {
    path: '/sleeper/import',
    name: 'SleeperImport',
    component: SleeperImport,
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Navigation guard for authentication
router.beforeEach((to, from, next) => {
  if (to.meta.requiresAuth) {
    // Check if user is authenticated
    const token = localStorage.getItem('sessionToken')
    if (!token) {
      next('/login')
      return
    }
  }
  next()
})

export default router 