import { defineConfig } from 'vite'
import uni from '@dcloudio/vite-plugin-uni'

// 解决 Windows 端口保留导致 Vite 默认 5173 起服务报 EACCES 的问题。
// 5173 落在系统保留区间 5139-5238 内，这里改到保留区间之外的 8080。
// 同时放开 host，方便模拟器/真机/局域网访问。
//
// 注意：uniapp 的 vite 编译器不会在使用自定义 vite.config.js 时自动注入
// @dcloudio/vite-plugin-uni，必须在 plugins 中显式声明，否则 .vue 文件无法解析。
export default defineConfig({
  plugins: [uni()],
  server: {
    port: 8080,
    host: true,
    strictPort: false
  }
})
