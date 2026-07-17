# UI-UX Pro Max Usage Guide

This guide is for the current project folder.

Installed skill path:

- `.codex/skills/ui-ux-pro-max/`

Main script:

- `.codex/skills/ui-ux-pro-max/scripts/search.py`

## What This Skill Is Good At

`ui-ux-pro-max` is a searchable UI/UX recommendation skill backed by local CSV datasets and Python scripts.

Use it for:

- design system generation
- style, color, and typography recommendations
- UX and accessibility checks
- chart and layout suggestions
- stack-specific implementation guidance
- UI review and polish passes

## Best Way To Use It In Codex

The easiest path is to name the skill in your prompt.

Prompt examples:

```text
Use ui-ux-pro-max to generate a mobile-first design system for this project.
Product: traditional chinese medicine health consultation app.
Tone: calm, trustworthy, modern, readable.
Output: style, colors, typography, layout, anti-patterns, and Vue implementation notes.
```

```text
Use ui-ux-pro-max to review the current page.
Focus on color hierarchy, form UX, touch feedback, mobile accessibility, and uni-app/Vue implementation advice.
```

```text
Use ui-ux-pro-max first, then refactor the current home page based on the generated design system.
Avoid flashy AI gradients and over-technical visuals.
```

## Running The Script Manually

If `python` is not available in your system PATH, this machine has a bundled Python in Codex desktop:

```powershell
$python = "C:\Users\21036\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
```

Run commands like this:

```powershell
& $python ".codex/skills/ui-ux-pro-max/scripts/search.py" "<query>"
```

If your own Python is available, you can use:

```powershell
python ".codex/skills/ui-ux-pro-max/scripts/search.py" "<query>"
```

## Most Useful Commands

### 1. Generate A Full Design System

Start here first.

```powershell
& $python ".codex/skills/ui-ux-pro-max/scripts/search.py" `
  "traditional chinese medicine health consultation mobile app calm trustworthy modern" `
  --design-system `
  -p "BenCao WenFang" `
  -f markdown
```

What this gives you:

- page pattern
- style direction
- color tokens
- typography pairing
- key effects
- anti-patterns
- delivery checklist

### 2. Persist The Design System To Files

Use this when you want reusable project rules across pages and sessions.

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

This creates:

- `design-system/bencao-wenfang/MASTER.md`
- `design-system/bencao-wenfang/pages/home.md`

Important note:

- the real output path is `design-system/<project-slug>/...`
- it is not just `design-system/MASTER.md`

### 3. Search A Single Domain

Use this after you already have a general direction.

Color:

```powershell
& $python ".codex/skills/ui-ux-pro-max/scripts/search.py" `
  "health wellness trust traditional chinese medicine" `
  --domain color
```

Typography:

```powershell
& $python ".codex/skills/ui-ux-pro-max/scripts/search.py" `
  "traditional chinese elegant readable" `
  --domain typography
```

UX:

```powershell
& $python ".codex/skills/ui-ux-pro-max/scripts/search.py" `
  "form feedback loading error clarity accessibility" `
  --domain ux
```

Mobile/app interface rules:

```powershell
& $python ".codex/skills/ui-ux-pro-max/scripts/search.py" `
  "touch target safe area accessibilityLabel navigation" `
  --domain web
```

Icon suggestions:

```powershell
& $python ".codex/skills/ui-ux-pro-max/scripts/search.py" `
  "medicine consultation diagnosis profile search" `
  --domain icons
```

### 4. Ask For Stack-Specific Guidance

This project is closer to `uni-app + Vue`, so `vue` is the best starting stack.

```powershell
& $python ".codex/skills/ui-ux-pro-max/scripts/search.py" `
  "form state navigation performance" `
  --stack vue
```

Other available stacks include:

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

## Recommended Workflow For This Project

Because this repo looks like a mobile-focused `uni-app / Vue` project, this sequence works well:

### Step 1. Generate And Persist The Design System

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

### Step 2. Add Mobile UX Rules

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

### Step 3. Add Vue Implementation Guidance

```powershell
& $python ".codex/skills/ui-ux-pro-max/scripts/search.py" `
  "form state navigation performance" `
  --stack vue
```

### Step 4. Feed The Result Back Into Codex

Example:

```text
Please refactor the current home page based on design-system/bencao-wenfang/MASTER.md
and design-system/bencao-wenfang/pages/home.md.
Use uni-app / Vue patterns and prioritize mobile usability.
```

## How To Write Better Queries

This skill works much better with English keywords than with Chinese keywords.

Recommended query shape:

- product type
- industry
- tone
- device or surface

Weak query:

```text
chinese medicine page
```

Better query:

```text
traditional chinese medicine health consultation mobile app calm trustworthy modern
```

More examples:

- `healthcare app clean calm accessible`
- `wellness mobile app warm natural minimal`
- `form-heavy consultation app trust readability chinese typography`

## How To Read The Output

Typical design system output includes:

- `Pattern`: page structure and CTA placement
- `Style`: visual direction, effects, performance, accessibility
- `Colors`: token-friendly palette
- `Typography`: heading/body pairing
- `Key Effects`: motion, shadow, and emphasis ideas
- `Avoid`: anti-patterns
- `Pre-Delivery Checklist`: review checklist

If you used `--persist`:

- `MASTER.md` is the global source of truth
- `pages/*.md` contains page-specific overrides

Rule priority:

1. check `pages/<page>.md` first
2. fall back to `MASTER.md` for everything else

## Practical Warnings

### English Queries Are More Reliable

Chinese queries can return results, but the recommendations are usually less stable.

Best practice:

- project name can be Chinese or English
- search keywords should be English whenever possible

### Some Advice Is Web-Oriented

The skill often emphasizes things like:

- `cursor-pointer`
- `hover`
- visible keyboard focus

For this mobile-oriented project, translate those ideas instead of copying them literally:

- `hover` -> pressed state / touch feedback
- `cursor-pointer` -> clear tap affordance
- `focus` -> accessibility and input clarity

### `--domain web` Is A Misleading Name

In this skill, `web` actually maps to app-interface guidance.
It is useful for:

- touch targets
- safe areas
- accessibility labels
- navigation behavior
- form/input interaction

## Troubleshooting

### Codex Does Not Pick Up The Skill

- restart Codex
- confirm `.codex/skills/ui-ux-pro-max/SKILL.md` exists

### `python` Is Not Found

Use the bundled Python path shown earlier in this guide.

### Results Feel Off

Try this order:

1. switch to English keywords
2. make the query more specific
3. run `--design-system` first
4. use `--domain` to deepen one dimension
5. add `--stack vue`

## One Complete Example

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

Then ask Codex:

```text
Refactor the current home page based on design-system/bencao-wenfang/MASTER.md
and design-system/bencao-wenfang/pages/home.md.
Keep the tone calm, trustworthy, and mobile-first.
```
