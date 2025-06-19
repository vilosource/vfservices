# Nested Menu Demo - Material Design

## Live Demo

1. **Login**: https://identity.vfservices.viloforge.com/
   - Username: `alice` / Password: `alice123`

2. **View Dashboard**: https://website.vfservices.viloforge.com/dashboard/

## Menu Structure (Up to 4 Levels Deep)

```
Inventory (mdi-box icon)
├── Products
│   ├── All Products
│   ├── Active Products
│   └── Discontinued
├── Categories
│   ├── Category Tree
│   └── Manage Categories
├── Warehouse
│   ├── Stock Levels
│   │   ├── By Location
│   │   └── Low Stock Alerts
│   └── Transfers
│       ├── Pending
│       └── Completed
├── Suppliers
└── Reports
    ├── Inventory Reports
    ├── Stock Movement
    └── Analytics
        ├── Trends
        └── Forecast
```

## Material Design Implementation

### 1. **Visual Hierarchy**
- Top-level items have Material Design Icons (MDI)
- Submenu items have no icons for cleaner appearance
- All submenu items align vertically (no indentation)
- Consistent padding and spacing throughout

### 2. **Bootstrap 5 Integration**
- Uses Bootstrap collapse component
- Smooth expand/collapse animations
- Proper ARIA attributes for accessibility
- Data-bs-toggle for interaction

### 3. **Interactive Features**
- Click to expand/collapse sections
- Blue hover state (#3d7eff)
- Active page highlighting
- Wave ripple effect on click
- Rotating arrow indicators

### 4. **State Management**
- Menu state persists using localStorage
- Remembers expanded sections between page loads
- Active menu item auto-expands parent sections

### 4. **Permission-Based Display**
Different users see different menu depths:

**Alice (Inventory Admin)**
- Sees complete menu with all levels
- Can access Manage Categories
- Has transfer permissions

**Bob (Warehouse Manager)**
- Sees Warehouse section with transfers
- No Suppliers access
- Can't manage categories

**Charlie (Stock Viewer)**
- Only sees Products (no sub-items)
- Very limited menu

## Try It Out

1. Login as different users to see permission filtering
2. Click menu items to expand/collapse
3. Use keyboard arrows to navigate
4. Notice the smooth animations
5. Check how deep nesting maintains visual hierarchy

## Technical Implementation

- Recursive menu rendering
- CSS-based indentation
- JavaScript state management
- Server-side permission filtering
- Maintains state across page loads