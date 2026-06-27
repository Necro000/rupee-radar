/**
 * Currency and number formatting utilities for RupeeRadar.
 * UI-11: Consistent Indian rupee formatting across all views.
 */

/**
 * Format a number as Indian Rupees with proper comma grouping.
 * e.g. 123456.78 → '₹1,23,456.78'
 */
export function formatINR(amount: number | null | undefined): string {
  if (amount == null || isNaN(amount)) return '₹0';
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(amount);
}

/**
 * Format a number as a short Indian Rupee amount (no paise for large values).
 * e.g. 123456 → '₹1,23,456'
 */
export function formatINRShort(amount: number | null | undefined): string {
  if (amount == null || isNaN(amount)) return '₹0';
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount);
}

/**
 * Format a percentage with 1 decimal place.
 * e.g. 24.5 → '24.5%'
 */
export function formatPercent(value: number | null | undefined): string {
  if (value == null || isNaN(value)) return '0%';
  return `${Math.abs(value).toFixed(1)}%`;
}

/**
 * Format a YYYY-MM date string to a human-readable month.
 * e.g. '2025-03' → 'Mar 2025'
 */
export function formatMonth(monthStr: string): string {
  if (!monthStr || monthStr === 'Unknown') return monthStr;
  try {
    const [year, month] = monthStr.split('-');
    const date = new Date(parseInt(year), parseInt(month) - 1, 1);
    return date.toLocaleDateString('en-IN', { month: 'short', year: 'numeric' });
  } catch {
    return monthStr;
  }
}

/**
 * Format an ISO date string to a human-readable date.
 * e.g. '2025-01-15' → '15 Jan 2025'
 */
export function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return '-';
  try {
    const [year, month, day] = dateStr.split('-');
    const date = new Date(parseInt(year), parseInt(month) - 1, parseInt(day));
    return date.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
  } catch {
    return dateStr;
  }
}
