# How to Configure Currency Display in Reports

## What I Fixed

1. **Currency field detection** - Now detects fields with "$" symbols, not just "USD" codes
2. **Symbol-to-code mapping** - Automatically converts "$" → "USD", "€" → "EUR", etc.
3. **Fallback field detection** - FloatingToolbar now shows currency fields even if backend detection didn't catch them
4. **Backend symbol handling** - Currency grouping now works with symbols

## How to Configure Currency on Your Widgets

### Step 1: Enter Edit Mode
1. Click the **"Edit Mode"** button in the top toolbar
2. Your widgets will become editable

### Step 2: Select a Widget
1. Click on any **Chart** or **Stats** widget you want to configure
2. The widget will get a blue ring around it
3. The FloatingToolbar on the left will switch to show configuration options

### Step 3: Configure Currency Settings

Scroll down in the FloatingToolbar until you see the **"Currency Settings"** section.

#### Option A: Use Fixed Currency (Recommended for your case)
1. **Currency Mode**: Select "Fixed Currency"
2. **Currency Code**: Enter `USD` (or the code for your currency)
3. Click anywhere outside the input - changes auto-save
4. The chart/stat will now show currency formatting

#### Option B: Use Currency from Data Field
1. **Currency Mode**: Select "From Data Field"
2. **Currency Field**: Select `computed_currency` from the dropdown
3. Your field should now appear in the list!
4. Optional: Check "Group by currency" to split data by different currencies
5. Changes auto-save automatically

### Step 4: Repeat for All Widgets
- Click on each chart/stat widget you want to format with currency
- Configure the currency settings as above
- Each widget remembers its own currency configuration

## Troubleshooting

### "I don't see computed_currency in the dropdown"
**Solution:** 
- Refresh the page to reload metadata
- The fallback detection should now show it automatically
- If still not visible, you can use "Fixed Currency" mode instead

### "Currency symbols not showing"
**Solution:**
- Make sure you've selected the widget and configured Currency Mode
- Default is "None" - you must explicitly enable it
- Use "Fixed Currency" with code "USD" for $ symbol

### "Numbers still showing without symbols"
**Checklist:**
1. ✓ Is the widget selected (blue ring)?
2. ✓ Have you set Currency Mode to "Fixed Currency" or "From Data Field"?
3. ✓ Have you entered a currency code or selected a currency field?
4. ✓ Did you click outside the input to trigger auto-save?
5. ✓ Try clicking "Refresh Data" button to reload the widget

## Quick Example

For a chart showing spending by category with USD currency:

1. **Edit Mode** → ON
2. **Click** the chart widget
3. **FloatingToolbar** → Scroll to "Currency Settings"
4. **Currency Mode** → "Fixed Currency"
5. **Currency Code** → Type `USD`
6. **Done!** Chart should now show $1,234.56 format

## Supported Currency Codes

Common codes you can use in "Fixed Currency" mode:
- USD - US Dollar ($)
- EUR - Euro (€)
- GBP - British Pound (£)
- JPY - Japanese Yen (¥)
- CAD - Canadian Dollar
- AUD - Australian Dollar
- CHF - Swiss Franc
- INR - Indian Rupee (₹)

And 20+ more currencies supported!

## Notes

- **Stats widgets**: Show single total with currency symbol
- **Chart widgets**: Format axis labels and tooltips with currency
- **Grouping**: When using "From Data Field" + "Group by currency", charts will show separate bars/lines for each currency
- **Auto-save**: All changes save automatically after 1 second
- **Lock Mode**: Exit edit mode to see final result without edit controls

