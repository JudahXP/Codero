import { Href, Router } from 'expo-router';

export function safeBack(router: Router, fallback: Href = '/home') {
  try {
    if (router.canGoBack && router.canGoBack()) {
      router.back();
      return;
    }
  } catch (error) {
    // fall through to fallback
  }
  router.replace(fallback);
}
