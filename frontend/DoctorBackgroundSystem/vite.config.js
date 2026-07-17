const vue = require('@vitejs/plugin-vue')

module.exports = {
  base: './',
  plugins: [vue.default()],
  server: {
    proxy: {
      '/api': {
        target: process.env.VITE_DEV_PROXY_TARGET || 'http://10.250.215.200:8000',
        changeOrigin: true
      }
    }
  }
}
