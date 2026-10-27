if ('serviceWorker' in navigator) {
  window.addEventListener('load', async () => {
    try {
      await navigator.serviceWorker.register('/service-worker.js', { scope: '/', updateViaCache: 'none' });
      // Retire the previous worker, whose scope only covered /static/pwa/.
      const registrations = await navigator.serviceWorker.getRegistrations();
      for (const registration of registrations) {
        const worker = registration.active || registration.waiting || registration.installing;
        if (worker && new URL(worker.scriptURL).pathname === '/static/pwa/sw.js') {
          await registration.unregister();
        }
      }
    } catch (error) {
      console.warn('Portfolio offline support could not be enabled.', error);
    }
  });
}
