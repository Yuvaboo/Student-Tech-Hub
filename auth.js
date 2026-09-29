/**
 * MURUGAN IMPEX — DENTAL PLATFORM & KNOWLEDGE HUB
 * auth.js — Shared Auth, Profile, Realtime & Utility Module
 *
 * Load order (in every HTML page):
 *   1. <script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
 *   2. <script src="supabase-config.js"></script>
 *   3. <script src="auth.js"></script>
 *
 * All functions attach to window.Auth.*
 * Uses window.supabaseClient (single shared client instance).
 */

(function () {
  'use strict';

  function getClient() {
    return window.supabaseClient;
  }

  var _currentUser = null;
  var _currentProfile = null;

  // ─── GET CURRENT USER ───────────────────────────────────────────────────
  async function getCurrentUser() {
    var db = getClient();
    if (!db) {
      console.error('[auth] Supabase client not found on window.supabaseClient');
      return null;
    }
    try {
      var result = await db.auth.getSession();
      _currentUser = (result.data && result.data.session) ? result.data.session.user : null;
    } catch (err) {
      console.error('[auth] getSession error:', err.message);
      _currentUser = null;
    }
    return _currentUser;
  }

  // ─── GET CURRENT PROFILE ────────────────────────────────────────────────
  async function getCurrentProfile(forceRefresh) {
    if (_currentProfile && !forceRefresh) return _currentProfile;
    var user = await getCurrentUser();
    if (!user) return null;

    var db = getClient();
    var meta = user.user_metadata || {};
    
    // Default fallback profile based on auth user
    var fallbackProfile = {
      id: user.id,
      email: user.email || '',
      full_name: meta.full_name || meta.name || (user.email ? user.email.split('@')[0] : 'Doctor'),
      phone: meta.phone || '',
      clinic_name: meta.clinic_name || '',
      dci_number: meta.dci_number || '',
      gstin: meta.gstin || '',
      address: meta.address || '',
      city: meta.city || '',
      state: meta.state || '',
      pincode: meta.pincode || '',
      role: (['admin@muruganimpex.in', 'yuvas@muruganimpex.in'].includes(user.email)) ? 'admin' : (meta.role || 'free'),
      avatar_url: meta.avatar_url || ''
    };

    try {
      var resp = await db.from('profiles').select('*').eq('id', user.id).maybeSingle();
      if (resp.error) {
        console.warn('[auth] Note on profile table query:', resp.error.message);
        _currentProfile = fallbackProfile;
      } else if (resp.data) {
        _currentProfile = Object.assign({}, fallbackProfile, resp.data);
      } else {
        _currentProfile = fallbackProfile;
      }
    } catch (e) {
      console.warn('[auth] Using fallback auth metadata profile:', e.message);
      _currentProfile = fallbackProfile;
    }

    return _currentProfile;
  }

  // ─── SIGN UP ────────────────────────────────────────────────────────────
  async function signUpWithEmail(email, password, meta) {
    meta = meta || {};
    var db = getClient();
    if (!db) return { user: null, error: new Error('Supabase client not initialized.') };

    var cleanEmail = email.trim().toLowerCase();
    var defaultRole = (['admin@muruganimpex.in', 'yuvas@muruganimpex.in'].includes(cleanEmail)) ? 'admin' : 'free';

    var resp = await db.auth.signUp({
      email: cleanEmail,
      password: password,
      options: {
        data: {
          full_name: meta.full_name || '',
          phone: meta.phone || '',
          clinic_name: meta.clinic_name || '',
          dci_number: meta.dci_number || '',
          gstin: meta.gstin || '',
          address: meta.address || '',
          city: meta.city || '',
          state: meta.state || '',
          pincode: meta.pincode || '',
          role: defaultRole
        }
      }
    });

    if (resp.error) {
      console.error('[auth] SignUp error:', resp.error.message);
      return { user: null, error: resp.error };
    }

    // Try updating profile in table if table exists
    if (resp.data.user) {
      try {
        await db.from('profiles').upsert({
          id: resp.data.user.id,
          full_name: meta.full_name || cleanEmail.split('@')[0],
          created_at: new Date().toISOString()
        }, { onConflict: 'id' });
      } catch (e) {
        // Table might have custom schema, non-blocking
      }
    }

    return { user: resp.data.user, error: null };
  }

  // ─── SIGN IN ────────────────────────────────────────────────────────────
  async function signInWithEmail(email, password) {
    var db = getClient();
    if (!db) return { user: null, profile: null, error: new Error('Supabase client not initialized.') };

    var cleanEmail = email.trim().toLowerCase();
    var resp = await db.auth.signInWithPassword({
      email: cleanEmail,
      password: password
    });

    if (resp.error) {
      console.error('[auth] SignIn error:', resp.error.message);
      return { user: null, profile: null, error: resp.error };
    }

    _currentUser = resp.data.user;
    _currentProfile = null;
    var profile = await getCurrentProfile(true);
    return { user: resp.data.user, profile: profile, error: null };
  }

  // ─── GOOGLE OAUTH ───────────────────────────────────────────────────────
  async function signInWithGoogle() {
    var db = getClient();
    if (!db) { showToast('Supabase not configured.', 'error'); return; }

    var resp = await db.auth.signInWithOAuth({
      provider: 'google',
      options: {
        redirectTo: window.location.origin + '/dashboard.html',
        queryParams: { access_type: 'offline', prompt: 'consent' }
      }
    });

    if (resp.error) {
      console.error('[auth] Google OAuth error:', resp.error.message);
      showToast('Google sign-in error: ' + resp.error.message, 'error');
    }
  }

  // ─── SIGN OUT ───────────────────────────────────────────────────────────
  async function signOut() {
    var db = getClient();
    if (db) {
      try { await db.auth.signOut(); } catch (e) { console.warn(e); }
    }
    _currentUser = null;
    _currentProfile = null;
    window.location.href = 'login.html';
  }

  // ─── ROUTE GUARDS ───────────────────────────────────────────────────────
  async function requireAuth(redirectPath) {
    redirectPath = redirectPath || 'login.html';
    var user = await getCurrentUser();
    if (!user) {
      window.location.href = redirectPath;
      return null;
    }
    return await getCurrentProfile();
  }

  async function requirePremium(redirectPath) {
    redirectPath = redirectPath || 'pricing.html';
    var profile = await requireAuth();
    if (!profile) return null;
    if (profile.role === 'premium' || profile.role === 'admin') return profile;

    var db = getClient();
    try {
      var resp = await db.from('subscriptions').select('id')
        .eq('user_id', profile.id).eq('status', 'active').maybeSingle();
      if (resp.data) return profile;
    } catch (e) {}

    showToast('Premium fellowship subscription required.', 'warning');
    window.location.href = redirectPath;
    return null;
  }

  async function requireAdminAccess(redirectPath) {
    redirectPath = redirectPath || 'index.html';
    var profile = await requireAuth();
    if (!profile) return null;
    if (profile.role !== 'admin') {
      showToast('Administrator access required.', 'error');
      window.location.href = redirectPath;
      return null;
    }
    return profile;
  }

  // ─── PROFILE UPDATE ─────────────────────────────────────────────────────
  async function updateProfile(fields) {
    var user = await getCurrentUser();
    if (!user) return { error: new Error('Not authenticated') };
    var db = getClient();

    // Update auth metadata
    try {
      await db.auth.updateUser({ data: fields });
    } catch (e) {
      console.warn('[auth] updateUser metadata failed:', e.message);
    }

    // Try updating table
    var resp = await db.from('profiles').update(fields).eq('id', user.id);
    _currentProfile = null;
    return { error: resp.error };
  }

  // ─── STORAGE HELPERS ───────────────────────────────────────────────────
  async function uploadAvatar(file) {
    var user = await getCurrentUser();
    if (!user) return { publicUrl: null, error: new Error('Not authenticated') };
    var db = getClient();
    var bucket = (window.APP_CONFIG && window.APP_CONFIG.storageBuckets) ? window.APP_CONFIG.storageBuckets.avatars : 'avatars';
    var ext = file.name.split('.').pop();
    var filePath = user.id + '/avatar.' + ext;
    var resp = await db.storage.from(bucket).upload(filePath, file, { upsert: true });
    if (resp.error) return { publicUrl: null, error: resp.error };
    var publicUrl = getPublicUrl(bucket, filePath);
    await updateProfile({ avatar_url: publicUrl });
    return { publicUrl: publicUrl, error: null };
  }

  function getPublicUrl(bucket, path) {
    var db = getClient();
    if (!db) return '';
    var resp = db.storage.from(bucket).getPublicUrl(path);
    return (resp.data && resp.data.publicUrl) ? resp.data.publicUrl : '';
  }

  // ─── AUTH STATE CHANGE ─────────────────────────────────────────────────
  function onAuthStateChange(callback) {
    var db = getClient();
    if (!db) return function () {};
    var resp = db.auth.onAuthStateChange(function (event, session) {
      _currentUser = (session) ? session.user : null;
      _currentProfile = null;
      if (typeof callback === 'function') callback(event, session);
    });
    return function () {
      if (resp && resp.data && resp.data.subscription) {
        resp.data.subscription.unsubscribe();
      }
    };
  }

  // ─── REALTIME HELPERS ──────────────────────────────────────────────────
  function subscribeToTable(table, onInsert, filter) {
    var db = getClient();
    if (!db) return null;
    var opts = { event: 'INSERT', schema: 'public', table: table };
    if (filter) opts.filter = filter.column + '=eq.' + filter.value;
    var channel = db.channel('realtime:' + table + ':' + Date.now())
      .on('postgres_changes', opts, function (payload) { onInsert(payload.new); });
    channel.subscribe();
    return channel;
  }

  function subscribeToUpdates(table, onUpdate, filter) {
    var db = getClient();
    if (!db) return null;
    var opts = { event: 'UPDATE', schema: 'public', table: table };
    if (filter) opts.filter = filter.column + '=eq.' + filter.value;
    var channel = db.channel('realtime:updates:' + table + ':' + Date.now())
      .on('postgres_changes', opts, function (payload) { onUpdate(payload.new); });
    channel.subscribe();
    return channel;
  }

  // ─── UTILITY FUNCTIONS ─────────────────────────────────────────────────
  function formatCurrency(amount) {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency', currency: 'INR',
      minimumFractionDigits: 0, maximumFractionDigits: 2
    }).format(amount || 0);
  }

  function formatDate(iso) {
    if (!iso) return '';
    try {
      return new Date(iso).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
    } catch (e) {
      return iso;
    }
  }

  function showToast(message, type, duration) {
    type = type || 'info';
    duration = (duration !== undefined) ? duration : 4000;
    var container = document.getElementById('toast-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'toast-container';
      container.style.cssText = 'position:fixed;top:20px;right:20px;z-index:99999;display:flex;flex-direction:column;gap:8px;pointer-events:none;';
      document.body.appendChild(container);
    }
    var colors = { success: '#10b981', error: '#ef4444', warning: '#f59e0b', info: '#00a896' };
    var icons  = { success: '✓', error: '✕', warning: '⚠', info: 'ℹ' };
    var color = colors[type] || colors.info;
    var icon  = icons[type]  || icons.info;
    var toast = document.createElement('div');
    toast.style.cssText = 'background:#0f2b48;color:#f1f5f9;border-left:4px solid ' + color + ';border-radius:8px;padding:12px 16px;font-size:14px;font-family:sans-serif;max-width:360px;box-shadow:0 8px 24px rgba(0,0,0,0.3);pointer-events:auto;cursor:pointer;display:flex;align-items:center;gap:10px;animation:toastSlideIn 0.3s ease;transition:opacity 0.3s;';
    toast.innerHTML = '<span style="color:' + color + ';font-weight:bold;font-size:16px">' + icon + '</span><span>' + message + '</span>';
    if (!document.getElementById('toast-keyframes')) {
      var s = document.createElement('style');
      s.id = 'toast-keyframes';
      s.textContent = '@keyframes toastSlideIn{from{transform:translateX(120%);opacity:0}to{transform:translateX(0);opacity:1}}';
      document.head.appendChild(s);
    }
    var dismiss = function () { toast.style.opacity = '0'; setTimeout(function () { toast.remove(); }, 300); };
    toast.addEventListener('click', dismiss);
    container.appendChild(toast);
    if (duration > 0) setTimeout(dismiss, duration);
  }

  function generateOrderReference() {
    var d = new Date().toISOString().slice(0, 10).replace(/-/g, '');
    return 'MI-' + d + '-' + Math.floor(10000 + Math.random() * 90000);
  }

  function generateInvoiceNumber() {
    var now = new Date();
    var fy = now.getMonth() >= 3
      ? now.getFullYear() + '-' + String(now.getFullYear() + 1).slice(-2)
      : (now.getFullYear() - 1) + '-' + String(now.getFullYear()).slice(-2);
    return 'INV/' + fy + '/' + Math.floor(10000 + Math.random() * 90000);
  }

  function calculateGST(subtotal) {
    var gst = parseFloat((subtotal * 0.18).toFixed(2));
    var half = parseFloat((gst / 2).toFixed(2));
    return { cgst: half, sgst: half, igst: gst, total: parseFloat((subtotal + gst).toFixed(2)) };
  }

  function generateAWB() {
    return 'BD' + Math.floor(100000000 + Math.random() * 900000000);
  }

  // ─── ATTACH TO WINDOW ──────────────────────────────────────────────────
  window.Auth = {
    getCurrentUser: getCurrentUser,
    getCurrentProfile: getCurrentProfile,
    signUpWithEmail: signUpWithEmail,
    signInWithEmail: signInWithEmail,
    signInWithGoogle: signInWithGoogle,
    signOut: signOut,
    requireAuth: requireAuth,
    requirePremium: requirePremium,
    requireAdminAccess: requireAdminAccess,
    updateProfile: updateProfile,
    uploadAvatar: uploadAvatar,
    getPublicUrl: getPublicUrl,
    onAuthStateChange: onAuthStateChange,
    subscribeToTable: subscribeToTable,
    subscribeToUpdates: subscribeToUpdates,
    formatCurrency: formatCurrency,
    formatDate: formatDate,
    showToast: showToast,
    generateOrderReference: generateOrderReference,
    generateInvoiceNumber: generateInvoiceNumber,
    calculateGST: calculateGST,
    generateAWB: generateAWB
  };

  console.log('[auth] Module ready on window.Auth');
})();
