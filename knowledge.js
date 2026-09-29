/**
 * MURUGAN IMPEX — KNOWLEDGE HUB
 * knowledge.js — Article listing, reader, comments, and realtime
 *
 * Load order:
 *   1. supabase CDN
 *   2. supabase-config.js
 *   3. auth.js
 *   4. app.js
 *   5. knowledge.js (this file)
 *
 * All functions attach to window.Knowledge.*
 */

(function () {
  'use strict';

  var db   = window.supabaseClient;
  var Auth = window.Auth;
  var App  = window.App;

  if (!db || !Auth || !App) {
    console.error('[knowledge] Missing dependencies. Ensure supabase-config.js, auth.js, app.js are loaded first.');
    return;
  }

  // ─── RENDER ARTICLE CARDS ─────────────────────────────────────────────────
  async function renderArticleList(container, opts) {
    opts = opts || {};
    if (!container) return;
    container.innerHTML = '<p style="text-align:center;color:#64748b;padding:40px">Loading articles...</p>';

    var result = await App.fetchArticles({
      tier: opts.tier || 'all',
      category: opts.category || null,
      limit: opts.limit || 20
    });

    if (result.error) {
      container.innerHTML = '<p style="color:#ef4444;text-align:center">Failed to load articles.</p>';
      console.error('[knowledge] fetchArticles error:', result.error.message);
      return;
    }

    if (result.articles.length === 0) {
      container.innerHTML = '<p style="color:#64748b;text-align:center;padding:40px">No articles published yet.</p>';
      return;
    }

    var profile = await Auth.getCurrentProfile();
    var isPremium = profile && (profile.role === 'premium' || profile.role === 'admin');

    var html = '<div class="knowledge-grid" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:24px;">';
    result.articles.forEach(function (article) {
      var locked = article.tier === 'premium' && !isPremium;
      var badge = article.tier === 'premium'
        ? '<span style="background:#f59e0b22;color:#f59e0b;border:1px solid #f59e0b44;border-radius:20px;padding:2px 10px;font-size:11px;font-weight:600">PREMIUM</span>'
        : '<span style="background:#10b98122;color:#10b981;border:1px solid #10b98144;border-radius:20px;padding:2px 10px;font-size:11px;font-weight:600">FREE</span>';

      html += '<div class="knowledge-card" style="background:var(--bg-card,#fff);border-radius:var(--radius-lg,16px);overflow:hidden;box-shadow:var(--shadow-md);transition:transform 0.2s,box-shadow 0.2s;border:1px solid var(--border-subtle,#e2e8f0);cursor:pointer" onclick="Knowledge.openArticle(\'' + article.slug + '\')">';

      if (article.thumbnail_url) {
        html += '<div style="height:180px;overflow:hidden"><img src="' + article.thumbnail_url + '" alt="' + article.title + '" style="width:100%;height:100%;object-fit:cover"></div>';
      } else {
        html += '<div style="height:180px;background:linear-gradient(135deg,var(--primary-teal,#00a896),var(--primary-navy,#0f2b48));display:flex;align-items:center;justify-content:center;color:white;font-size:40px">📚</div>';
      }

      html += '<div style="padding:16px">';
      html += '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">' + badge;
      html += '<span style="font-size:12px;color:var(--text-muted,#64748b)">' + (article.read_time || '15 min') + '</span></div>';
      html += '<h3 style="font-size:16px;font-weight:700;margin-bottom:6px;color:var(--text-main,#1a202c);line-height:1.3">' + article.title + '</h3>';
      html += '<p style="font-size:13px;color:var(--text-muted,#64748b);line-height:1.5;margin-bottom:12px">' + (article.excerpt || '').slice(0, 120) + '...</p>';
      html += '<div style="display:flex;justify-content:space-between;align-items:center;font-size:12px;color:var(--text-light,#94a3b8)">';
      html += '<span>⭐ ' + (article.rating || '4.9') + '</span>';
      html += '<span>' + (article.category || 'General') + '</span>';
      html += '</div>';
      if (locked) {
        html += '<div style="margin-top:10px;text-align:center;padding:6px;background:#f59e0b11;border-radius:8px;font-size:12px;color:#f59e0b">🔒 Premium subscription required</div>';
      }
      html += '</div></div>';
    });
    html += '</div>';
    container.innerHTML = html;
  }

  // ─── OPEN ARTICLE ──────────────────────────────────────────────────────────
  async function openArticle(slug) {
    var result = await App.fetchArticleBySlug(slug);
    if (result.error || !result.article) {
      Auth.showToast('Article not found.', 'error');
      return;
    }

    var article = result.article;
    var profile = await Auth.getCurrentProfile();
    var isPremium = profile && (profile.role === 'premium' || profile.role === 'admin');

    if (article.tier === 'premium' && !isPremium) {
      Auth.showToast('Premium subscription required to read this article.', 'warning');
      window.location.href = 'pricing.html';
      return;
    }

    // Navigate to article reader page
    window.location.href = 'premium-content.html?slug=' + encodeURIComponent(slug);
  }

  // ─── RENDER FULL ARTICLE (for premium-content.html) ────────────────────────
  async function renderArticleReader(container) {
    if (!container) return;

    var params = new URLSearchParams(window.location.search);
    var slug = params.get('slug');

    if (!slug) {
      container.innerHTML = '<p style="color:#64748b;text-align:center;padding:40px">No article selected.</p>';
      return;
    }

    container.innerHTML = '<p style="text-align:center;color:#64748b;padding:40px">Loading article...</p>';

    var result = await App.fetchArticleBySlug(slug);
    if (result.error || !result.article) {
      container.innerHTML = '<p style="color:#ef4444;text-align:center">Article not found.</p>';
      return;
    }

    var article = result.article;
    var profile = await Auth.getCurrentProfile();
    var isPremium = profile && (profile.role === 'premium' || profile.role === 'admin');

    if (article.tier === 'premium' && !isPremium) {
      container.innerHTML = '<div style="text-align:center;padding:60px"><h2>🔒 Premium Content</h2><p style="color:#64748b;margin:16px 0">This surgical masterclass requires a premium subscription.</p><a href="pricing.html" style="display:inline-block;background:var(--primary-teal,#00a896);color:white;padding:12px 28px;border-radius:8px;text-decoration:none;font-weight:600">View Plans</a></div>';
      return;
    }

    var html = '';
    html += '<article style="max-width:800px;margin:0 auto">';
    html += '<div style="margin-bottom:24px">';
    html += '<span style="background:' + (article.tier === 'premium' ? '#f59e0b22;color:#f59e0b' : '#10b98122;color:#10b981') + ';border-radius:20px;padding:3px 12px;font-size:12px;font-weight:600">' + article.tier.toUpperCase() + '</span>';
    html += ' <span style="font-size:12px;color:var(--text-muted,#64748b);margin-left:8px">' + (article.category || '') + '</span>';
    html += ' <span style="font-size:12px;color:var(--text-light,#94a3b8);margin-left:8px">' + (article.read_time || '') + '</span>';
    html += '</div>';
    html += '<h1 style="font-size:28px;font-weight:800;color:var(--text-main,#1a202c);margin-bottom:12px;line-height:1.3">' + article.title + '</h1>';
    html += '<p style="font-size:14px;color:var(--text-muted,#64748b);margin-bottom:24px">By ' + (article.author_name || 'Dr. Murugan Impex Clinical Panel') + ' · ' + Auth.formatDate(article.created_at) + '</p>';

    if (article.thumbnail_url) {
      html += '<img src="' + article.thumbnail_url + '" alt="' + article.title + '" style="width:100%;border-radius:12px;margin-bottom:24px">';
    }

    html += '<div class="article-content" style="font-size:16px;line-height:1.8;color:var(--text-main,#1a202c)">' + article.full_content + '</div>';

    if (article.download_file_url) {
      html += '<div style="margin-top:24px;padding:16px;background:var(--primary-teal,#00a896)11;border:1px solid var(--primary-teal,#00a896)33;border-radius:12px">';
      html += '<a href="' + article.download_file_url + '" target="_blank" style="color:var(--primary-teal,#00a896);font-weight:600;text-decoration:none">📄 Download: ' + (article.download_badge || 'Clinical Protocol PDF') + '</a>';
      html += '</div>';
    }

    html += '</article>';

    // Comments section
    html += '<div id="comments-section" style="max-width:800px;margin:40px auto 0">';
    html += '<h3 style="font-size:20px;font-weight:700;margin-bottom:16px">💬 Discussion</h3>';
    html += '<div id="comment-form-area"></div>';
    html += '<div id="comments-list" style="margin-top:20px"></div>';
    html += '</div>';

    container.innerHTML = html;

    // Render comment form and list
    renderCommentForm(document.getElementById('comment-form-area'), article.id);
    await renderComments(document.getElementById('comments-list'), article.id);

    // Subscribe to realtime comments
    Auth.subscribeToTable('comments', function (newComment) {
      if (newComment.content_id === article.id) {
        prependComment(document.getElementById('comments-list'), newComment);
      }
    }, { column: 'content_id', value: article.id });
  }

  // ─── COMMENT FORM ──────────────────────────────────────────────────────────
  function renderCommentForm(container, contentId) {
    if (!container) return;
    var html = '<form id="comment-form" style="display:flex;gap:8px;margin-bottom:16px">';
    html += '<input type="text" id="comment-input" placeholder="Add a comment or clinical query..." style="flex:1;padding:10px 14px;border:1px solid var(--border-subtle,#e2e8f0);border-radius:8px;font-size:14px;background:var(--bg-card,#fff);color:var(--text-main,#1a202c)">';
    html += '<button type="submit" style="padding:10px 20px;background:var(--primary-teal,#00a896);color:white;border:none;border-radius:8px;font-weight:600;cursor:pointer">Post</button>';
    html += '</form>';
    container.innerHTML = html;

    document.getElementById('comment-form').addEventListener('submit', async function (e) {
      e.preventDefault();
      var input = document.getElementById('comment-input');
      var text = input.value.trim();
      if (!text) return;
      input.disabled = true;
      var result = await App.postComment({ content_id: contentId, comment: text });
      input.disabled = false;
      if (result.error) {
        Auth.showToast('Failed to post comment: ' + result.error.message, 'error');
      } else {
        input.value = '';
        Auth.showToast('Comment posted!', 'success');
      }
    });
  }

  // ─── RENDER COMMENTS LIST ──────────────────────────────────────────────────
  async function renderComments(container, contentId) {
    if (!container) return;
    var result = await App.fetchComments(contentId);
    if (result.error) {
      container.innerHTML = '<p style="color:#ef4444;font-size:13px">Could not load comments.</p>';
      return;
    }
    if (result.comments.length === 0) {
      container.innerHTML = '<p style="color:#94a3b8;font-size:13px">No comments yet. Be the first to share your clinical insight!</p>';
      return;
    }
    var html = '';
    result.comments.forEach(function (c) { html += buildCommentCard(c); });
    container.innerHTML = html;
  }

  function prependComment(container, comment) {
    if (!container) return;
    var placeholder = container.querySelector('p');
    if (placeholder && placeholder.textContent.includes('No comments')) placeholder.remove();
    container.insertAdjacentHTML('afterbegin', buildCommentCard(comment));
  }

  function buildCommentCard(c) {
    return '<div style="padding:12px 0;border-bottom:1px solid var(--border-subtle,#e2e8f0)">' +
      '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px">' +
        '<span style="font-weight:600;font-size:14px;color:var(--text-main,#1a202c)">' + (c.author_name || 'Doctor') + '</span>' +
        '<span style="font-size:12px;color:var(--text-light,#94a3b8)">' + Auth.formatDate(c.created_at) + '</span>' +
      '</div>' +
      '<div style="font-size:12px;color:var(--text-muted,#64748b);margin-bottom:4px">' + (c.author_role || 'Dental Surgeon') + ' · ⭐ ' + (c.rating || 5) + '</div>' +
      '<p style="font-size:14px;color:var(--text-main,#1a202c);line-height:1.5">' + c.comment + '</p>' +
    '</div>';
  }

  // ─── CATEGORY FILTER ───────────────────────────────────────────────────────
  function setupCategoryFilter(container, articlesContainer) {
    if (!container) return;
    var categories = ['All', 'Implantology', 'Prosthodontics', 'CAD/CAM', 'Endodontics', 'Orthodontics', 'Surgery', 'Materials'];
    var html = '<div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:24px">';
    categories.forEach(function (cat) {
      html += '<button class="cat-filter-btn" data-category="' + (cat === 'All' ? '' : cat) + '" style="padding:6px 16px;border-radius:20px;border:1px solid var(--border-subtle,#e2e8f0);background:' + (cat === 'All' ? 'var(--primary-teal,#00a896)' : 'var(--bg-card,#fff)') + ';color:' + (cat === 'All' ? 'white' : 'var(--text-muted,#64748b)') + ';font-size:13px;cursor:pointer;font-weight:500;transition:all 0.2s">' + cat + '</button>';
    });
    html += '</div>';
    container.innerHTML = html;

    container.querySelectorAll('.cat-filter-btn').forEach(function (btn) {
      btn.addEventListener('click', function () {
        container.querySelectorAll('.cat-filter-btn').forEach(function (b) {
          b.style.background = 'var(--bg-card,#fff)';
          b.style.color = 'var(--text-muted,#64748b)';
        });
        btn.style.background = 'var(--primary-teal,#00a896)';
        btn.style.color = 'white';
        var cat = btn.dataset.category;
        renderArticleList(articlesContainer, { tier: 'all', category: cat || null });
      });
    });
  }

  // ─── PUBLIC API ───────────────────────────────────────────────────────────
  window.Knowledge = {
    renderArticleList: renderArticleList,
    openArticle: openArticle,
    renderArticleReader: renderArticleReader,
    renderComments: renderComments,
    setupCategoryFilter: setupCategoryFilter
  };

  console.log('[knowledge] Module loaded. Access via window.Knowledge.*');
})();
