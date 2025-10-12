/**
 * Currency formatting utilities
 */

// Symbol to code mapping (for when data contains symbols instead of codes)
const SYMBOL_TO_CODE = {
  '$': 'USD',
  '€': 'EUR',
  '£': 'GBP',
  '¥': 'JPY',
  '₹': 'INR',
  '₽': 'RUB',
  'R$': 'BRL',
  '₩': 'KRW',
  'kr': 'NOK',
  'zł': 'PLN',
  '฿': 'THB',
  'Rp': 'IDR',
  'RM': 'MYR',
  '₱': 'PHP',
  'R': 'ZAR',
  '₺': 'TRY'
}

// Currency symbol mapping
const CURRENCY_SYMBOLS = {
  USD: '$',
  EUR: '€',
  GBP: '£',
  JPY: '¥',
  CNY: '¥',
  CHF: 'CHF',
  CAD: 'CA$',
  AUD: 'A$',
  INR: '₹',
  RUB: '₽',
  BRL: 'R$',
  KRW: '₩',
  MXN: 'MX$',
  SGD: 'S$',
  HKD: 'HK$',
  NOK: 'kr',
  SEK: 'kr',
  DKK: 'kr',
  PLN: 'zł',
  THB: '฿',
  IDR: 'Rp',
  MYR: 'RM',
  PHP: '₱',
  ZAR: 'R',
  TRY: '₺',
  NZD: 'NZ$'
}

// Currencies that don't show decimals
const NO_DECIMAL_CURRENCIES = new Set(['JPY', 'KRW', 'VND', 'IDR'])

/**
 * Format a number value with currency symbol
 * @param {number} value - The numeric value to format
 * @param {string} currencyCode - The ISO currency code (e.g., 'USD', 'EUR')
 * @param {object} options - Additional formatting options
 * @returns {string} Formatted currency string
 */
export function formatCurrency(value, currencyCode, options = {}) {
  // Handle null/undefined values
  if (value === null || value === undefined || isNaN(value)) {
    return '-'
  }

  // Convert symbol to code if necessary
  let code = currencyCode || ''
  if (SYMBOL_TO_CODE[code]) {
    code = SYMBOL_TO_CODE[code]
  } else {
    code = code.toUpperCase()
  }
  
  // Default options
  const {
    showSymbol = true,
    showCode = false,
    locale = 'en-US',
    compact = false
  } = options

  // Check if value is negative (for parentheses formatting)
  const isNegative = value < 0
  const absValue = Math.abs(value)

  // Determine decimal places
  const decimals = NO_DECIMAL_CURRENCIES.has(code) ? 0 : 2

  // Format the absolute value
  let formatted
  if (compact && absValue >= 1000) {
    // Compact notation for large numbers
    formatted = new Intl.NumberFormat(locale, {
      notation: 'compact',
      maximumFractionDigits: 1
    }).format(absValue)
  } else {
    formatted = new Intl.NumberFormat(locale, {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals
    }).format(absValue)
  }

  // Get currency symbol
  const symbol = CURRENCY_SYMBOLS[code] || code

  // Build result
  let result
  if (!showSymbol && !showCode) {
    result = formatted
  } else if (showCode) {
    result = `${formatted} ${code}`
  } else {
    // Symbol placement (most currencies prefix, some suffix)
    const suffixCurrencies = new Set(['NOK', 'SEK', 'DKK', 'PLN'])
    if (suffixCurrencies.has(code)) {
      result = `${formatted} ${symbol}`
    } else {
      result = `${symbol}${formatted}`
    }
  }

  // Wrap in parentheses if negative (financial reporting style)
  return isNegative ? `(${result})` : result
}

/**
 * Get the currency symbol for a given currency code
 * @param {string} currencyCode - The ISO currency code
 * @returns {string} The currency symbol
 */
export function getCurrencySymbol(currencyCode) {
  const code = (currencyCode || '').toUpperCase()
  return CURRENCY_SYMBOLS[code] || code
}

/**
 * Parse currency string back to number
 * @param {string} currencyString - Currency formatted string
 * @returns {number|null} Parsed number or null if invalid
 */
export function parseCurrency(currencyString) {
  if (!currencyString || typeof currencyString !== 'string') {
    return null
  }

  // Remove currency symbols and letters
  const cleaned = currencyString.replace(/[^0-9.,\-]/g, '')
  
  // Handle different decimal separators
  const normalized = cleaned.replace(/,/g, '')
  
  const parsed = parseFloat(normalized)
  return isNaN(parsed) ? null : parsed
}

/**
 * Format currency for chart axis labels (shorter format)
 * @param {number} value - The numeric value to format
 * @param {string} currencyCode - The ISO currency code
 * @returns {string} Formatted currency string (compact)
 */
export function formatCurrencyCompact(value, currencyCode) {
  return formatCurrency(value, currencyCode, { compact: true })
}
