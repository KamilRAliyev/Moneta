# Currency Debugging Guide

## Quick Fix Applied ✅

I've added:
1. **Console logging** to see what currency fields are detected
2. **Better UI feedback** showing currency field count
3. **Helpful tips** in the UI when no fields detected
4. **"Recommended" label** on Fixed Currency mode

## How to Test

### Step 1: Open Browser Console
1. Open your app: http://localhost:5173/reports
2. Press `F12` or `Cmd+Option+I` (Mac) to open DevTools
3. Go to the **Console** tab

### Step 2: Enter Edit Mode & Select a Widget
1. Click **"Edit Mode"** button
2. Click on any **Chart** or **Stats** widget
3. Look in the console for messages like:
   ```
   💰 FloatingToolbar: Computing currency fields
     - metadata.currency_fields: [...]
     - metadata.ingested_columns: [...]
     - metadata.computed_columns: [...]
   ```

### Step 3: Check What You See

#### Scenario A: Backend Detected Currency Fields ✅
Console shows:
```
✅ Using backend currency_fields: ["computed_currency"]
```

UI shows:
```
Currency Field dropdown: computed_currency
✓ Found 1 currency field(s)
```

**Action:** Select `computed_currency` from dropdown

#### Scenario B: Fallback Detection Working ⚠️
Console shows:
```
⚠️ Using fallback detection, found: ["computed_currency"]
```

UI shows:
```
Currency Field dropdown: computed_currency
✓ Found 1 currency field(s)
```

**Action:** Select `computed_currency` from dropdown

#### Scenario C: No Detection 😔
Console shows:
```
⚠️ Using fallback detection, found: []
```

UI shows:
```
No currency fields detected
💡 Tip: Use "Fixed Currency" mode instead
```

**Action:** 
1. Change Currency Mode to **"Fixed Currency (Recommended)"**
2. Enter **USD** in the Currency Code field
3. Done! Charts will show $1,234.56 format

## Recommended Solution (Easiest)

**Just use Fixed Currency mode:**

1. Edit Mode → ON
2. Click widget
3. Scroll to "Currency Settings"
4. Currency Mode → **"Fixed Currency (Recommended)"**
5. Currency Code → **USD**
6. Done!

This bypasses any detection issues and works immediately.

## If You Want to Use "From Data Field"

### Check Backend Detection

Open terminal and run:
```bash
curl http://localhost:8888/api/transactions/metadata
```

Look for:
```json
{
  "ingested_columns": {...},
  "computed_columns": {...},
  "currency_fields": ["computed_currency"],  // <-- Should see this
  ...
}
```

If `currency_fields` is empty `[]`, the backend didn't detect it.

### Force Backend Detection

Your field is `computed_currency` with value `"$"`. 

The backend should detect it now with our improvements, but if not:

**Option 1: Refresh the page** to reload metadata

**Option 2: Check your transactions have the field**
```bash
curl http://localhost:8888/api/transactions/?limit=1
```

Should see:
```json
{
  "transactions": [
    {
      "computed_content": {
        "computed_currency": "$",
        ...
      }
    }
  ]
}
```

## Common Issues

### Issue: "I selected the field but nothing changed"
**Solution:** 
- Make sure you clicked outside the input (to trigger auto-save)
- Or click "Refresh Data" button
- Check console for API errors

### Issue: "Currency field not in dropdown"
**Solution:**
1. Check console logs - what does it say?
2. Try refreshing the page
3. Use "Fixed Currency" mode instead (recommended)

### Issue: "Dropdown shows field but no formatting"
**Solution:**
- Your data might have "$" but the formatter needs "USD"
- Use "Fixed Currency" mode with "USD" instead

## Test Complete Flow

1. ✅ Backend detects `computed_currency` 
2. ✅ FloatingToolbar shows it in dropdown
3. ✅ Select currency field
4. ✅ Charts format with $ symbol
5. ✅ Stats format with $ symbol

OR simpler:

1. ✅ Use "Fixed Currency" mode
2. ✅ Enter "USD"
3. ✅ See $ symbols everywhere

## What the Console Logs Tell You

| Log Message | Meaning | What To Do |
|------------|---------|------------|
| `✅ Using backend currency_fields: ["computed_currency"]` | Perfect! Backend detected it | Use "From Data Field" mode |
| `⚠️ Using fallback detection, found: ["computed_currency"]` | Frontend fallback working | Use "From Data Field" mode |
| `⚠️ Using fallback detection, found: []` | Not detected anywhere | Use "Fixed Currency" mode |
| No logs at all | Metadata not loaded | Refresh page |

## Need More Help?

Share the console output and I can tell you exactly what's happening!

