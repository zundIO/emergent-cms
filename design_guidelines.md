{
  "design_system_name": "The Emerald Monolith — Organic Brutalism",
  "brand_attributes": [
    "editorial-dense",
    "trustworthy",
    "industrial-organic",
    "quietly-premium",
    "fast-and-precise"
  ],
  "north_star": {
    "one_liner": "A Webflow-like CMS editor where content is editable but layout is sacred — boundaries are communicated by surface shifts, not lines.",
    "success_actions": [
      "Select an element on the canvas and immediately understand what can be edited",
      "Edit text/image/link content in the right panel with zero ambiguity",
      "Preview device sizes quickly",
      "Publish with confidence (clear draft/published state)"
    ]
  },
  "implementation_notes_js": {
    "stack": ["React (JS)", "Tailwind", "shadcn/ui"],
    "rule": "This repo uses .js/.jsx components (NOT .tsx). Keep all examples in JS.",
    "testing": "All interactive + key informational elements MUST include data-testid in kebab-case (role-based)."
  },
  "inspiration_fusion": {
    "references": [
      {
        "source": "shadcn neo-brutalism theme",
        "url": "https://www.shadcn.io/theme/neo-brutalism",
        "take": "Brutalist confidence + strong hierarchy; adapt to 'no-line rule' by using surface steps instead of borders."
      },
      {
        "source": "Dribbble — AI dashboard with glassmorphism",
        "url": "https://dribbble.com/shots/27072441-AI-Dashboard-with-Glassmorphism",
        "take": "Use frosted floating panels for top toolbar menus / popovers; keep opacity ~80% with blur 12px."
      },
      {
        "source": "Webflow Made in Webflow — brutalism/neubrutalism galleries",
        "url": "https://webflow.com/made-in-webflow/brutalism",
        "take": "Editorial spacing + bold icon rails; translate into a compact, professional CMS workspace."
      }
    ],
    "style_recipe": "Organic Brutalism (raw, honest surfaces + subtle grain) + Glassmorphism (floating utilities) + High-density enterprise UI (32px controls)."
  },
  "color_system": {
    "gradient_restriction_rule": {
      "prohibited": [
        "blue-500 to purple-600",
        "purple-500 to pink-500",
        "green-500 to blue-500",
        "red to pink",
        "any dark/saturated multi-stop gradients"
      ],
      "rules": [
        "NEVER let gradients cover more than 20% of the viewport.",
        "NEVER apply gradients to text-heavy content/reading areas.",
        "NEVER use gradients on small UI elements (<100px width).",
        "NEVER stack multiple gradient layers in the same viewport.",
        "IF gradient area exceeds 20% OR impacts readability THEN fallback to solid colors."
      ],
      "allowed_usage": [
        "Hero/header strip behind top toolbar (subtle, low-contrast)",
        "Decorative overlays (noise + faint emerald bloom)",
        "Primary CTA button only (large enough)"
      ]
    },
    "semantic_tokens_css": {
      "where": "/app/frontend/src/index.css (override :root and .dark tokens)",
      "tokens": {
        "--bg": "#121414",
        "--sunken": "#0d0e0e",
        "--elevated": "#292a2a",
        "--on-surface": "#e3e2e2",
        "--muted": "#a7a7a7",
        "--muted-2": "#7b7b7b",
        "--primary": "#10b981",
        "--primary-2": "#4edea3",
        "--primary-dim": "rgba(16,185,129,0.55)",
        "--primary-fixed-dim": "rgba(16,185,129,0.75)",
        "--danger": "#ef4444",
        "--warning": "#f59e0b",
        "--info": "#38bdf8",
        "--focus-ring": "rgba(78,222,163,0.55)",
        "--glass": "rgba(41,42,42,0.80)",
        "--glass-borderless": "rgba(255,255,255,0.06)",
        "--shadow-ambient": "0 20px 40px rgba(0,0,0,0.4)"
      },
      "shadcn_hsl_mapping": {
        "note": "shadcn tokens are HSL. Convert these hex values to HSL when implementing. Keep the semantic intent identical.",
        "must_change": [
          "--background, --card, --popover => use bg/sunken/elevated",
          "--foreground => on-surface (NOT pure white)",
          "--primary => emerald",
          "--border/--input => should NOT be used for 1px borders; keep very low-contrast for internal component needs"
        ]
      }
    },
    "surface_hierarchy": {
      "levels": [
        { "name": "App background", "color": "#121414", "usage": "workspace base" },
        { "name": "Sunken", "color": "#0d0e0e", "usage": "canvas surround, sidebars wells" },
        { "name": "Elevated", "color": "#292a2a", "usage": "panels, cards, toolbars" },
        { "name": "Glass floating", "color": "rgba(41,42,42,0.80)", "usage": "popovers, dropdowns, floating tool palettes" }
      ],
      "no_line_rule": "Do not use 1px separators as boundaries. Use surface steps, padding, and subtle shadows instead."
    }
  },
  "typography": {
    "fonts": {
      "headlines": {
        "family": "Space Grotesk",
        "usage": "page title, panel titles, table numerals",
        "weights": [500, 600, 700]
      },
      "body_ui": {
        "family": "Inter",
        "usage": "all UI labels, helper text, form content",
        "weights": [400, 500, 600]
      }
    },
    "google_fonts_import": {
      "where": "/app/frontend/src/index.css",
      "css": "@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Space+Grotesk:wght@500;600;700&display=swap');"
    },
    "scale": {
      "h1": "text-4xl sm:text-5xl lg:text-6xl font-semibold tracking-tight",
      "h2": "text-base md:text-lg font-medium text-[color:var(--muted)]",
      "panel_title": "text-sm font-semibold tracking-wide",
      "label": "text-xs font-medium text-[color:var(--muted)]",
      "body": "text-sm leading-6 text-[color:var(--on-surface)]",
      "mono_numbers": "font-[family:Space_Grotesk] tabular-nums"
    },
    "text_rules": [
      "Never use pure white (#fff). Use on-surface #e3e2e2.",
      "Use Inter for dense UI; reserve Space Grotesk for headings and numeric emphasis.",
      "Prefer tighter tracking for headings (tracking-tight) and normal tracking for body."
    ]
  },
  "layout_grid": {
    "workspace": {
      "structure": "Left icon rail (56px) + Center canvas (fluid) + Right properties panel (360–420px) + Top toolbar (56px)",
      "mobile": "On mobile: left rail collapses into bottom bar; right panel becomes a Sheet/Drawer; canvas becomes scrollable with pinch/zoom disabled (use device presets instead).",
      "spacing": {
        "major_group_gap": "24px (editorial feel)",
        "panel_padding": "p-4",
        "dense_row_gap": "gap-2",
        "canvas_padding": "p-6 md:p-10"
      }
    },
    "canvas": {
      "max_width": "max-w-[1100px]",
      "frame": "rounded-[6px] bg-[color:var(--sunken)] p-6",
      "element_hit_area": "min-h-[28px] px-2 py-1"
    }
  },
  "components": {
    "component_path": {
      "shadcn_primary": "/app/frontend/src/components/ui",
      "must_use": [
        "button.jsx",
        "input.jsx",
        "textarea.jsx",
        "tabs.jsx",
        "badge.jsx",
        "tooltip.jsx",
        "dropdown-menu.jsx",
        "popover.jsx",
        "scroll-area.jsx",
        "resizable.jsx",
        "collapsible.jsx",
        "dialog.jsx",
        "sheet.jsx",
        "table.jsx",
        "sonner.jsx"
      ]
    },
    "buttons": {
      "radius": "rounded-[4px] (0.25rem)",
      "variants": {
        "primary": {
          "style": "Large-enough gradient only",
          "tailwind": "bg-[linear-gradient(135deg,#4edea3,#10b981)] text-[#0b0c0c] shadow-[0_10px_24px_rgba(0,0,0,0.35)] hover:brightness-[1.03] active:brightness-[0.98]",
          "focus": "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[color:var(--focus-ring)] focus-visible:ring-offset-0"
        },
        "ghost": {
          "tailwind": "bg-transparent text-[color:var(--on-surface)] hover:bg-[rgba(255,255,255,0.06)]",
          "focus": "focus-visible:ring-2 focus-visible:ring-[color:var(--focus-ring)]"
        },
        "text": {
          "tailwind": "bg-transparent text-[color:var(--muted)] hover:text-[color:var(--on-surface)]"
        }
      },
      "micro_interaction": "On hover: subtle brightness shift; on press: scale-95 (only on buttons, not globally)."
    },
    "inputs": {
      "density": "h-8 (32px)",
      "style": "No borders; use background shift + emerald focus line",
      "tailwind": "h-8 bg-[color:var(--sunken)] text-[color:var(--on-surface)] placeholder:text-[color:var(--muted-2)] rounded-[4px] px-3",
      "focus_accent_line": {
        "implementation": "Use a pseudo-element or inset shadow to create a 2px emerald line at bottom on focus.",
        "tailwind_hint": "focus-visible:shadow-[inset_0_-2px_0_0_rgba(78,222,163,0.9)]"
      }
    },
    "badges": {
      "draft": "bg-[rgba(245,158,11,0.14)] text-[#fbbf24]",
      "published": "bg-[rgba(16,185,129,0.14)] text-[#4edea3]",
      "muted": "bg-[rgba(255,255,255,0.06)] text-[color:var(--muted)]"
    },
    "tabs": {
      "top_toolbar_tabs": "Use shadcn Tabs with pill-less, underline-less style; indicate active via background shift (elevated) and emerald dot indicator.",
      "tailwind": "data-[state=active]:bg-[rgba(255,255,255,0.06)] data-[state=active]:text-[color:var(--on-surface)]"
    },
    "sidebar": {
      "left_icon_rail": {
        "width": "w-14",
        "item": "h-10 w-10 rounded-[4px] grid place-items-center",
        "active": "bg-[rgba(16,185,129,0.14)] text-[color:var(--primary-2)]",
        "inactive": "text-[color:var(--primary-fixed-dim)] hover:bg-[rgba(255,255,255,0.06)]"
      },
      "tooltip": "Every icon-only control must have Tooltip with label."
    },
    "panels": {
      "right_properties_panel": {
        "width": "w-[380px] lg:w-[420px]",
        "surface": "bg-[color:var(--elevated)]",
        "shadow": "shadow-[var(--shadow-ambient)]",
        "sections": "Use Collapsible for Typography/Content/Image/Link; section headers are sticky within ScrollArea."
      },
      "floating_popovers": {
        "style": "Glassmorphism",
        "tailwind": "bg-[rgba(41,42,42,0.80)] backdrop-blur-[12px] shadow-[var(--shadow-ambient)]"
      }
    },
    "tables": {
      "rule": "No divider lines. Use alternating row surfaces + padding.",
      "row_styles": {
        "odd": "bg-[rgba(255,255,255,0.02)]",
        "even": "bg-[rgba(255,255,255,0.05)]",
        "hover": "hover:bg-[rgba(16,185,129,0.08)]"
      },
      "numbers": "Use Space Grotesk + tabular-nums for numeric columns."
    },
    "canvas_selection": {
      "selected_outline": "2px emerald glow (not a border line everywhere; only on selected element)",
      "tailwind": "ring-2 ring-[rgba(78,222,163,0.85)] shadow-[0_0_0_6px_rgba(16,185,129,0.10)]",
      "hover": "hover:shadow-[0_0_0_6px_rgba(16,185,129,0.06)]",
      "label": "On selection, show a small floating label (glass) with element type + path."
    }
  },
  "motion_microinteractions": {
    "library": {
      "recommended": "framer-motion",
      "install": "npm i framer-motion",
      "usage": [
        "Panel entrance (right panel slide-in)",
        "Canvas selection label fade/scale",
        "Sidebar active indicator transitions"
      ]
    },
    "principles": [
      "No universal transition (never transition: all).",
      "Use 120–180ms for hover feedback; 180–240ms for panel transitions.",
      "Easing: cubic-bezier(0.2, 0.8, 0.2, 1) for premium feel.",
      "Respect prefers-reduced-motion: reduce (disable parallax/scale)."
    ],
    "tailwind_patterns": {
      "hover": "transition-colors duration-150",
      "press": "active:scale-[0.98] transition-transform duration-150",
      "panel": "transition-[transform,opacity] duration-200"
    }
  },
  "texture_and_background": {
    "noise_overlay": {
      "rule": "Use subtle grain to make dark surfaces feel organic; keep opacity <= 0.06.",
      "css_snippet": ".noise::before{content:'';position:absolute;inset:0;background-image:url('data:image/svg+xml;utf8,<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"180\" height=\"180\"><filter id=\"n\"><feTurbulence type=\"fractalNoise\" baseFrequency=\"0.8\" numOctaves=\"3\" stitchTiles=\"stitch\"/></filter><rect width=\"180\" height=\"180\" filter=\"url(%23n)\" opacity=\"0.35\"/></svg>');mix-blend-mode:overlay;opacity:.06;pointer-events:none;border-radius:inherit;}"
    },
    "image_urls": [
      {
        "category": "background-texture",
        "description": "Dark concrete/grain texture for subtle backdrop in login or empty states (use as low-opacity overlay only)",
        "url": "https://images.unsplash.com/photo-1574110537361-ff1948fc4a57?crop=entropy&cs=srgb&fm=jpg&ixlib=rb-4.1.0&q=85"
      },
      {
        "category": "background-texture",
        "description": "Dark road/concrete texture for canvas surround (very subtle, blurred)",
        "url": "https://images.unsplash.com/photo-1630668660451-777d1e5222e0?crop=entropy&cs=srgb&fm=jpg&ixlib=rb-4.1.0&q=85"
      },
      {
        "category": "background-texture",
        "description": "Organic ring texture for 'Organic Brutalism' accent in marketing/login side panel",
        "url": "https://images.unsplash.com/photo-1577198253878-285d6ac85592?crop=entropy&cs=srgb&fm=jpg&ixlib=rb-4.1.0&q=85"
      }
    ]
  },
  "accessibility": {
    "contrast": [
      "Ensure on-surface (#e3e2e2) on bg (#121414) meets WCAG AA.",
      "Muted text must still be readable; avoid going below ~#7b7b7b on bg."
    ],
    "focus": [
      "All interactive elements must have visible focus ring using emerald focus token.",
      "Do not remove outlines without replacement."
    ],
    "hit_targets": [
      "Icon buttons: min 40x40.",
      "Canvas elements: ensure selectable hit area >= 28px height."
    ]
  },
  "data_testid_conventions": {
    "pattern": "kebab-case describing role",
    "examples": [
      "data-testid=\"login-form-submit-button\"",
      "data-testid=\"editor-left-rail-pages-button\"",
      "data-testid=\"editor-topbar-publish-button\"",
      "data-testid=\"editor-canvas-selected-element-label\"",
      "data-testid=\"properties-panel-typography-section\"",
      "data-testid=\"pages-list-modal\""
    ]
  },
  "instructions_to_main_agent": [
    "Replace default CRA App.css centering styles; do NOT center the app container.",
    "Override shadcn tokens in index.css to match Emerald Monolith surfaces and on-surface text (no pure white).",
    "Enforce the No-Line Rule: remove separators/borders; use surface shifts and padding for grouping.",
    "Use shadcn Resizable for left/center/right workspace; ScrollArea inside side panels.",
    "Canvas selection: ring + glow only on selected element; show a small glass label with element type/path.",
    "Inputs must be 32px height and show emerald accent line on focus (inset shadow).",
    "Primary button gradient is allowed (large CTA only). Avoid gradients elsewhere (<=20% viewport).",
    "Use Tooltip for icon-only sidebar items.",
    "All interactive + key informational elements must include data-testid attributes."
  ],
  "appendix_general_ui_ux_design_guidelines": "- You must **not** apply universal transition. Eg: `transition: all`. This results in breaking transforms. Always add transitions for specific interactive elements like button, input excluding transforms\n- You must **not** center align the app container, ie do not add `.App { text-align: center; }` in the css file. This disrupts the human natural reading flow of text\n- NEVER: use AI assistant Emoji characters like`🤖🧠💭💡🔮🎯📚🎭🎬🎪🎉🎊🎁🎀🎂🍰🎈🎨🎰💰💵💳🏦💎🪙💸🤑📊📈📉💹🔢🏆🥇 etc for icons. Always use **FontAwesome cdn** or **lucid-react** library already installed in the package.json\n\n **GRADIENT RESTRICTION RULE**\nNEVER use dark/saturated gradient combos (e.g., purple/pink) on any UI element.  Prohibited gradients: blue-500 to purple 600, purple 500 to pink-500, green-500 to blue-500, red to pink etc\nNEVER use dark gradients for logo, testimonial, footer etc\nNEVER let gradients cover more than 20% of the viewport.\nNEVER apply gradients to text-heavy content or reading areas.\nNEVER use gradients on small UI elements (<100px width).\nNEVER stack multiple gradient layers in the same viewport.\n\n**ENFORCEMENT RULE:**\n    • Id gradient area exceeds 20% of viewport OR affects readability, **THEN** use solid colors\n\n**How and where to use:**\n   • Section backgrounds (not content backgrounds)\n   • Hero section header content. Eg: dark to light to dark color\n   • Decorative overlays and accent elements only\n   • Hero section with 2-3 mild color\n   • Gradients creation can be done for any angle say horizontal, vertical or diagonal\n\n- For AI chat, voice application, **do not use purple color. Use color like light green, ocean blue, peach orange etc**\n\n</Font Guidelines>\n\n- Every interaction needs micro-animations - hover states, transitions, parallax effects, and entrance animations. Static = dead. \n   \n- Use 2-3x more spacing than feels comfortable. Cramped designs look cheap.\n\n- Subtle grain textures, noise overlays, custom cursors, selection states, and loading animations: separates good from extraordinary.\n   \n- Before generating UI, infer the visual style from the problem statement (palette, contrast, mood, motion) and immediately instantiate it by setting global design tokens (primary, secondary/accent, background, foreground, ring, state colors), rather than relying on any library defaults. Don't make the background dark as a default step, always understand problem first and define colors accordingly\n    Eg: - if it implies playful/energetic, choose a colorful scheme\n           - if it implies monochrome/minimal, choose a black–white/neutral scheme\n\n**Component Reuse:**\n\t- Prioritize using pre-existing components from src/components/ui when applicable\n\t- Create new components that match the style and conventions of existing components when needed\n\t- Examine existing components to understand the project's component patterns before creating new ones\n\n**IMPORTANT**: Do not use HTML based component like dropdown, calendar, toast etc. You **MUST** always use `/app/frontend/src/components/ui/ ` only as a primary components as these are modern and stylish component\n\n**Best Practices:**\n\t- Use Shadcn/UI as the primary component library for consistency and accessibility\n\t- Import path: ./components/[component-name]\n\n**Export Conventions:**\n\t- Components MUST use named exports (export const ComponentName = ...)\n\t- Pages MUST use default exports (export default function PageName() {...})\n\n**Toasts:**\n  - Use `sonner` for toasts\"\n  - Sonner component are located in `/app/src/components/ui/sonner.tsx`\n\nUse 2–4 color gradients, subtle textures/noise overlays, or CSS-based noise to avoid flat visuals."
}
