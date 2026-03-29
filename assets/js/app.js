/* ========================================
   Skills Market - app.js
   Data loading, search, filter, rendering
   ======================================== */

(function () {
  'use strict';

  // ---- State ----
  var allSkills = [];
  var categories = [];
  var frameworks = [];
  var activeCategory = 'all';
  var searchQuery = '';
  var favorites = JSON.parse(localStorage.getItem('skill-favorites') || '[]');

  function isFavorited(skillId) {
    return favorites.indexOf(skillId) !== -1;
  }

  function toggleFavorite(skillId) {
    var idx = favorites.indexOf(skillId);
    if (idx === -1) {
      favorites.push(skillId);
    } else {
      favorites.splice(idx, 1);
    }
    localStorage.setItem('skill-favorites', JSON.stringify(favorites));
  }

  // ---- Data Loading ----
  async function loadData() {
    try {
      var [skillsRes, catsRes, fwRes] = await Promise.all([
        fetch('data/skills.json'),
        fetch('data/categories.json'),
        fetch('data/frameworks.json')
      ]);
      allSkills = await skillsRes.json();
      categories = await catsRes.json();
      frameworks = await fwRes.json();
    } catch (e) {
      document.querySelector('.content').innerHTML =
        '<div class="empty-state">数据加载失败，请刷新重试</div>';
      throw e;
    }
  }

  // ---- Helpers ----
  function getCategoryLabel(id) {
    var cat = categories.find(function (c) { return c.id === id; });
    return cat ? cat.name : id;
  }

  function getCategoryIcon(id) {
    var cat = categories.find(function (c) { return c.id === id; });
    return cat ? cat.icon : '📦';
  }

  function filterSkills() {
    var q = searchQuery.toLowerCase().trim();
    return allSkills.filter(function (skill) {
      if (activeCategory === 'favorites') {
        if (!isFavorited(skill.id)) return false;
      } else {
        var matchCategory = activeCategory === 'all' || skill.category === activeCategory;
        if (!matchCategory) return false;
      }
      if (!q) return true;
      return (
        skill.id.toLowerCase().indexOf(q) !== -1 ||
        skill.name.toLowerCase().indexOf(q) !== -1 ||
        skill.summary.toLowerCase().indexOf(q) !== -1 ||
        skill.tags.some(function (t) { return t.toLowerCase().indexOf(q) !== -1; })
      );
    });
  }

  // ---- Escape HTML to prevent XSS ----
  function esc(str) {
    var div = document.createElement('div');
    div.appendChild(document.createTextNode(str));
    return div.innerHTML;
  }

  // ---- Sanitize HTML (strip script/event handlers from Markdown output) ----
  function sanitizeHtml(html) {
    var doc = new DOMParser().parseFromString(html, 'text/html');
    doc.querySelectorAll('script,iframe,object,embed,form').forEach(function (el) { el.remove(); });
    doc.querySelectorAll('*').forEach(function (el) {
      Array.from(el.attributes).forEach(function (attr) {
        if (attr.name.startsWith('on') || (attr.name === 'href' && attr.value.trim().toLowerCase().startsWith('javascript:'))) {
          el.removeAttribute(attr.name);
        }
      });
    });
    return doc.body.innerHTML;
  }

  // ---- Update search placeholder with count ----
  function updateSearchPlaceholder() {
    var input = document.getElementById('search-input');
    if (input) {
      input.placeholder = 'Search ' + allSkills.length + ' skills: try \'code review\', \'git automation\', \'data analysis\'...';
    }
  }

  // ---- Render: Categories ----
  function renderCategories() {
    var container = document.getElementById('categories');
    if (!container) return;

    var html = '<button class="category-tag active" data-id="all">全部</button>';
    html += '<button class="category-tag" data-id="favorites">♡ 收藏</button>';
    categories.forEach(function (cat) {
      html += '<button class="category-tag" data-id="' + esc(cat.id) + '">'
        + cat.icon + ' ' + esc(cat.name) + '</button>';
    });
    container.innerHTML = html;

    container.addEventListener('click', function (e) {
      var tag = e.target.closest('.category-tag');
      if (!tag) return;
      activeCategory = tag.dataset.id;
      container.querySelectorAll('.category-tag').forEach(function (t) {
        t.classList.toggle('active', t.dataset.id === activeCategory);
      });
      renderSkillsGrid();
    });
  }

  // ---- Render: Skills Grid — Terminal Card Style ----
  function renderSkillsGrid() {
    var container = document.getElementById('skills-grid');
    if (!container) return;

    var skills = filterSkills();

    if (skills.length === 0) {
      container.innerHTML = '<div class="empty-state">没有找到匹配的 Skills</div>';
      return;
    }

    container.innerHTML = skills.map(function (skill, index) {
      var catIcon = getCategoryIcon(skill.category);
      var catLabel = getCategoryLabel(skill.category);
      var authorName = skill.author ? skill.author.name : 'unknown';
      var delay = Math.min(index * 0.05, 0.3);

      return '<div class="skill-card" data-id="' + esc(skill.id) + '" style="animation-delay:' + delay + 's">'
        + '<div class="card-header">'
        + '<div class="window-dots">'
        + '<span class="dot red"></span>'
        + '<span class="dot yellow"></span>'
        + '<span class="dot green"></span>'
        + '</div>'
        + '<span class="card-filename">' + esc(skill.name) + '</span>'
        + '<span class="card-stars">★ ' + skill.files.length + ' files</span>'
        + '</div>'
        + '<div class="card-body">'
        + '<div class="card-source">'
        + '<span class="card-icon">' + catIcon + '</span>'
        + '<span class="card-category">from "' + esc(authorName) + '"</span>'
        + '</div>'
        + '<div class="card-summary">' + esc(skill.summary) + '</div>'
        + '<div class="card-footer">'
        + '<span class="card-date">' + esc(skill.updatedAt) + '</span>'
        + '<span class="card-favorite' + (isFavorited(skill.id) ? ' favorited' : '') + '" data-skill-id="' + esc(skill.id) + '">'
        + (isFavorited(skill.id) ? '♥' : '♡')
        + '</span>'
        + '</div>'
        + '</div>'
        + '</div>';
    }).join('');
  }

  // ---- Bind: Skills Grid Click (once) ----
  function bindSkillsGridClick() {
    var container = document.getElementById('skills-grid');
    if (!container) return;
    container.addEventListener('click', function (e) {
      if (e.target.classList.contains('card-favorite')) {
        var skillId = e.target.dataset.skillId;
        toggleFavorite(skillId);
        e.target.classList.toggle('favorited');
        e.target.textContent = isFavorited(skillId) ? '♥' : '♡';
        if (activeCategory === 'favorites') renderSkillsGrid();
        return;
      }
      var card = e.target.closest('.skill-card');
      if (!card) return;
      window.location.href = 'skill.html?id=' + encodeURIComponent(card.dataset.id);
    });
  }

  // ---- Install Section Constants & Helpers ----
  var INSTALL_PLATFORMS = [
    { id: 'claude-code', label: 'Claude Code', basePath: '.claude/skills' },
    { id: 'codex', label: 'Codex', basePath: '.agents/skills' },
    { id: 'openclaw', label: 'OpenClaw', dynamic: true }
  ];

  var INSTALL_OS = [
    { id: 'macos', label: 'macOS' },
    { id: 'windows', label: 'Windows' }
  ];

  function detectOS() {
    return (navigator.platform && navigator.platform.indexOf('Win') !== -1) ? 'windows' : 'macos';
  }

  function getUniqueDirs(files, skillId) {
    var dirs = {};
    files.forEach(function (f) {
      var parts = f.split('/');
      if (parts.length > 1) {
        for (var i = 1; i < parts.length; i++) {
          dirs[parts.slice(0, i).join('/')] = true;
        }
      }
    });
    var result = Object.keys(dirs);
    result.sort();
    return result;
  }

  function getInstallBasePath(platformId, osId, skillId) {
    var platform = INSTALL_PLATFORMS.find(function (p) { return p.id === platformId; });
    if (platform && platform.dynamic) {
      return osId === 'windows' ? '$SkillDir' : '$SKILL_DIR';
    }
    var base = platform ? platform.basePath : '.claude/skills';
    if (osId === 'windows') {
      return '$env:USERPROFILE\\' + base.replace(/\//g, '\\') + '\\' + skillId;
    }
    return '~/' + base + '/' + skillId;
  }

  function generateInstallScript(platformId, osId, skill) {
    var baseUrl = window.location.origin + '/skills/' + skill.id + '/';
    var platform = INSTALL_PLATFORMS.find(function (p) { return p.id === platformId; });
    var isDynamic = platform && platform.dynamic;
    var basePath = getInstallBasePath(platformId, osId, skill.id);
    var subDirs = getUniqueDirs(skill.files, skill.id);

    if (osId === 'macos') {
      var cmds = [];
      // Dynamic platforms: prepend variable assignment and quote paths for variable expansion
      if (isDynamic) {
        cmds.push('SKILL_DIR="$(npm root -g)/openclaw/skills/' + skill.id + '"');
      }
      var q = isDynamic ? '"' : '';
      // mkdir for base + subdirs
      var mkdirPaths = [q + basePath + q];
      subDirs.forEach(function (d) { mkdirPaths.push(q + basePath + '/' + d + q); });
      cmds.push('mkdir -p ' + mkdirPaths.join(' '));
      // curl for each file
      skill.files.forEach(function (f) {
        cmds.push('curl -sL ' + baseUrl + f + ' -o ' + q + basePath + '/' + f + q);
      });
      return cmds.join(' && \\\n');
    }

    // Windows PowerShell
    var lines = [];
    // Dynamic platforms: prepend variable assignment
    if (isDynamic) {
      lines.push('$SkillDir = "$(npm root -g)\\openclaw\\skills\\' + skill.id + '"');
    }
    var mkdirPaths = [basePath];
    subDirs.forEach(function (d) { mkdirPaths.push(basePath + '\\' + d.replace(/\//g, '\\')); });
    mkdirPaths.forEach(function (p) {
      lines.push('New-Item -ItemType Directory -Force -Path "' + p + '" | Out-Null');
    });
    skill.files.forEach(function (f) {
      var winFile = f.replace(/\//g, '\\');
      lines.push('Invoke-WebRequest -Uri "' + baseUrl + f + '" -OutFile "' + basePath + '\\' + winFile + '"');
    });
    return lines.join('\n');
  }

  function renderInstallSection(skill) {
    var container = document.getElementById('skill-install');
    if (!container) return;

    var currentPlatform = 'claude-code';
    var currentOS = detectOS();

    function buildHTML() {
      var platformTabs = INSTALL_PLATFORMS.map(function (p) {
        return '<button class="install-tab' + (p.id === currentPlatform ? ' active' : '') + '" data-platform="' + p.id + '">' + esc(p.label) + '</button>';
      }).join('');

      var osTabs = INSTALL_OS.map(function (o) {
        return '<button class="install-tab' + (o.id === currentOS ? ' active' : '') + '" data-os="' + o.id + '">' + esc(o.label) + '</button>';
      }).join('');

      var script = generateInstallScript(currentPlatform, currentOS, skill);
      var langLabel = currentOS === 'macos' ? 'bash' : 'powershell';

      return '<p class="section-title">\u5B89\u88C5</p>'
        + '<div class="install-selectors">'
        + '<div class="install-selector-group" id="install-platform-tabs">' + platformTabs + '</div>'
        + '<div class="install-selector-group" id="install-os-tabs">' + osTabs + '</div>'
        + '</div>'
        + '<div class="install-code-wrapper">'
        + '<div class="install-code-header">'
        + '<span class="install-code-lang">' + langLabel + '</span>'
        + '<button class="install-copy-btn" id="install-copy-btn">\u590D\u5236</button>'
        + '</div>'
        + '<pre class="install-code" id="install-code-block"><code>' + esc(script) + '</code></pre>'
        + '</div>';
    }

    container.innerHTML = buildHTML();

    function rebind() {
      // Platform tabs
      container.querySelectorAll('#install-platform-tabs .install-tab').forEach(function (btn) {
        btn.addEventListener('click', function () {
          currentPlatform = btn.dataset.platform;
          container.innerHTML = buildHTML();
          rebind();
        });
      });
      // OS tabs
      container.querySelectorAll('#install-os-tabs .install-tab').forEach(function (btn) {
        btn.addEventListener('click', function () {
          currentOS = btn.dataset.os;
          container.innerHTML = buildHTML();
          rebind();
        });
      });
      // Copy button
      var copyBtn = document.getElementById('install-copy-btn');
      if (copyBtn) {
        copyBtn.addEventListener('click', function () {
          var code = document.getElementById('install-code-block').textContent;
          navigator.clipboard.writeText(code).then(function () {
            copyBtn.textContent = '\u5DF2\u590D\u5236';
            copyBtn.classList.add('copied');
            setTimeout(function () {
              copyBtn.textContent = '\u590D\u5236';
              copyBtn.classList.remove('copied');
            }, 2000);
          });
        });
      }
    }

    rebind();
  }

  // ---- Render: Skill Detail Page ----
  async function renderSkillDetail() {
    var params = new URLSearchParams(window.location.search);
    var id = params.get('id');
    if (!id) return;

    var skill = allSkills.find(function (s) { return s.id === id; });
    if (!skill) {
      document.getElementById('skill-detail').innerHTML =
        '<div class="empty-state">Skill 不存在</div>';
      return;
    }

    // Update page title
    document.title = skill.name + ' - Skills Market - 元初AI';

    // Header
    var headerEl = document.getElementById('skill-header');
    var authorHtml = skill.author.link
      ? '<a href="' + esc(skill.author.link) + '" target="_blank">' + esc(skill.author.name) + '</a>'
      : esc(skill.author.name);

    headerEl.innerHTML =
      '<div class="skill-detail-icon">' + esc(skill.icon) + '</div>'
      + '<h1 class="skill-detail-name">' + esc(skill.name) + '</h1>'
      + '<div class="skill-detail-meta">'
      + '<span>' + authorHtml + '</span>'
      + '<span>更新于 ' + esc(skill.updatedAt) + '</span>'
      + '</div>';

    // Tags
    var tagsEl = document.getElementById('skill-tags');
    var catIcon = getCategoryIcon(skill.category);
    var catLabel = getCategoryLabel(skill.category);
    var catHtml = '<span class="tag">' + catIcon + ' ' + esc(catLabel) + '</span>';
    var tagsList = skill.tags.map(function (t) {
      return '<span class="tag">#' + esc(t) + '</span>';
    }).join('');
    tagsEl.innerHTML = catHtml + tagsList;

    // Description — fetch README.md
    var descEl = document.getElementById('skill-description');
    if (skill.description && skill.description.endsWith('.md')) {
      try {
        var res = await fetch(skill.description);
        if (res.ok) {
          var md = await res.text();
          var rendered = typeof marked !== 'undefined' ? marked.parse(md) : '<pre>' + esc(md) + '</pre>';
          descEl.innerHTML = sanitizeHtml(rendered);
        } else {
          descEl.innerHTML = '<p>' + esc(skill.summary) + '</p>';
        }
      } catch (e) {
        descEl.innerHTML = '<p>' + esc(skill.summary) + '</p>';
      }
    } else {
      descEl.innerHTML = '<p>' + esc(skill.summary) + '</p>';
    }

    // Examples
    var examplesEl = document.getElementById('skill-examples');
    if (skill.examples && skill.examples.length > 0) {
      examplesEl.innerHTML =
        '<p class="section-title">EXAMPLES</p>'
        + skill.examples.map(function (ex) {
          return '<div class="example-item">'
            + '<div class="example-label">Input</div>'
            + '<div class="example-content">' + esc(ex.input) + '</div>'
            + '<div class="example-label">Output</div>'
            + '<div class="example-content">' + esc(ex.output) + '</div>'
            + '</div>';
        }).join('');
    } else {
      examplesEl.style.display = 'none';
    }

    // Downloads (sidebar)
    var downloadsEl = document.getElementById('skill-downloads');
    var fileCount = skill.files.length;
    var downloadLabel = fileCount === 1 ? '下载 SKILL.md' : '下载 Skill（' + fileCount + ' 个文件）';
    downloadsEl.innerHTML =
      '<p class="section-title">下载</p>'
      + '<div class="download-item">'
      + '<div class="download-item-inner">'
      + '<div class="download-info">'
      + '<div class="download-framework">' + esc(skill.name) + '</div>'
      + '<div class="download-desc">跨平台通用格式（Claude Code / Codex / OpenClaw）</div>'
      + '</div>'
      + '<button class="download-btn" id="download-skill-btn">' + downloadLabel + '</button>'
      + '</div>'
      + '</div>';

    // Bind download button
    document.getElementById('download-skill-btn').addEventListener('click', async function () {
      var btn = this;
      btn.disabled = true;
      btn.textContent = '打包中...';
      try {
        if (fileCount === 1) {
          // Single file: download directly
          var filePath = 'skills/' + skill.id + '/' + skill.files[0];
          var res = await fetch(filePath);
          var blob = await res.blob();
          var url = URL.createObjectURL(blob);
          var a = document.createElement('a');
          a.href = url;
          a.download = skill.files[0];
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          URL.revokeObjectURL(url);
        } else {
          // Multiple files: zip them
          var zip = new JSZip();
          var folder = zip.folder(skill.id);
          var fetches = skill.files.map(function (f) {
            return fetch('skills/' + skill.id + '/' + f)
              .then(function (res) { return res.blob(); })
              .then(function (blob) { folder.file(f, blob); });
          });
          await Promise.all(fetches);
          var content = await zip.generateAsync({ type: 'blob' });
          var url = URL.createObjectURL(content);
          var a = document.createElement('a');
          a.href = url;
          a.download = skill.id + '.zip';
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          URL.revokeObjectURL(url);
        }
      } catch (e) {
        console.error('Download failed:', e);
      }
      btn.disabled = false;
      btn.textContent = downloadLabel;
    });

    // Install section (sidebar)
    renderInstallSection(skill);

    // Meta card (sidebar)
    var metaEl = document.getElementById('skill-meta-card');
    if (metaEl) {
      var linksHtml = '';
      if (skill.links && skill.links.github) {
        linksHtml = '<a href="' + esc(skill.links.github) + '" target="_blank">GitHub</a>';
      }
      metaEl.innerHTML =
        '<div class="meta-row"><span class="meta-label">作者</span><span class="meta-value">' + authorHtml + '</span></div>'
        + '<div class="meta-row"><span class="meta-label">分类</span><span class="meta-value">' + catIcon + ' ' + esc(catLabel) + '</span></div>'
        + '<div class="meta-row"><span class="meta-label">格式</span><span class="meta-value">' + skill.files.length + ' 个文件</span></div>'
        + '<div class="meta-row"><span class="meta-label">更新</span><span class="meta-value">' + esc(skill.updatedAt) + '</span></div>'
        + '<div class="meta-row"><span class="meta-label">创建</span><span class="meta-value">' + esc(skill.createdAt) + '</span></div>'
        + (linksHtml ? '<div class="meta-row"><span class="meta-label">链接</span><span class="meta-value">' + linksHtml + '</span></div>' : '');
    }

    // Related Skills — same category, exclude self
    var related = allSkills.filter(function (s) {
      return s.category === skill.category && s.id !== skill.id;
    }).slice(0, 4);

    var relatedEl = document.getElementById('skill-related');
    if (related.length > 0) {
      document.getElementById('related-grid').innerHTML = related.map(function (s) {
        var fileName = s.id + '.md';
        var catIcon = getCategoryIcon(s.category);
        var authorName = s.author ? s.author.name : 'unknown';
        return '<div class="skill-card" data-id="' + esc(s.id) + '">'
          + '<div class="card-header">'
          + '<div class="window-dots">'
          + '<span class="dot red"></span>'
          + '<span class="dot yellow"></span>'
          + '<span class="dot green"></span>'
          + '</div>'
          + '<span class="card-filename">' + esc(s.name) + '</span>'
          + '</div>'
          + '<div class="card-body">'
          + '<div class="card-source">'
          + '<span class="card-icon">' + catIcon + '</span>'
          + '<span class="card-category">from "' + esc(authorName) + '"</span>'
          + '</div>'
          + '<div class="card-summary">' + esc(s.summary) + '</div>'
          + '<div class="card-footer">'
          + '<span class="card-date">' + esc(s.updatedAt) + '</span>'
          + '<span class="card-favorite' + (isFavorited(s.id) ? ' favorited' : '') + '" data-skill-id="' + esc(s.id) + '">'
          + (isFavorited(s.id) ? '♥' : '♡')
          + '</span>'
          + '</div>'
          + '</div>'
          + '</div>';
      }).join('');

      document.getElementById('related-grid').addEventListener('click', function (e) {
        if (e.target.classList.contains('card-favorite')) {
          var skillId = e.target.dataset.skillId;
          toggleFavorite(skillId);
          e.target.classList.toggle('favorited');
          e.target.textContent = isFavorited(skillId) ? '♥' : '♡';
          return;
        }
        var card = e.target.closest('.skill-card');
        if (!card) return;
        window.location.href = 'skill.html?id=' + encodeURIComponent(card.dataset.id);
      });
    } else {
      relatedEl.style.display = 'none';
    }
  }

  // ---- Search Binding ----
  function bindSearch() {
    var input = document.getElementById('search-input');
    if (!input) return;

    var timer;
    input.addEventListener('input', function () {
      clearTimeout(timer);
      timer = setTimeout(function () {
        searchQuery = input.value;
        renderSkillsGrid();
      }, 150);
    });
  }

  // ---- Init ----
  async function init() {
    await loadData();

    var isDetailPage = document.getElementById('skill-detail');
    if (isDetailPage) {
      await renderSkillDetail();
    } else {
      updateSearchPlaceholder();
      renderCategories();
      renderSkillsGrid();
      bindSkillsGridClick();
      bindSearch();
    }
  }

  // Run
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
