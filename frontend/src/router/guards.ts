import { Router } from 'vue-router'
import { useAuthStore } from '../store/authStore'

export function setupRouteGuards(router: Router) {
  router.beforeEach((to, from, next) => {
    const auth = useAuthStore()
    const isLoggedIn = Boolean(auth.token)

    const publicRoutes = ['/login', '/register']
    const isPublic = publicRoutes.includes(to.path)

    if (!isLoggedIn && !isPublic) {
      next('/login')
    } else {
      next()
    }
  })
}
