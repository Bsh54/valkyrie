---
name: Clinical Precision & Discovery
colors:
  surface: '#f7f9fb'
  surface-dim: '#d8dadc'
  surface-bright: '#f7f9fb'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f2f4f6'
  surface-container: '#eceef0'
  surface-container-high: '#e6e8ea'
  surface-container-highest: '#e0e3e5'
  on-surface: '#191c1e'
  on-surface-variant: '#424752'
  inverse-surface: '#2d3133'
  inverse-on-surface: '#eff1f3'
  outline: '#727783'
  outline-variant: '#c2c6d4'
  surface-tint: '#005db6'
  primary: '#00478d'
  on-primary: '#ffffff'
  primary-container: '#005eb8'
  on-primary-container: '#c8daff'
  inverse-primary: '#a9c7ff'
  secondary: '#006970'
  on-secondary: '#ffffff'
  secondary-container: '#7af1fc'
  on-secondary-container: '#006e75'
  tertiary: '#793100'
  on-tertiary: '#ffffff'
  tertiary-container: '#9f4300'
  on-tertiary-container: '#ffcfb9'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#d6e3ff'
  primary-fixed-dim: '#a9c7ff'
  on-primary-fixed: '#001b3d'
  on-primary-fixed-variant: '#00468c'
  secondary-fixed: '#7df4ff'
  secondary-fixed-dim: '#5dd8e2'
  on-secondary-fixed: '#002022'
  on-secondary-fixed-variant: '#004f54'
  tertiary-fixed: '#ffdbcb'
  tertiary-fixed-dim: '#ffb691'
  on-tertiary-fixed: '#341100'
  on-tertiary-fixed-variant: '#793100'
  background: '#f7f9fb'
  on-background: '#191c1e'
  surface-variant: '#e0e3e5'
  success-docking: '#22C55E'
  warning-energy: '#F97316'
  deep-navy: '#325880'
  structural-blue: '#5E94C3'
  molecular-green: '#5D864F'
typography:
  headline-xl:
    fontFamily: Public Sans
    fontSize: 40px
    fontWeight: '700'
    lineHeight: 48px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Public Sans
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
  headline-md:
    fontFamily: Public Sans
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  code-md:
    fontFamily: JetBrains Mono
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
  label-caps:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '700'
    lineHeight: 16px
    letterSpacing: 0.05em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  base: 4px
  gutter: 24px
  margin-mobile: 16px
  margin-desktop: 32px
  max-width: 1440px
---

## Brand & Style

The design system is engineered for **DrugForge**, a molecular docking laboratory where high-throughput screening meets rigorous pharmaceutical research. The brand personality is "Pharmacy-Tech": a fusion of clinical authority and cutting-edge computational power.

The visual style follows a **Modern Corporate** foundation with a **Technical/Hacker** edge. It prioritizes clarity and precision to evoke trust in scientific results, while utilizing monospaced accents and dense data visualizations to appeal to bio-informaticians and research engineers. The interface should feel like a state-of-the-art laboratory instrument: clean, responsive, and data-dense.

## Colors

The palette is rooted in a clinical white-space environment. 
- **Primary (Medical Blue):** Used for primary actions and brand presence.
- **Secondary (Lab Teal):** Used for interactive sub-elements and navigation highlights.
- **Neutral (Sterile Gray/White):** Dominates the interface to maintain a "clean-room" aesthetic.
- **Accents:** Reserved strictly for semantic meaning—`success-docking` for positive binding affinity and `warning-energy` for high-energy strain or docking failures.
- **Named Colors:** Derived from structural biology references (RCSB), these provide a bridge between traditional scientific databases and the modern DrugForge UI.

## Typography

Typography is used to distinguish between human-readable content and machine-readable data.
- **Public Sans** is utilized for headlines to provide a sturdy, institutional feel.
- **Inter** handles the bulk of UI and body text for maximum legibility at small sizes in dense dashboards.
- **JetBrains Mono** is a functional accent for SMILES strings, PDB IDs, and technical metadata.

Scale hierarchy is kept tight to ensure high information density. Headers should use a slight negative letter-spacing for a modern "tech" look, while labels utilize monospacing to signal technical attributes.

## Layout & Spacing

The layout is based on a **12-column fixed grid** for desktop, optimized for a 1440px max width. This ensures scientific charts and 3D viewports maintain consistent aspect ratios. 

- **Spacing Rhythm:** Based on a 4px baseline grid.
- **Data Density:** Padding in tables and lists should be tight (`8px` to `12px`) to maximize visible data without compromising legibility.
- **Breakpoints:**
  - **Mobile (<768px):** Single column, 16px margins, vertical stacking of data cards.
  - **Tablet (768px - 1024px):** 2-column layout for sidebars and main viewports.
  - **Desktop (>1024px):** Full 12-column utility with sticky side-panels for molecular parameters.

## Elevation & Depth

To maintain a "Clinical" look, elevation is primarily achieved through **Tonal Layers** and **Low-Contrast Outlines** rather than heavy shadows.

- **Surface 0 (Background):** Sterile Gray (#F8FAFC).
- **Surface 1 (Cards/Panels):** Clean White (#FFFFFF) with a 1px border of #E2E8F0.
- **Depth:** Use extremely soft, subtle ambient shadows (0px 4px 12px rgba(0, 0, 0, 0.03)) only for floating elements like dropdowns or active modals.
- **3D Viewports:** Should appear "inset" using a subtle inner shadow to distinguish the molecular visualization space from the flat UI.

## Shapes

The design system utilizes **Soft (0.25rem)** roundedness to maintain a precise, professional character. 

- **Components:** Buttons and input fields use a 4px radius. 
- **Large Elements:** Cards and 3D viewports use 8px (`rounded-lg`) to provide a subtle modern softening.
- **Technical Badges:** Utilize a full pill-shape for "Drug-likeness" tags to distinguish them from interactive buttons.

## Components

- **Buttons:** Primary buttons use `primary_color_hex` with white text. Ghost buttons use `primary_color_hex` outlines for secondary technical actions.
- **Technical Badges:** Small pill-shaped containers using `label-caps` typography. Background colors should be low-opacity versions of the semantic colors (e.g., 10% Green for "Lipinski Pass").
- **3D Viewports:** Framed in a Surface 1 container with an inset shadow. Includes a toolbar for "Rotate," "Zoom," and "Export PDB."
- **Data Tables:** High-density, border-bottom only, with a `code-md` font for chemical IDs. Hover states should use a subtle Lab Teal tint.
- **Specification Code Blocks:** Using `jetbrainsMono` on a slightly darker gray background (#F1F5F9) to denote raw SMILES strings or JSON configuration files.
- **Cards:** Minimal padding (16-24px), subtle 1px border, no heavy shadows. Used for grouping molecular properties.
- **Status Indicators:** Use "Active Molecule Green" for successful docking runs and "Atomic Orange" for potential binding clashes or high-energy warnings.