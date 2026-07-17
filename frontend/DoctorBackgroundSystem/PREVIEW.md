# 本地预览说明

这个项目是 `Vue + Vite`，不能直接双击 `index.html` 预览。

## 开发预览

适合边改边看，页面会自动刷新。

在项目根目录运行：

```powershell
.\start-dev.ps1
```

打开：

```text
http://127.0.0.1:5173/
```

## 打包预览

适合看最终交付效果，会先构建，再启动预览服务。

在项目根目录运行：

```powershell
.\start-preview.ps1
```

打开：

```text
http://127.0.0.1:4173/
```

## 如果脚本被 PowerShell 拦住

可以先运行：

```powershell
powershell -ExecutionPolicy Bypass -File .\start-dev.ps1
```

或：

```powershell
powershell -ExecutionPolicy Bypass -File .\start-preview.ps1
```

## 如果本机已经安装了 Node.js

也可以直接运行：

```powershell
npm run dev
```

和：

```powershell
npm run build
npm run serve
```
