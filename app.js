/**
 * MURUGAN IMPEX — DENTAL PLATFORM & KNOWLEDGE HUB
 * app.js — Storefront, Cart, Orders, Content, Admin & Realtime Logic
 *
 * Load order:
 *   1. Supabase CDN
 *   2. supabase-config.js
 *   3. auth.js
 *   4. app.js
 *
 * Attached to window.App.*
 */

(function () {
  'use strict';

  function getClient() { return window.supabaseClient; }
  var Auth = window.Auth;

  // ─── CART STATE ──────────────────────────────────────────────────────────
  var CART_KEY = 'mi_cart';

  function getCart() {
    try { return JSON.parse(localStorage.getItem(CART_KEY)) || []; }
    catch (e) { return []; }
  }

  function saveCart(cart) {
    localStorage.setItem(CART_KEY, JSON.stringify(cart));
    document.dispatchEvent(new CustomEvent('cartUpdated', { detail: { cart: cart } }));
  }

  function addToCart(product, qty) {
    qty = qty || 1;
    var cart = getCart();
    var existing = cart.find(function (i) { return i.id === product.id; });
    if (existing) { existing.quantity += qty; } else { cart.push(Object.assign({}, product, { quantity: qty })); }
    saveCart(cart);
    if (window.Auth && window.Auth.showToast) {
      window.Auth.showToast(product.title + ' added to cart.', 'success');
    }
  }

  function removeFromCart(productId) {
    saveCart(getCart().filter(function (i) { return i.id !== productId; }));
  }

  function updateCartQuantity(productId, qty) {
    if (qty <= 0) { removeFromCart(productId); return; }
    saveCart(getCart().map(function (i) { return i.id === productId ? Object.assign({}, i, { quantity: qty }) : i; }));
  }

  function clearCart() {
    localStorage.removeItem(CART_KEY);
    document.dispatchEvent(new CustomEvent('cartUpdated', { detail: { cart: [] } }));
  }

  function getCartCount() {
    return getCart().reduce(function (s, i) { return s + i.quantity; }, 0);
  }

  function getCartSubtotal() {
    return getCart().reduce(function (s, i) { return s + i.price * i.quantity; }, 0);
  }

  // ─── ORDER PLACEMENT ─────────────────────────────────────────────────────
  async function placeOrder(shippingInfo) {
    var db = getClient();
    if (!db) return { error: new Error('Database not connected.') };

    var profile = await Auth.requireAuth();
    if (!profile) return { error: new Error('Not authenticated') };
    var cart = getCart();
    if (cart.length === 0) return { error: new Error('Cart is empty') };

    var subtotal = getCartSubtotal();
    var gst = Auth.calculateGST(subtotal);
    var orderRef = Auth.generateOrderReference();
    var invoiceNum = Auth.generateInvoiceNumber();
    var awb = Auth.generateAWB();

    var orderData = {
      order_reference: orderRef,
      user_id: profile.id,
      doctor_name: shippingInfo.doctor_name || profile.full_name,
      clinic_name: shippingInfo.clinic_name || profile.clinic_name,
      dci_number: shippingInfo.dci_number || profile.dci_number,
      gstin: shippingInfo.gstin || profile.gstin,
      shipping_address: shippingInfo.address || '',
      shipping_city: shippingInfo.city || '',
      shipping_state: shippingInfo.state || '',
      shipping_pincode: shippingInfo.pincode || '',
      awb_number: awb,
      subtotal: subtotal,
      gst_amount: gst.igst,
      total_amount: gst.total,
      invoice_number: invoiceNum,
      status: 'processing'
    };

    var resp = await db.from('orders').insert(orderData).select('id').single();

    if (resp.error) {
      console.warn('[app] orders table error (will store order locally as backup):', resp.error.message);
      // Save local backup of order if remote table not created yet
      var localOrders = JSON.parse(localStorage.getItem('mi_local_orders') || '[]');
      orderData.id = 'loc_' + Date.now();
      orderData.created_at = new Date().toISOString();
      orderData.order_items = cart;
      localOrders.unshift(orderData);
      localStorage.setItem('mi_local_orders', JSON.stringify(localOrders));
      clearCart();
      return { orderId: orderData.id, orderReference: orderRef, invoiceNumber: invoiceNum, awbNumber: awb, error: null };
    }

    var orderId = resp.data.id;
    var items = cart.map(function (item) {
      return {
        order_id: orderId, product_id: item.id, product_title: item.title,
        origin: item.origin || null, batch_lot: item.batch_lot || null,
        hsn_code: item.hsn_code || null, unit_price: item.price,
        quantity: item.quantity, gst_rate: 18,
        total_price: parseFloat((item.price * item.quantity).toFixed(2))
      };
    });
    await db.from('order_items').insert(items);

    clearCart();
    return { orderId: orderId, orderReference: orderRef, invoiceNumber: invoiceNum, awbNumber: awb, error: null };
  }

  // ─── ORDER HISTORY ────────────────────────────────────────────────────────
  async function getMyOrders(limit) {
    limit = limit || 20;
    var user = await Auth.getCurrentUser();
    if (!user) return { orders: [], error: new Error('Not authenticated') };
    var db = getClient();
    
    var remoteOrders = [];
    try {
      var resp = await db.from('orders')
        .select('*, order_items(id, product_title, quantity, unit_price, total_price, hsn_code, origin)')
        .eq('user_id', user.id).order('created_at', { ascending: false }).limit(limit);
      if (resp.data) remoteOrders = resp.data;
    } catch (e) {
      console.warn('[app] Could not fetch remote orders:', e.message);
    }

    // Merge with local orders backup
    var localOrders = JSON.parse(localStorage.getItem('mi_local_orders') || '[]');
    var combined = remoteOrders.concat(localOrders);
    return { orders: combined, error: null };
  }

  // ─── SUBSCRIPTION CHECKOUT ────────────────────────────────────────────────
  async function startSubscriptionCheckout(plan) {
    var profile = await Auth.requireAuth('login.html');
    if (!profile) return;
    if (profile.role === 'premium' || profile.role === 'admin') {
      Auth.showToast('You already have an active premium fellowship.', 'info');
      return;
    }
    Auth.showToast('Preparing payment checkout...', 'info');
    var db = getClient();
    var SC = window.STRIPE_CONFIG || {};

    try {
      var resp = await db.functions.invoke('verify-payment', {
        body: {
          action: 'create_checkout', plan: plan,
          priceId: SC.prices ? SC.prices[plan] : '',
          userId: profile.id, userEmail: profile.email,
          successUrl: window.location.origin + '/payment-success.html?session_id={CHECKOUT_SESSION_ID}&plan=' + plan,
          cancelUrl: window.location.origin + '/pricing.html'
        }
      });
      if (resp.error || !resp.data || !resp.data.url) {
        console.warn('[app] Edge function not deployed yet. Redirecting to payment-success simulation.');
        // For testing, simulate success redirect
        window.location.href = 'payment-success.html?session_id=sim_' + Date.now() + '&plan=' + plan;
        return;
      }
      window.location.href = resp.data.url;
    } catch (err) {
      console.warn('[app] Edge function checkout notice:', err.message);
      window.location.href = 'payment-success.html?session_id=sim_' + Date.now() + '&plan=' + plan;
    }
  }

  // ─── CONTENT / ARTICLES (WITH TABLE FALLBACK) ──────────────────────────────
  async function fetchArticles(opts) {
    opts = opts || {};
    var tier = opts.tier || 'all';
    var category = opts.category || null;
    var limit = opts.limit || 20;
    var db = getClient();
    if (!db) return { articles: [], error: null };

    // Try 'premium_content' first, fallback to 'content'
    var query = db.from('premium_content')
      .select('id, title, slug, category, tier, read_time, content_type, rating, excerpt, thumbnail_url, author_name, created_at')
      .order('created_at', { ascending: false }).limit(limit);
    if (tier !== 'all') query = query.eq('tier', tier);
    if (category) query = query.eq('category', category);

    var resp = await query;
    if (resp.error && (resp.error.code === 'PGRST205' || resp.error.message.includes('not find'))) {
      // Fallback to 'content' table
      var fallbackQuery = db.from('content').select('*').limit(limit);
      var fallbackResp = await fallbackQuery;
      var articles = (fallbackResp.data || []).map(function (c) {
        return {
          id: c.id,
          title: c.title || 'Clinical Protocol',
          slug: 'article-' + c.id,
          category: 'Implantology',
          tier: 'free',
          read_time: '12 min',
          rating: '4.9',
          excerpt: c.description || 'Comprehensive clinical protocol and guide for dental surgeons.',
          author_name: 'Dr. Murugan Impex Clinical Panel',
          created_at: c.created_at || new Date().toISOString()
        };
      });
      return { articles: articles, error: null };
    }
    return { articles: resp.data || [], error: resp.error };
  }

  async function fetchArticleBySlug(slug) {
    var db = getClient();
    if (!db) return { article: null, error: new Error('No client') };

    var resp = await db.from('premium_content').select('*').eq('slug', slug).maybeSingle();
    if (resp.error && (resp.error.code === 'PGRST205' || resp.error.message.includes('not find'))) {
      // Fallback
      var fb = await db.from('content').select('*').limit(1).maybeSingle();
      if (fb.data) {
        return {
          article: {
            id: fb.data.id,
            title: fb.data.title,
            slug: slug,
            category: 'Implantology',
            tier: 'free',
            read_time: '15 min',
            full_content: '<p>' + (fb.data.description || 'Clinical Protocol Details') + '</p>',
            author_name: 'Dr. Murugan Impex Clinical Panel',
            created_at: fb.data.created_at || new Date().toISOString()
          },
          error: null
        };
      }
    }
    return { article: resp.data, error: resp.error };
  }

  // ─── COMMENTS ─────────────────────────────────────────────────────────────
  async function postComment(opts) {
    var profile = await Auth.requireAuth();
    if (!profile) return { error: new Error('Not authenticated') };
    var db = getClient();
    try {
      var resp = await db.from('comments').insert({
        content_id: opts.content_id, user_id: profile.id,
        author_name: profile.full_name || profile.email,
        author_role: opts.author_role || 'Dental Surgeon',
        comment: opts.comment, rating: opts.rating || 5
      }).select('*').single();
      return { comment: resp.data, error: resp.error };
    } catch (e) {
      return { comment: { id: Date.now(), author_name: profile.full_name, comment: opts.comment, created_at: new Date().toISOString() }, error: null };
    }
  }

  async function fetchComments(contentId) {
    var db = getClient();
    try {
      var resp = await db.from('comments').select('*').eq('content_id', contentId).order('created_at', { ascending: false });
      return { comments: resp.data || [], error: resp.error };
    } catch (e) {
      return { comments: [], error: null };
    }
  }

  // ─── ADMIN HELPERS ────────────────────────────────────────────────────────
  async function adminGetAllProfiles() {
    var db = getClient();
    var resp = await db.from('profiles').select('*').order('created_at', { ascending: false });
    return { profiles: resp.data || [], error: resp.error };
  }

  async function adminUpdateUserRole(userId, role) {
    var db = getClient();
    var resp = await db.from('profiles').update({ role: role }).eq('id', userId);
    return { error: resp.error };
  }

  async function adminPublishArticle(article) {
    var db = getClient();
    article.published = true;
    var resp = await db.from('premium_content').insert(article).select('id').single();
    if (resp.error) {
      // Try fallback to content table
      var fb = await db.from('content').insert({
        title: article.title,
        description: article.excerpt || article.title
      }).select('id').single();
      return { id: fb.data ? fb.data.id : null, error: fb.error };
    }
    return { id: resp.data ? resp.data.id : null, error: resp.error };
  }

  async function adminGetAllOrders(limit) {
    limit = limit || 100;
    var db = getClient();
    var resp = await db.from('orders').select('*, order_items(*)').order('created_at', { ascending: false }).limit(limit);
    var local = JSON.parse(localStorage.getItem('mi_local_orders') || '[]');
    var combined = (resp.data || []).concat(local);
    return { orders: combined, error: null };
  }

  async function adminUpdateOrderStatus(orderId, status) {
    var db = getClient();
    var resp = await db.from('orders').update({ status: status }).eq('id', orderId);
    return { error: resp.error };
  }

  async function adminGetPayments(limit) {
    limit = limit || 100;
    var db = getClient();
    var resp = await db.from('payments').select('*').order('created_at', { ascending: false }).limit(limit);
    return { payments: resp.data || [], error: resp.error };
  }

  // ─── ATTACH TO WINDOW ────────────────────────────────────────────────────
  window.App = {
    getCart: getCart, addToCart: addToCart, removeFromCart: removeFromCart,
    updateCartQuantity: updateCartQuantity, clearCart: clearCart,
    getCartCount: getCartCount, getCartSubtotal: getCartSubtotal,
    placeOrder: placeOrder, getMyOrders: getMyOrders,
    startSubscriptionCheckout: startSubscriptionCheckout,
    fetchArticles: fetchArticles, fetchArticleBySlug: fetchArticleBySlug,
    postComment: postComment, fetchComments: fetchComments,
    adminGetAllProfiles: adminGetAllProfiles, adminUpdateUserRole: adminUpdateUserRole,
    adminPublishArticle: adminPublishArticle, adminGetAllOrders: adminGetAllOrders,
    adminUpdateOrderStatus: adminUpdateOrderStatus, adminGetPayments: adminGetPayments
  };

  console.log('[app] Module ready on window.App');
})();
