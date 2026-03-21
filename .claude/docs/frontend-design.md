# Frontend Design System

> This is the canonical UI theme for all Insight Engine frontend work.
> Every new page, component, and modal MUST follow these conventions.

## Theme Overview

Dark, modern B2B SaaS aesthetic. Slate backgrounds, indigo accents, glass cards.
Reference implementation: `src/frontend/src/app/login/page.tsx` and `signup/page.tsx`.

---

## Background

```tsx
// Page background — always
<div className="min-h-screen bg-slate-950 flex items-center justify-center p-4">

// Subtle grid overlay — add to every full-page layout
<div
  className="pointer-events-none fixed inset-0 opacity-[0.03]"
  style={{
    backgroundImage:
      "linear-gradient(#fff 1px, transparent 1px), linear-gradient(90deg, #fff 1px, transparent 1px)",
    backgroundSize: "40px 40px",
  }}
/>
```

---

## Cards / Panels

```tsx
// Primary card
<div className="bg-slate-900/80 backdrop-blur-sm border border-white/10 rounded-2xl p-8 shadow-2xl">

// Secondary / inner panel
<div className="bg-white/5 border border-white/10 rounded-xl p-4">
```

---

## Typography

```tsx
// Page title (brand)
<h1 className="text-2xl font-bold text-white tracking-tight">

// Card heading
<h2 className="text-lg font-semibold text-white mb-6">

// Section heading
<h3 className="text-sm font-semibold text-white">

// Body text
<p className="text-sm text-slate-400">

// Muted / helper text
<span className="text-xs text-slate-500">

// Form field label — always uppercase small caps
<label className="block text-xs font-medium text-slate-400 uppercase tracking-wider mb-1.5">
```

---

## Inputs

```tsx
// Text / email / password input
const INPUT_CLASS =
  "w-full px-4 py-2.5 rounded-xl border border-white/10 bg-white/5 text-white text-sm placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition";

// Select / dropdown
const SELECT_CLASS =
  "w-full px-4 py-2.5 rounded-xl border border-white/10 bg-slate-800 text-white text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition";

// Textarea
const TEXTAREA_CLASS =
  "w-full px-4 py-3 rounded-xl border border-white/10 bg-white/5 text-white text-sm placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition resize-none";
```

**Critical:** Always include `text-white` on inputs. Never omit it — without it, typed text inherits the placeholder colour.

---

## Buttons

```tsx
// Primary CTA
<button className="w-full py-2.5 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:bg-indigo-800 disabled:text-indigo-400 text-white text-sm font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 focus:ring-offset-slate-900 shadow-lg shadow-indigo-500/20">

// Secondary / ghost
<button className="px-4 py-2 rounded-xl border border-white/10 text-slate-300 hover:bg-white/5 text-sm font-medium transition-colors">

// Danger
<button className="px-4 py-2 rounded-xl bg-red-600/20 hover:bg-red-600/30 border border-red-500/30 text-red-400 text-sm font-medium transition-colors">

// Icon button
<button className="p-2 rounded-lg hover:bg-white/5 text-slate-400 hover:text-white transition-colors">
```

---

## Alerts & Errors

```tsx
// Error
<div className="rounded-xl bg-red-500/10 border border-red-500/30 px-4 py-3 text-sm text-red-400">

// Warning
<div className="rounded-xl bg-amber-500/10 border border-amber-500/30 px-4 py-3 text-sm text-amber-400">

// Success
<div className="rounded-xl bg-emerald-500/10 border border-emerald-500/30 px-4 py-3 text-sm text-emerald-400">

// Info
<div className="rounded-xl bg-indigo-500/10 border border-indigo-500/30 px-4 py-3 text-sm text-indigo-400">
```

---

## Brand Icon / Logo

```tsx
// Always use this logo block at the top of auth pages
<div className="text-center mb-8">
  <div className="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-indigo-600 mb-4 shadow-lg shadow-indigo-500/30">
    <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
    </svg>
  </div>
  <h1 className="text-2xl font-bold text-white tracking-tight">Insight Engine</h1>
  <p className="mt-1 text-sm text-slate-400">Cross-domain innovation discovery</p>
</div>
```

---

## Links

```tsx
<a href="/path" className="text-indigo-400 hover:text-indigo-300 font-medium transition-colors">
```

---

## Dividers

```tsx
<hr className="border-white/10 my-6" />

// With label
<div className="relative my-6">
  <hr className="border-white/10" />
  <span className="absolute left-1/2 -translate-x-1/2 -translate-y-1/2 bg-slate-900 px-3 text-xs text-slate-500">
    or
  </span>
</div>
```

---

## Badges / Tags

```tsx
// Default
<span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-white/10 text-slate-300">

// Indigo
<span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-500/20 text-indigo-300">

// Green
<span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-500/20 text-emerald-300">
```

---

## Colour Reference

| Token       | Tailwind class          | Use                          |
|-------------|-------------------------|------------------------------|
| Background  | `bg-slate-950`          | Page background              |
| Surface     | `bg-slate-900`          | Cards, sidebars              |
| Surface 2   | `bg-white/5`            | Input backgrounds, inner panels |
| Border      | `border-white/10`       | All borders                  |
| Text primary | `text-white`           | Headings, input values       |
| Text secondary | `text-slate-400`     | Body, descriptions           |
| Text muted  | `text-slate-500`        | Placeholders, helper text    |
| Accent      | `indigo-600 / indigo-500` | Primary CTA, focus rings, links |
| Error       | `red-400 / red-500`     | Error states                 |
| Success     | `emerald-400 / emerald-500` | Success states           |
| Warning     | `amber-400 / amber-500` | Warning states               |

---

## Layout Rules

- Max card width on auth/centered pages: `max-w-md`
- Max content width on dashboard: `max-w-7xl mx-auto px-6`
- Spacing scale: use `space-y-4` (form fields), `space-y-6` (sections), `gap-4` (grids)
- Border radius: `rounded-xl` for inputs/buttons, `rounded-2xl` for cards
- All interactive elements must have focus rings using `focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 focus:ring-offset-slate-900`
