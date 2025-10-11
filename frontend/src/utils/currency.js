/**
 * Currency formatting utilities
 */

const CURRENCY_SYMBOLS = {
  USD: '$',
  EUR: '€',
  GBP: '£',
  JPY: '¥',
  CNY: '¥',
  AUD: 'A$',
  CAD: 'C$',
  CHF: 'CHF',
  INR: '₹',
  RUB: '₽',
  BRL: 'R$',
  KRW: '₩',
  TRY: '₺',
  MXN: 'MX$',
  SEK: 'kr',
  NOK: 'kr',
  DKK: 'kr',
  PLN: 'zł',
  THB: '฿',
  IDR: 'Rp',
  MYR: 'RM',
  PHP: '₱',
  SGD: 'S$',
  HKD: 'HK$',
  NZD: 'NZ$',
  ZAR: 'R'
}

/**
 * Format amount with currency symbol
 * @param {number} amount - The amount to format
 * @param {string} currency - Currency code (e.g., 'USD', 'EUR')
 * @param {object} options - Formatting options
 * @returns {string} Formatted currency string
 */
export function formatCurrency(amount, currency = 'USD', options = {}) {
  const {
    decimals = 2,
    showSymbol = true,
    showCode = false,
    locale = 'en-US'
  } = options

  if (amount === null || amount === undefined || isNaN(amount)) {
    return '-'
  }

  const numAmount = Number(amount)
  
  // Use Intl.NumberFormat for proper locale-aware formatting
  const formatter = new Intl.NumberFormat(locale, {
    style: showSymbol ? 'currency' : 'decimal',
    currency: currency || 'USD',
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  })

  let formatted = formatter.format(numAmount)

  // Optionally append currency code
  if (showCode && currency) {
    formatted += ` ${currency}`
  }

  return formatted
}

/**
 * Get currency symbol for a currency code
 * @param {string} currency - Currency code
 * @returns {string} Currency symbol
 */
export function getCurrencySymbol(currency) {
  return CURRENCY_SYMBOLS[currency] || currency
}

/**
 * Parse currency string to number
 * @param {string} str - Currency string
 * @returns {number} Parsed amount
 */
export function parseCurrency(str) {
  if (typeof str === 'number') return str
  if (!str) return 0
  
  // Remove currency symbols, commas, and spaces
  const cleaned = str.replace(/[^0-9.-]/g, '')
  return parseFloat(cleaned) || 0
}

/**
 * Format amount for compact display (K, M, B)
 * @param {number} amount - The amount to format
 * @param {string} currency - Currency code
 * @returns {string} Formatted compact string
 */
export function formatCompactCurrency(amount, currency = 'USD') {
  if (amount === null || amount === undefined || isNaN(amount)) {
    return '-'
  }

  const numAmount = Math.abs(Number(amount))
  const symbol = getCurrencySymbol(currency)
  const sign = amount < 0 ? '-' : ''

  if (numAmount >= 1e9) {
    return `${sign}${symbol}${(numAmount / 1e9).toFixed(1)}B`
  } else if (numAmount >= 1e6) {
    return `${sign}${symbol}${(numAmount / 1e6).toFixed(1)}M`
  } else if (numAmount >= 1e3) {
    return `${sign}${symbol}${(numAmount / 1e3).toFixed(1)}K`
  } else {
    return `${sign}${symbol}${numAmount.toFixed(2)}`
  }
}

