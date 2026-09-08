/**
 * Milliy Sertifikat Bot - WebApp API Konfiguratsiyasi
 * Backend API Base URL Resolver & O'z-o'zini tiklovchi Fetcher
 */

// Faol Cloudflare Tunnel yoki Server manzili
let DEFAULT_API_BASE = "https://fifth-alien-engaging-anderson.trycloudflare.com";

/**
 * Backend API URL manzilini aniqlash:
 * 1. URL dagi ?api= parametri (Telegram bot havolasidan olingan)
 * 2. GitHub Pages bo'lsa, avtomatik DEFAULT_API_BASE
 * 3. Brauzer localStorage keshidagi manzil (faqat mos kelsa)
 * 4. Lokal origin
 */
function getApiBaseUrl() {
  try {
    const urlParams = new URLSearchParams(window.location.search);
    const queryApi = urlParams.get('api');
    if (queryApi) {
      const clean = queryApi.replace(/\/+$/, '');
      localStorage.setItem('MS_API_BASE_URL', clean);
      return clean;
    }
    if (window.location.hostname.includes('github.io')) {
      return DEFAULT_API_BASE;
    }
    const saved = localStorage.getItem('MS_API_BASE_URL');
    if (saved && !saved.includes('localhost') && !saved.includes('trycloudflare.com')) {
      return saved;
    }
  } catch (e) {
    console.warn("Storage/URL access warning:", e);
  }
  return DEFAULT_API_BASE;
}

let API_BASE = getApiBaseUrl();

/**
 * Avtomatik qayta urinish va o'z-o'zini tiklovchi API so'rov funksiyasi.
 * Agar joriy API_BASE ishlamasa (eski tunnel bo'lsa), avtomatik DEFAULT_API_BASE ga fallback qiladi.
 */
async function apiFetch(path, options = {}) {
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  let targetBase = API_BASE;
  try {
    const res = await fetch(`${targetBase}${cleanPath}`, options);
    return res;
  } catch (err) {
    if (DEFAULT_API_BASE && targetBase !== DEFAULT_API_BASE) {
      console.warn("[API] Ulanish xatosi! DEFAULT_API_BASE ga o'tilmoqda:", DEFAULT_API_BASE);
      try {
        const fallbackRes = await fetch(`${DEFAULT_API_BASE}${cleanPath}`, options);
        API_BASE = DEFAULT_API_BASE;
        try {
          localStorage.setItem('MS_API_BASE_URL', DEFAULT_API_BASE);
        } catch (e) {}
        return fallbackRes;
      } catch (fallbackErr) {
        console.error("[API] Fallback ham ulanmadi:", fallbackErr);
      }
    }
    throw err;
  }
}
