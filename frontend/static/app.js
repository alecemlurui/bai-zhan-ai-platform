const API_BASE = ''; // 前端与后端同域
const LS_TOKEN = 'bz_token';
const LS_USER = 'bz_user';

let state = {
  token: localStorage.getItem(LS_TOKEN) || '',
  user: JSON.parse(localStorage.getItem(LS_USER) || 'null'),
  currentTopicId: null,
  currentTitleId: null,
  currentArticleId: null,
};

// ------------------------- 工具 -------------------------
async function api(path, options = {}) {
  const url = `${API_BASE}${path}`;
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };
  if (state.token) headers['Authorization'] = `Bearer ${state.token}`;
  const resp = await fetch(url, { ...options, headers });
  const body = await resp.json().catch(() => ({}));
  if (!resp.ok) {
    if (resp.status === 401) {
      logout();
      showAuth();
      throw new Error('登录已过期，请重新登录');
    }
    const detail = body.detail || body.message || JSON.stringify(body);
    throw new Error(`${resp.status}: ${detail}`);
  }
  return body;
}

function toast(message, type = 'success') {
  const el = document.getElementById('toast');
  el.textContent = message;
  el.className = `toast ${type} show`;
  setTimeout(() => (el.className = 'toast'), 3000);
}

function formatTime(iso) {
  if (!iso) return '-';
  const d = new Date(iso);
  return d.toLocaleString();
}

function escapeHtml(str) {
  return String(str).replace(/[&<>]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));
}

// ------------------------- 状态初始化 -------------------------
function initApp() {
  if (state.token && state.user) {
    showWorkspace();
    loadTopics();
  } else {
    showAuth();
  }
}

function showAuth() {
  document.getElementById('auth-section').style.display = 'block';
  document.getElementById('workspace').style.display = 'none';
  document.getElementById('user-bar').style.display = 'none';
}

function showWorkspace() {
  document.getElementById('auth-section').style.display = 'none';
  document.getElementById('workspace').style.display = 'block';
  document.getElementById('user-bar').style.display = 'flex';
  document.getElementById('username').textContent = state.user?.username || '用户';
}

// ------------------------- 认证 -------------------------
async function login(e) {
  e.preventDefault();
  const username = document.getElementById('login-username').value.trim();
  const password = document.getElementById('login-password').value;
  try {
    const data = await api('/api/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });
    state.token = data.access_token;
    state.user = { username };
    localStorage.setItem(LS_TOKEN, state.token);
    localStorage.setItem(LS_USER, JSON.stringify(state.user));
    showWorkspace();
    loadTopics();
    toast('登录成功');
  } catch (err) {
    toast(err.message, 'error');
  }
}

async function register(e) {
  e.preventDefault();
  const username = document.getElementById('register-username').value.trim();
  const password = document.getElementById('register-password').value;
  const email = document.getElementById('register-email').value.trim() || null;
  try {
    await api('/api/v1/auth/register', {
      method: 'POST',
      body: JSON.stringify({ username, password, email }),
    });
    toast('注册成功，请登录');
    switchTab('login');
    document.getElementById('login-username').value = username;
  } catch (err) {
    toast(err.message, 'error');
  }
}

function logout() {
  state = { token: '', user: null, currentTopicId: null, currentTitleId: null, currentArticleId: null };
  localStorage.removeItem(LS_TOKEN);
  localStorage.removeItem(LS_USER);
  showAuth();
}

// ------------------------- 页面与标签 -------------------------
function switchTab(name) {
  document.querySelectorAll('#auth-section .tab').forEach(t => {
    t.classList.toggle('active', t.dataset.tab === name);
  });
  document.querySelectorAll('#auth-section .form').forEach(f => {
    f.classList.toggle('active', f.id === `${name}-form`);
  });
}

function switchPage(name) {
  document.querySelectorAll('.nav-item').forEach(n => n.classList.toggle('active', n.dataset.page === name));
  document.querySelectorAll('.page').forEach(p => p.classList.toggle('active', p.id === `page-${name}`));
  if (name === 'articles') loadArticles();
  if (name === 'tasks') loadTasks();
}

// ------------------------- 主题 -------------------------
async function loadTopics() {
  try {
    const topics = await api('/api/v1/topics');
    const list = document.getElementById('topic-list');
    list.innerHTML = topics.length
      ? topics.map(t => `
        <li data-id="${t.id}" data-title="${escapeHtml(t.title)}">
          <div>
            <div>${escapeHtml(t.title)}</div>
            <div class="meta">ID: ${t.id} · 状态: ${t.status}</div>
          </div>
          <button class="select-topic">选择</button>
        </li>
      `).join('')
      : '<li class="meta">暂无主题</li>';
    list.querySelectorAll('.select-topic').forEach(btn => {
      btn.addEventListener('click', e => {
        e.stopPropagation();
        const li = btn.closest('li');
        selectTopic(Number(li.dataset.id), li.dataset.title);
      });
    });
  } catch (err) {
    toast(err.message, 'error');
  }
}

async function createTopic(e) {
  e.preventDefault();
  const title = document.getElementById('topic-title').value.trim();
  if (!title) return;
  try {
    await api('/api/v1/topics', {
      method: 'POST',
      body: JSON.stringify({ title, params: {} }),
    });
    document.getElementById('topic-title').value = '';
    toast('主题创建成功');
    loadTopics();
  } catch (err) {
    toast(err.message, 'error');
  }
}

function selectTopic(id, title) {
  state.currentTopicId = id;
  document.getElementById('topic-detail').style.display = 'block';
  document.getElementById('detail-title').textContent = title;
  document.getElementById('detail-topic-id').textContent = id;
  loadTitles(id);
  loadTopicArticles(id);
}

// ------------------------- 标题 -------------------------
async function generateTitles() {
  if (!state.currentTopicId) return toast('请先选择主题', 'error');
  try {
    const task = await api(`/api/v1/topics/${state.currentTopicId}/generate-titles`, { method: 'POST' });
    toast(`标题生成任务已提交 (#${task.id})`);
    pollTask(task.id, () => loadTitles(state.currentTopicId));
  } catch (err) {
    toast(err.message, 'error');
  }
}

async function loadTitles(topicId) {
  try {
    const titles = await api(`/api/v1/topics/${topicId}/titles`);
    const list = document.getElementById('title-list');
    list.innerHTML = titles.length
      ? titles.map(t => `
        <li data-id="${t.id}">
          <div>
            <div>${escapeHtml(t.text)}</div>
            <div class="meta">得分: ${t.score ?? '-'} · ${t.is_selected ? '已选中' : '未选中'}</div>
          </div>
          <button class="select-title">生成文章</button>
        </li>
      `).join('')
      : '<li class="meta">暂无标题，点击上方按钮生成</li>';
    document.getElementById('article-panel').style.display = titles.length ? 'block' : 'none';
    list.querySelectorAll('.select-title').forEach(btn => {
      btn.addEventListener('click', e => {
        e.stopPropagation();
        state.currentTitleId = Number(btn.closest('li').dataset.id);
        document.getElementById('generate-article-btn').textContent = `为标题 #${state.currentTitleId} 生成文章`;
      });
    });
  } catch (err) {
    toast(err.message, 'error');
  }
}

// ------------------------- 文章 -------------------------
async function generateArticle() {
  if (!state.currentTitleId) return toast('请先在标题列表点击“生成文章”选择标题', 'error');
  const useRag = document.getElementById('use-rag').checked;
  const ragQuery = document.getElementById('rag-query').value.trim();
  const payload = { title_id: state.currentTitleId, use_rag: useRag };
  if (useRag) {
    payload.rag_query = ragQuery || undefined;
    payload.rag_top_k = 5;
  }
  try {
    const task = await api('/api/v1/articles/generate', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    toast(`文章生成任务已提交 (#${task.id})`);
    pollTask(task.id, () => loadTopicArticles(state.currentTopicId));
  } catch (err) {
    toast(err.message, 'error');
  }
}

async function loadTopicArticles(topicId) {
  try {
    // 通过标题列表再取文章比较繁琐，这里只刷新主题下第一篇文章
    const titles = await api(`/api/v1/topics/${topicId}/titles`);
    const container = document.getElementById('article-list');
    container.innerHTML = '';
    for (const t of titles.filter(t => t.is_selected)) {
      const articles = await api(`/api/v1/articles/title/${t.id}`);
      articles.forEach(a => {
        const li = document.createElement('li');
        li.dataset.id = a.id;
        li.innerHTML = `<div><div>文章 #${a.id}</div><div class="meta">状态: ${a.status}</div></div><button class="view-article">查看</button>`;
        li.querySelector('.view-article').addEventListener('click', e => {
          e.stopPropagation();
          viewArticle(a);
        });
        container.appendChild(li);
      });
    }
    if (!container.innerHTML) container.innerHTML = '<li class="meta">暂无文章</li>';
  } catch (err) {
    toast(err.message, 'error');
  }
}

async function loadArticles() {
  try {
    // 拉取所有主题，再拉每个主题下的文章（简单实现）
    const topics = await api('/api/v1/topics?limit=100');
    const container = document.getElementById('all-article-list');
    container.innerHTML = '';
    for (const t of topics) {
      const titles = await api(`/api/v1/topics/${t.id}/titles`);
      for (const title of titles) {
        const articles = await api(`/api/v1/articles/title/${title.id}`);
        articles.forEach(a => {
          const li = document.createElement('li');
          li.dataset.id = a.id;
          li.innerHTML = `<div><div>${escapeHtml(title.text)}</div><div class="meta">主题: ${escapeHtml(t.title)} · 状态: ${a.status}</div></div><button class="view-article">查看</button>`;
          li.querySelector('.view-article').addEventListener('click', e => {
            e.stopPropagation();
            viewArticle(a);
          });
          container.appendChild(li);
        });
      }
    }
    if (!container.innerHTML) container.innerHTML = '<li class="meta">暂无文章</li>';
  } catch (err) {
    toast(err.message, 'error');
  }
}

async function viewArticle(article) {
  state.currentArticleId = article.id;
  document.getElementById('article-detail').style.display = 'block';
  document.getElementById('article-detail-title').textContent = `文章 #${article.id}`;
  document.getElementById('article-detail-content').textContent = article.content || '（内容为空）';
  document.getElementById('cover-result').innerHTML = '';
  document.getElementById('publish-result').innerHTML = '';
}

// ------------------------- 封面与发布 -------------------------
async function generateCover() {
  if (!state.currentArticleId) return toast('请先查看文章', 'error');
  try {
    const data = await api('/api/v1/articles/generate-cover', {
      method: 'POST',
      body: JSON.stringify({ article_id: state.currentArticleId, prompt: '', width: 512, height: 512 }),
    });
    document.getElementById('cover-result').innerHTML = `
      <p>封面已生成：<a href="${data.url}" target="_blank">${data.url}</a></p>
      <img src="${data.url}" style="max-width:100%;border-radius:8px;" />
    `;
  } catch (err) {
    toast(err.message, 'error');
  }
}

async function publishArticle() {
  if (!state.currentArticleId) return toast('请先查看文章', 'error');
  try {
    const task = await api('/api/v1/publish', {
      method: 'POST',
      body: JSON.stringify({ article_id: state.currentArticleId, platform: 'xiaohongshu' }),
    });
    toast(`发布任务已提交 (#${task.id})`);
    pollTask(task.id, () => {
      document.getElementById('publish-result').innerHTML = '<p class="success">发布流程已完成，请到“任务队列”查看结果</p>';
    });
  } catch (err) {
    toast(err.message, 'error');
  }
}

// ------------------------- RAG -------------------------
async function ingestMaterial(e) {
  e.preventDefault();
  const materialId = Number(document.getElementById('ingest-material-id').value);
  const text = document.getElementById('ingest-text').value;
  const tags = document.getElementById('ingest-tags').value.split(',').map(s => s.trim()).filter(Boolean);
  try {
    const result = await api(`/api/v1/rag/ingest/${materialId}`, {
      method: 'POST',
      body: JSON.stringify({ text, metadata: { tags } }),
    });
    toast(`入库成功: ${result.message || 'ok'}`);
  } catch (err) {
    toast(err.message, 'error');
  }
}

async function searchRag(e) {
  e.preventDefault();
  const q = document.getElementById('search-q').value.trim();
  const topK = document.getElementById('search-topk').value;
  try {
    const data = await api(`/api/v1/rag/search?q=${encodeURIComponent(q)}&top_k=${topK}`);
    const box = document.getElementById('search-result');
    box.innerHTML = data.contexts.length
      ? data.contexts.map((c, i) => `
        <div style="margin-bottom:12px;">
          <strong>#${i + 1} 相似度 ${(c.score ?? c.distance ?? '-').toString().slice(0, 6)}</strong>
          <p>${escapeHtml(c.text || c.content || JSON.stringify(c))}</p>
        </div>
      `).join('')
      : '<p>未检索到结果</p>';
  } catch (err) {
    toast(err.message, 'error');
  }
}

// ------------------------- 任务 -------------------------
async function loadTasks() {
  try {
    // 后端目前没有列出所有任务的接口，这里通过轮询展示最近手动触发过的任务
    const box = document.getElementById('task-list');
    if (!state.taskIds || state.taskIds.length === 0) {
      box.innerHTML = '<li class="meta">暂无任务，请从主题或文章页面触发</li>';
      return;
    }
    box.innerHTML = '';
    for (const id of state.taskIds.slice().reverse()) {
      try {
        const t = await api(`/api/v1/tasks/${id}`);
        const li = document.createElement('li');
        li.innerHTML = `
          <div>
            <div>任务 #${t.id} · ${t.type}</div>
            <div class="meta">状态: ${t.status} · 尝试: ${t.attempts}/${t.max_attempts} · ${formatTime(t.updated_at)}</div>
          </div>
        `;
        box.appendChild(li);
      } catch (err) {
        console.warn(err);
      }
    }
  } catch (err) {
    toast(err.message, 'error');
  }
}

state.taskIds = JSON.parse(localStorage.getItem('bz_task_ids') || '[]');
function rememberTask(id) {
  if (!state.taskIds.includes(id)) {
    state.taskIds.push(id);
    localStorage.setItem('bz_task_ids', JSON.stringify(state.taskIds));
  }
}

async function pollTask(taskId, onDone) {
  rememberTask(taskId);
  let attempts = 0;
  const max = 60;
  const interval = setInterval(async () => {
    try {
      const t = await api(`/api/v1/tasks/${taskId}`);
      if (t.status === 'success' || t.status === 'failed') {
        clearInterval(interval);
        toast(`任务 #${taskId} ${t.status === 'success' ? '完成' : '失败'}`);
        if (t.status === 'success' && onDone) onDone();
      }
    } catch (err) {
      console.warn('poll error', err);
    }
    if (++attempts > max) clearInterval(interval);
  }, 2000);
}

// ------------------------- 事件绑定 -------------------------
document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('login-form').addEventListener('submit', login);
  document.getElementById('register-form').addEventListener('submit', register);
  document.getElementById('logout-btn').addEventListener('click', logout);

  document.querySelectorAll('#auth-section .tab').forEach(t => {
    t.addEventListener('click', () => switchTab(t.dataset.tab));
  });

  document.querySelectorAll('.nav-item').forEach(n => {
    n.addEventListener('click', () => switchPage(n.dataset.page));
  });

  document.getElementById('topic-form').addEventListener('submit', createTopic);
  document.getElementById('generate-titles-btn').addEventListener('click', generateTitles);
  document.getElementById('generate-article-btn').addEventListener('click', generateArticle);
  document.getElementById('generate-cover-btn').addEventListener('click', generateCover);
  document.getElementById('publish-btn').addEventListener('click', publishArticle);
  document.getElementById('ingest-form').addEventListener('submit', ingestMaterial);
  document.getElementById('search-form').addEventListener('submit', searchRag);
  document.getElementById('refresh-tasks-btn').addEventListener('click', loadTasks);

  initApp();
});
