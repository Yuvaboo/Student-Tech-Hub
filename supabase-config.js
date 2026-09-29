/**
 * MURUGAN IMPEX — KNOWLEDGE HUB & CLINICAL PLATFORM
 * Supabase + Stripe Configuration
 *
 * IMPORTANT: This file must be loaded AFTER the Supabase CDN script:
 *   <script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
 *   <script src="supabase-config.js"></script>
 *
 * Uses window.supabase.createClient() — no ES module imports.
 * Service-role keys and payment secrets are strictly kept server-side.
 */

(function () {
  'use strict';

  // ─── SUPABASE CREDENTIALS ────────────────────────────────────────────────
  var SUPABASE_URL  = 'https://zvlqhrsiojkptpnewqfm.supabase.co';
  var SUPABASE_ANON = 'sb_publishable_HZ_CwTl7T_mAXa9s9EmX0Q_r9uWUH0K';

  // Allow runtime override via localStorage
  var storedUrl  = localStorage.getItem('ENV_SUPABASE_URL');
  var storedAnon = localStorage.getItem('ENV_SUPABASE_ANON_KEY');
  if (storedUrl)  SUPABASE_URL  = storedUrl;
  if (storedAnon) SUPABASE_ANON = storedAnon;

  // ─── VALIDATE CDN ────────────────────────────────────────────────────────
  if (typeof window.supabase === 'undefined' || typeof window.supabase.createClient !== 'function') {
    console.error('[supabase-config] FATAL: Supabase JS library not loaded. Add this BEFORE supabase-config.js:\n  <script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>');
    return;
  }

  // ─── CREATE CLIENT ────────────────────────────────────────────────────────
  var client = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON, {
    auth: {
      persistSession: true,
      autoRefreshToken: true,
      detectSessionInUrl: true,
      storage: window.localStorage
    },
    realtime: {
      params: { eventsPerSecond: 10 }
    }
  });

  console.log('[supabase-config] Client created for:', SUPABASE_URL);

  // ─── CONNECTION TEST ──────────────────────────────────────────────────────
  // Quick test to confirm we can reach Supabase (non-blocking)
  client.auth.getSession().then(function (result) {
    if (result.error) {
      console.warn('[supabase-config] Auth test returned error:', result.error.message);
    } else {
      console.log('[supabase-config] ✓ Supabase connected. Session:', result.data.session ? 'active' : 'none');
    }
  }).catch(function (err) {
    console.error('[supabase-config] ✕ Connection FAILED:', err.message);
  });

  // ─── EXPORT CONFIG TO WINDOW ──────────────────────────────────────────────
  window.SUPABASE_CONFIG = {
    url: SUPABASE_URL,
    anonKey: SUPABASE_ANON
  };

  // The single Supabase client instance used across all pages
  window.supabaseClient = client;

  // Helper: check if we have real credentials (not placeholder)
  window.isSupabaseConfigured = function () {
    return SUPABASE_URL && !SUPABASE_URL.includes('placeholder') &&
           SUPABASE_ANON && !SUPABASE_ANON.includes('placeholder');
  };

  // Helper: dynamically swap credentials (reloads page)
  window.configureSupabaseCredentials = function (url, anonKey) {
    if (!url || !anonKey) return false;
    localStorage.setItem('ENV_SUPABASE_URL', url.trim());
    localStorage.setItem('ENV_SUPABASE_ANON_KEY', anonKey.trim());
    window.location.reload();
    return true;
  };

  // ─── STRIPE & PAYMENT CONFIG ──────────────────────────────────────────────
  window.STRIPE_CONFIG = {
    publishableKey: 'pk_test_51PLACEHOLDER_KEY',
    prices: {
      monthly: 'price_monthly_1499',
      annual: 'price_annual_12999'
    }
  };

  // ─── APPLICATION SETTINGS ─────────────────────────────────────────────────
  window.APP_CONFIG = {
    name: 'Murugan Impex Knowledge Hub',
    tagline: 'Premium Dental Education & Clinical Guides',
    currency: 'INR',
    symbol: '₹',
    monthlyPrice: 1499,
    annualPrice: 12999,
    annualSaving: 'Save ₹5,989/year',
    supportEmail: 'support@muruganimpex.in',
    whatsapp: '+918008008008',
    adminEmails: ['admin@muruganimpex.in', 'yuvas@muruganimpex.in'],

    storageBuckets: {
      clinicalFiles: 'clinical-files',
      contentMedia: 'content-media',
      avatars: 'avatars',
      invoices: 'invoices'
    },

    tables: {
      profiles: 'profiles',
      subscriptions: 'subscriptions',
      payments: 'payments',
      premiumContent: 'premium_content',
      orders: 'orders',
      orderItems: 'order_items',
      comments: 'comments',
      chatMessages: 'chat_messages',
      files: 'files'
    }
  };

})();
