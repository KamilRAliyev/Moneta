# URGENT: Get Currency Showing RIGHT NOW

## The Simplest Solution (30 seconds per widget)

Your widgets are configured correctly, but need to be **toggled** to apply formatting.

### Do This For Each Widget:

1. **Click "Edit Mode"** (top right)
2. **Click the "Refresh Data" button** (next to date picker)
3. **Done!** Check if $ appears

If that doesn't work:

1. **Click Edit Mode**
2. **Click widget** (gets blue ring)
3. **In FloatingToolbar**, change:
   - Currency Mode: **"From Data Field"** → **"Fixed Currency"**
   - Currency Code: Type **"USD"**
4. **Click another widget or press ESC**
5. **Repeat for all money widgets**

## Why It's Not Showing

The widgets were saved with currency config **before** I added the auto-USD defaulting code. You need to either:
- Refresh the data (triggers new fetch with new code)
- OR change the config (triggers update)

## Test After Refreshing

1. Open Console (F12)
2. Click "Refresh Data" button
3. Look for: `💰 Using field mode, defaulting to USD`
4. If you see that, charts should show $

## If Still Not Working

**Switch ALL widgets to Fixed Currency mode:**

It's simpler and more reliable:

1. Edit Mode ON
2. For each chart/stat:
   - Click it
   - Currency Mode → "Fixed Currency (Recommended)"
   - Currency Code → "USD"
3. Done!

This bypasses the field detection entirely and just applies USD formatting directly.

## Console Check

After refresh, you should see in console:
```
🔥 ChartWidget MOUNTED with dateRange: ...
🔥 ChartWidget currency config: {currency_mode: "field", currency_field: "computed_currency", currency_code: null}
📊 ChartWidget fetching data...
💰 Using field mode, defaulting to USD (field: computed_currency)
📊 Single series data with currency: USD
```

If you see `currency: USD` in the last line, the currency IS being set. The issue would then be in the chart rendering.

## Nuclear Option: Start Fresh

If nothing works:

1. Click each widget
2. Currency Mode → "none"
3. Save (click away)
4. Click widget again
5. Currency Mode → "Fixed Currency"
6. Currency Code → "USD"
7. Save

This completely resets the currency config.

