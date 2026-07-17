# UI-UX Pro Max 使用指南

这是一份面向当前项目的中文版使用说明。

已安装的 skill 目录：

- `.codex/skills/ui-ux-pro-max/`

核心脚本：

- `.codex/skills/ui-ux-pro-max/scripts/search.py`

## 这是什么

`ui-ux-pro-max` 是一个基于本地数据集和 Python 脚本的 UI/UX 辅助 skill，适合用来做这些事：

- 生成设计系统
- 推荐风格、配色、字体和页面结构
- 补充 UX 和可访问性建议
- 给不同技术栈补充实现思路
- 审查现有页面并找出不专业或不稳定的地方

## 最推荐的用法

最省事的方式，是在 Codex 里直接点名使用这个 skill。

可以直接复制这些提示词：

```text
使用 ui-ux-pro-max，为当前项目生成一套移动端设计系统。
产品类型：traditional chinese medicine health consultation app。
气质：calm、trustworthy、modern、readable。
输出：风格、配色、字体、页面结构、反模式，以及 Vue 落地建议。
```

```text
使用 ui-ux-pro-max 审查当前页面。
重点检查：配色层级、表单体验、触摸反馈、移动端可访问性、uni-app / Vue 的实现建议。
```

```text
先使用 ui-ux-pro-max 生成设计系统，再基于结果重构当前首页。
避免花哨的 AI 渐变和过强的科技感。
```

## 手动运行脚本

如果你想先拿到原始推荐结果，再决定怎么落地，可以直接运行脚本。

如果系统里没有可用的 `python`，这台机器可以使用 Codex 自带的 Python：

```powershell
$python = "C:\Users\21036\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
```

运行方式：

```powershell
& $python ".codex/skills/ui-ux-pro-max/scripts/search.py" "<query>"
```

如果你本机已经装了 Python，也可以直接写：

```powershell
python ".codex/skills/ui-ux-pro-max/scripts/search.py" "<query>"
```

## 最常用命令

### 1. 先生成完整设计系统

建议每次都从这一步开始：

```powershell
& $python ".codex/skills/ui-ux-pro-max/scripts/search.py" `
  "traditional chinese medicine health consultation mobile app calm trustworthy modern" `
  --design-system `
  -p "BenCao WenFang" `
  -f markdown
```

这一步通常会给出：

- 页面结构
- 整体风格
- 配色 token
- 字体组合
- 动效方向
- 需要避免的反模式
- 交付前检查项

### 2. 把设计系统保存到本地

如果你想让后续页面都复用同一套规则，使用 `--persist`：

```powershell
& $python ".codex/skills/ui-ux-pro-max/scripts/search.py" `
  "traditional chinese medicine health consultation mobile app calm trustworthy modern" `
  --design-system `
  --persist `
  --page home `
  -p "bencao-wenfang" `
  -f markdown `
  --output-dir .
```

执行后会生成：

- `design-system/bencao-wenfang/MASTER.md`
- `design-system/bencao-wenfang/pages/home.md`

要注意：

- 实际保存路径是 `design-system/<project-slug>/...`
- 不是 `design-system/MASTER.md`

### 3. 只查某一个维度

当你已经有大方向，只想继续补细节时，用 `--domain`。

查配色：

```powershell
& $python ".codex/skills/ui-ux-pro-max/scripts/search.py" `
  "health wellness trust traditional chinese medicine" `
  --domain color
```

查字体：

```powershell
& $python ".codex/skills/ui-ux-pro-max/scripts/search.py" `
  "traditional chinese elegant readable" `
  --domain typography
```

查 UX：

```powershell
& $python ".codex/skills/ui-ux-pro-max/scripts/search.py" `
  "form feedback loading error clarity accessibility" `
  --domain ux
```

查移动端界面规范：

```powershell
& $python ".codex/skills/ui-ux-pro-max/scripts/search.py" `
  "touch target safe area accessibilityLabel navigation" `
  --domain web
```

查图标建议：

```powershell
& $python ".codex/skills/ui-ux-pro-max/scripts/search.py" `
  "medicine consultation diagnosis profile search" `
  --domain icons
```

### 4. 查技术栈建议

当前项目更接近 `uni-app + Vue`，所以优先建议用 `vue`：

```powershell
& $python ".codex/skills/ui-ux-pro-max/scripts/search.py" `
  "form state navigation performance" `
  --stack vue
```

目前可用的 stack 包括：

- `angular`
- `astro`
- `avalonia`
- `flutter`
- `html-tailwind`
- `javafx`
- `jetpack-compose`
- `laravel`
- `nextjs`
- `nuxtjs`
- `nuxt-ui`
- `react`
- `react-native`
- `shadcn`
- `svelte`
- `swiftui`
- `threejs`
- `uno`
- `uwp`
- `vue`
- `winui`
- `wpf`

## 当前项目推荐工作流

结合当前项目更偏移动端、且使用 `uni-app / Vue` 这一点，推荐按下面的顺序使用。

### 第一步：先生成并保存设计系统

```powershell
& $python ".codex/skills/ui-ux-pro-max/scripts/search.py" `
  "traditional chinese medicine health consultation mobile app calm trustworthy modern" `
  --design-system `
  --persist `
  --page home `
  -p "bencao-wenfang" `
  -f markdown `
  --output-dir .
```

### 第二步：补移动端体验规则

```powershell
& $python ".codex/skills/ui-ux-pro-max/scripts/search.py" `
  "touch target safe area loading form accessibility" `
  --domain web
```

```powershell
& $python ".codex/skills/ui-ux-pro-max/scripts/search.py" `
  "form feedback disabled state loading skeleton" `
  --domain ux
```

### 第三步：补 Vue 落地建议

```powershell
& $python ".codex/skills/ui-ux-pro-max/scripts/search.py" `
  "form state navigation performance" `
  --stack vue
```

### 第四步：把规则交给 Codex 实现

例如这样提：

```text
请基于 design-system/bencao-wenfang/MASTER.md 和 design-system/bencao-wenfang/pages/home.md，
重构当前首页的配色、字体层级、按钮样式和表单交互。
技术栈是 uni-app / Vue，优先保证移动端体验。
```

## 查询词怎么写更有效

这个 skill 的底层数据主要是英文，所以：

- 中文查询可以用，但稳定性一般
- 英文关键词通常更准
- 最好把产品类型、行业、气质、端形态一起写进去

不推荐这样写：

```text
中医页面
```

更推荐这样写：

```text
traditional chinese medicine health consultation mobile app calm trustworthy modern
```

还可以参考这些写法：

- `healthcare app clean calm accessible`
- `wellness mobile app warm natural minimal`
- `form-heavy consultation app trust readability chinese typography`

## 如何理解输出结果

设计系统输出通常包含这些部分：

- `Pattern`：页面结构、CTA 摆放和信息顺序
- `Style`：整体视觉方向、动效、性能、可访问性倾向
- `Colors`：主色、背景色、强调色、边框色等 token
- `Typography`：标题字体、正文字体、气质描述
- `Key Effects`：阴影、过渡、强调方式
- `Avoid`：明确不建议使用的反模式
- `Pre-Delivery Checklist`：交付前检查项

如果用了 `--persist`：

- `MASTER.md` 是全局设计规则
- `pages/*.md` 是单页面覆盖规则

推荐读取顺序：

1. 先看 `pages/<page>.md`
2. 没有覆盖项时，再回退到 `MASTER.md`

## 使用时要注意的几件事

### 英文关键词更可靠

我已经验证过，中文查询也能出结果，但英文关键词更容易得到稳定和贴题的建议。

建议做法：

- 项目名可以用中文
- 查询关键词尽量用英文

### 有些建议偏 Web，要转成移动端语义

这个 skill 常会强调：

- `cursor-pointer`
- `hover`
- 可见的 focus 状态

在当前项目里，不要机械照抄，建议这样转换：

- `hover` 转成按压态和点击反馈
- `cursor-pointer` 转成明确的可点击视觉提示
- `focus` 保留为可访问性和输入流程可见性

### `--domain web` 这个名字容易误导

这里的 `web` 不只是网页。
在这个 skill 里，它更接近这些内容：

- 触摸区域
- 安全区
- 无障碍标签
- 导航行为
- 输入控件交互

### `--persist` 的目录要以实际输出为准

当前脚本的真实行为是：

- 保存到 `design-system/<project-slug>/`
- 不是直接保存到 `design-system/`

## 故障排查

### Codex 没有识别到 skill

- 重启 Codex
- 确认 `.codex/skills/ui-ux-pro-max/SKILL.md` 存在

### `python` 命令不可用

使用前面给出的 Codex 自带 Python 路径。

### 结果看起来不准

建议按这个顺序排查：

1. 改用英文关键词
2. 把查询写得更具体
3. 先跑 `--design-system`
4. 再用 `--domain` 深挖单一维度
5. 最后补 `--stack vue`

## 一套可以直接复制的完整示例

```powershell
$python = "C:\Users\21036\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"

& $python ".codex/skills/ui-ux-pro-max/scripts/search.py" `
  "traditional chinese medicine health consultation mobile app calm trustworthy modern" `
  --design-system `
  --persist `
  --page home `
  -p "bencao-wenfang" `
  -f markdown `
  --output-dir .

& $python ".codex/skills/ui-ux-pro-max/scripts/search.py" `
  "touch target safe area loading form accessibility" `
  --domain web

& $python ".codex/skills/ui-ux-pro-max/scripts/search.py" `
  "form feedback disabled state loading skeleton" `
  --domain ux

& $python ".codex/skills/ui-ux-pro-max/scripts/search.py" `
  "form state navigation performance" `
  --stack vue
```

然后在 Codex 里继续这样提：

```text
请基于 design-system/bencao-wenfang/MASTER.md 和 design-system/bencao-wenfang/pages/home.md，
把当前首页改成更适合中医健康咨询产品的移动端视觉风格，
并按 uni-app / Vue 的方式落地。
```
