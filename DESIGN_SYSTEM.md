# DeFi Yield Guard Bot - Spark-Inspired Design System

## 🎨 Overview

This dashboard features a modern, Spark Protocol-inspired design system with dark backgrounds, gradient mesh effects, bold typography, and Iconify icons.

---

## 🌈 Color Palette

### Primary Gradient Colors
- **Purple**: `#6B5FED` - Primary brand color
- **Blue**: `#4F7BF5` - Secondary brand color
- **Teal**: `#3DBAA5` - Success/positive metrics
- **Orange**: `#E89B5F` - Warning/risk indicators
- **Gold**: `#D4A574` - Premium/highlight accents

### Accent Colors
- **Light Purple**: `#8B7BED`
- **Light Teal**: `#5DD4C1`
- **Light Orange**: `#F5B97F`
- **Success Green**: `#51CF66`
- **Error Red**: `#FF6B6B`

### Background Colors
- **Primary**: `#0F1419` - Almost black main background
- **Secondary**: `#1A1F26` - Dark grey for cards
- **Tertiary**: `#242930` - Elevated surfaces
- **Elevated**: `#2D333A` - Modals and popups

### Text Colors
- **Primary**: `#FFFFFF` - White for headings
- **Secondary**: `#B8BCC4` - Light grey for body text
- **Tertiary**: `#7B8088` - Muted grey for labels
- **Disabled**: `#4A4D52` - Disabled text

### Border Colors
- **Primary**: `#2A2F36` - Subtle borders
- **Accent**: `#3A4048` - Emphasized borders
- **Divider**: `#242930` - Section dividers

---

## 📝 Typography

### Font Family
- **Primary**: Space Grotesk (300, 400, 500, 600, 700)
- **Monospace**: JetBrains Mono (400, 500, 600, 700) - For numbers and metrics

### Heading Styles
- **H1**: 3.5rem, 700 weight, uppercase, -0.04em letter-spacing, purple-to-teal gradient
- **H2**: 2.25rem, 700 weight, uppercase, -0.03em letter-spacing
- **H3**: 1.25rem, 600 weight, uppercase, -0.02em letter-spacing

### Text Styles
- All headings are **UPPERCASE** for that bold Spark aesthetic
- Tight letter-spacing for modern look
- Body text uses 1rem with 1.6 line-height for readability

---

## 🎭 Visual Effects

### Gradient Meshes (Background)
Three overlapping radial gradients create depth:
1. **Purple mesh** at top-left (20%, 20%)
2. **Teal mesh** at bottom-right (80%, 80%)
3. **Orange mesh** at center (50%, 50%)

### Card Gradients (Hover Effects)
- **Purple Card**: `rgba(107, 95, 237, 0.15)` → `rgba(79, 123, 245, 0.1)`
- **Teal Card**: `rgba(61, 186, 165, 0.15)` → `rgba(93, 212, 193, 0.1)`
- **Orange Card**: `rgba(232, 155, 95, 0.15)` → `rgba(212, 165, 116, 0.1)`

### Glow Effects
- **Purple Glow**: `rgba(107, 95, 237, 0.4)`
- **Teal Glow**: `rgba(61, 186, 165, 0.4)`
- **Orange Glow**: `rgba(232, 155, 95, 0.4)`
- **Blue Glow**: `0 0 15px rgba(79, 123, 245, 0.5)`

### Shadows
- **Small**: `rgba(0, 0, 0, 0.3)`
- **Medium**: `rgba(0, 0, 0, 0.4)`
- **Large**: `rgba(0, 0, 0, 0.6)`

---

## 🎴 Bento Grid Layout

### Grid Configuration
```css
display: grid;
grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
gap: 1rem;
```

### Card Styles
- **Background**: Dark grey (#1A1F26)
- **Border**: Subtle (#2A2F36)
- **Border Radius**: 12px
- **Padding**: 2.5rem
- **Transition**: 0.4s cubic-bezier(0.4, 0, 0.2, 1)

### Hover Effects
- Transforms up by 2px
- Border glows with purple
- Box shadow intensifies
- Gradient overlay fades in

### Modifiers
- `.bento-wide`: `grid-column: span 2`
- `.bento-tall`: `grid-row: span 2`
- `.bento-large`: Both span 2

---

## 🎯 Iconify Icons

### Icon Library
Using Material Design Icons (mdi) via Iconify CDN:
```html
<script src="https://code.iconify.design/3/3.1.0/iconify.min.js"></script>
```

### Landing Page Icons
- **Hero**: `mdi:shield-check` - Shield with checkmark
- **Quick Start**: `mdi:lightning-bolt` - Lightning bolt
- **Returns**: `mdi:trending-up` - Trending up arrow
- **Risk**: `mdi:alert-circle-outline` - Alert circle
- **Protocols**: `mdi:bank` - Bank building
- **Aave**: `cryptocurrency:aave` - Aave logo
- **Morpho**: `mdi:atom` - Atom symbol
- **Features**: `mdi:star-check` - Star with check
- **Feature Items**: `mdi:check-circle` - Check circle
- **Get Started**: `mdi:rocket-launch` - Rocket

### Dashboard Icons
- **Sidebar**: `mdi:shield-check` - Shield
- **Calculator**: `mdi:calculator` - Calculator
- **Chart**: `mdi:chart-line` - Line chart
- **Cash**: `mdi:cash-multiple` - Money stack

### Icon Styling
```html
<span class="iconify"
      data-icon="mdi:icon-name"
      data-inline="false"
      style="vertical-align: middle;">
</span>
```

---

## 📊 Chart Styling

### Plotly Template Colors
- **Primary**: `#6B5FED` (Purple)
- **Secondary**: `#3DBAA5` (Teal)
- **Tertiary**: `#E89B5F` (Orange)
- **Quaternary**: `#4F7BF5` (Blue)
- **Quinary**: `#D4A574` (Gold)

### Chart Background
- **Paper**: `#1A1F26` (Card background)
- **Plot**: `#0F1419` (Main background)
- **Grid**: `#2A2F36` (Subtle lines)

---

## 🎨 Component Guidelines

### Metric Cards
- Display large numbers in JetBrains Mono
- Use gradient colors for values
- Label text in uppercase, small, tertiary color
- Include relevant Iconify icon

### Buttons
- Primary: Gradient purple to blue
- Border radius: 12px
- Font weight: 600
- Hover: Lift effect + glow

### Input Fields
- Background: Tertiary (#242930)
- Border: Primary (#2A2F36)
- Focus: Blue border + glow effect
- Border radius: 12px
- Padding: 0.75rem 1rem

### Tables
- Header: Gradient background, uppercase text
- Rows: Hover effect with tertiary background
- Border: Subtle primary color
- Border radius: 16px container

---

## 🚀 Usage Examples

### Importing Colors
```python
from styles.color_palette import FintechColorPalette as colors

# Use in code
background = colors.BG_PRIMARY
heading_color = colors.GRADIENT_PURPLE
```

### Creating a Bento Card
```html
<div class="bento-item">
    <h3 style="color: {colors.GRADIENT_PURPLE};">
        <span class="iconify" data-icon="mdi:icon-name"></span>
        Title
    </h3>
    <p style="color: {colors.TEXT_SECONDARY};">
        Description text
    </p>
</div>
```

### Applying CSS
```python
from styles.custom_css import get_custom_css

st.markdown(get_custom_css(), unsafe_allow_html=True)
```

---

## 📱 Responsive Design

### Breakpoints
- Mobile: < 768px
- Tablet: 768px - 1024px
- Desktop: > 1024px

### Grid Adaptation
- Bento grid uses `auto-fit` with 300px minimum
- Cards stack vertically on mobile
- Wide cards become full-width on small screens

---

## ✨ Animation Principles

### Timing Functions
- Standard: `cubic-bezier(0.4, 0, 0.2, 1)` - Material Design
- Hover: 0.3s - 0.4s duration
- Transition: 0.4s for smooth effects

### Micro-interactions
- Cards lift on hover (-2px transform)
- Borders glow with theme colors
- Gradients fade in smoothly
- Shadows intensify on elevation

---

## 🎯 Best Practices

1. **Always use uppercase for headings** - Matches Spark aesthetic
2. **Use JetBrains Mono for numbers** - Better readability for metrics
3. **Apply gradient overlays on hover** - Creates depth
4. **Include Iconify icons** - Better than emoji, scalable
5. **Maintain 1rem gap** between bento cards - Tighter, modern spacing
6. **Use gradient mesh background** - Adds visual interest without clutter
7. **Apply purple/teal/orange theme consistently** - Brand cohesion

---

## 🔗 Resources

- **Iconify**: https://iconify.design/
- **Space Grotesk Font**: Google Fonts
- **JetBrains Mono Font**: Google Fonts
- **Material Design Icons**: https://materialdesignicons.com/

---

## 📝 Version History

- **v2.0** - Spark-inspired redesign with Iconify icons
- **v1.0** - Initial Streamlit dashboard

---

**Built for DeFi Yield Guard Bot | Spark Protocol Aesthetic**
