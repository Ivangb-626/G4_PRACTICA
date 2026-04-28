import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../store/authStore'

export function useAuth() {
  const auth = useAuthStore()
  const router = useRouter()

  const isLoggedIn = computed(() => Boolean(auth.token))
  const username = computed(() => auth.username)
  const token = computed(() => auth.token)

  async function logout() {
    auth.logout()
    await router.push('/login')
  }

  return {
    isLoggedIn,
    username,
    token,
    logout
  }
}
