# Menu System Demo Guide - Material Design

## Live Demo URLs

### 1. Dashboard with Material Design Menu
Visit: https://website.vfservices.viloforge.com/dashboard/

**Note:** You need to be logged in first. Follow these steps:

### 2. Login Process

1. **Go to Identity Provider**: https://identity.vfservices.viloforge.com/
2. **Login with one of these demo users**:
   - **Alice** (Inventory Manager): `alice` / `alice123`
   - **Bob** (Stock Viewer): `bob` / `bob123`
   - **Charlie** (Warehouse Manager): `charlie` / `charlie123`

3. **After login, visit the dashboard**: https://website.vfservices.viloforge.com/dashboard/

## What You'll See

### Material Design Sidebar Menu
- Clean, modern interface matching material theme
- Top-level "Inventory" item with MDI box icon
- Collapsible sections using Bootstrap 5
- No icons on submenu items for cleaner look
- All submenu items align vertically

### For Alice (Inventory Manager)
- Full Inventory menu with all nested options:
  - Products → All Products, Active Products, Discontinued
  - Categories → Category Tree, Manage Categories
  - Warehouse → Stock Levels → By Location, Low Stock Alerts
  - Warehouse → Transfers → Pending, Completed
  - Suppliers
  - Reports → Inventory Reports, Stock Movement, Analytics

### For Bob (Stock Viewer)
- Limited Inventory menu:
  - Products only (basic view)

### For Charlie (Warehouse Manager)
- Warehouse-focused menu:
  - Products
  - Categories
  - Warehouse (with full nested options)
  - Reports

## Direct API Testing

You can also test the menu API directly:

1. **Login to get JWT token**:
```bash
curl -X POST https://identity.vfservices.viloforge.com/api/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"alice123"}'
```

2. **Get menu from inventory service**:
```bash
curl https://inventory.vfservices.viloforge.com/api/menus/sidebar_menu/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Visual Demo

### Dashboard Screenshot Layout
```
┌─────────────────────────────────────────┐
│  VFServices Dashboard                   │
├─────────────┬───────────────────────────┤
│ INVENTORY   │  Welcome to Dashboard     │
│ ├─ Products │                           │
│ ├─ Categories│  User: alice             │
│ └─ Suppliers│  Roles: inventory_admin   │
│             │                           │
│             │  [Quick Links]            │
│             │  • Analytics              │
│             │  • Settings               │
└─────────────┴───────────────────────────┘
```

## Quick Links

- **Main Page**: https://website.vfservices.viloforge.com/
- **Dashboard**: https://website.vfservices.viloforge.com/dashboard/
- **API Explorer**: https://website.vfservices.viloforge.com/demo/api-explorer/
- **RBAC Demo**: https://website.vfservices.viloforge.com/demo/

## Testing Different Permissions

1. Login as different users to see how the menu changes
2. The menu dynamically adjusts based on each user's role
3. Menu items are filtered server-side for security

## Troubleshooting

If the menu doesn't appear:
1. Make sure you're logged in (check for JWT cookie)
2. Try logging out and back in
3. Clear your browser cache
4. Check the browser console for errors