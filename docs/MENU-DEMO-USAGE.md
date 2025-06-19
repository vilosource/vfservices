# Menu System Demo - Usage Guide

## Accessing the Material Design Menu

The menu system now features a modern Material Design interface with smooth animations and Bootstrap 5 integration.

### 1. Login
Go to https://website.vfservices.viloforge.com and login as alice (username: alice, password: alice123)

### 2. Navigate to Dashboard
After logging in, you'll be redirected to the dashboard at https://website.vfservices.viloforge.com/dashboard/

### 3. Using the Material Design Menu
The sidebar menu features a clean, modern design with collapsible sections:

1. **Click on "Inventory"** - The main menu item with an icon (mdi-box) expands to show:
   - Products (no icon)
   - Categories (no icon)
   - Warehouse (no icon)
   - Suppliers (no icon)
   - Reports (no icon)

2. **Click on any submenu item** to expand it further. For example:
   - Click "Products" to see:
     - All Products
     - Active Products
     - Discontinued
   
   - Click "Warehouse" to see:
     - Stock Levels
     - Transfers

3. **Deep Nesting Example** - Click through:
   - Inventory → Warehouse → Stock Levels → By Location
   - This demonstrates the 4-level deep nesting capability

### Material Design Features

- **Bootstrap 5 Collapse** - Smooth expand/collapse animations
- **Material Design Icons (MDI)** - Only on top-level menu items
- **Clean Visual Hierarchy** - All submenu items align vertically
- **Hover Effects** - Blue highlighting on hover (#3d7eff)
- **Active State** - Current page highlighted in blue
- **Persistent State** - Menu remembers expanded sections using localStorage
- **Wave Ripple Effect** - Material design ripple animation on click
- **Responsive Design** - Works seamlessly on different screen sizes

### Permission-Based Filtering

Different users see different menu items based on their roles:

- **alice** (inventory_manager): Sees all inventory menu items
- **bob** (stock_viewer): Sees only Products, Categories, and basic views
- **charlie** (warehouse_manager): Sees Products, Categories, Warehouse, and Reports

### Technical Details

The menu system:
- Fetches menu data from microservices via API
- Caches the menu for 5 minutes in Redis for performance
- Filters items based on user permissions
- Renders using Django template tags
- Uses CSS for styling and JavaScript for interactivity

### Troubleshooting

If you don't see the nested menus:
1. Make sure you're logged in
2. Click on the parent menu items to expand them
3. Check that JavaScript is enabled in your browser
4. Try refreshing the page (Ctrl+F5)

The menu is working correctly - it just starts in a collapsed state for a cleaner initial view!