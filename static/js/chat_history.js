// chat_history.js - 对话历史侧边栏组件

class ChatHistoryManager {
    constructor(options = {}) {
        this.pageName = options.page || '';  // 当前页面标识
        this.currentFilter = '';  // 筛选条件，初始化为空表示"全部"
        this.onLoadChat = options.onLoadChat || null;
        this.init();
    }

    init() {
        this.createSidebar();
        this.bindEvents();
        // 初始化时不加载，等打开侧边栏时再加载
    }

    createSidebar() {
        // 创建遮罩层
        this.overlay = document.createElement('div');
        this.overlay.className = 'chat-history-overlay';
        document.body.appendChild(this.overlay);

        // 创建侧边栏
        this.sidebar = document.createElement('div');
        this.sidebar.className = 'chat-history-sidebar';
        this.sidebar.innerHTML = `
            <div class="chat-history-header">
                <h3>对话历史</h3>
                <button class="chat-history-close" title="关闭">&times;</button>
            </div>
            <div class="chat-history-search">
                <input type="text" placeholder="搜索对话历史..." class="chat-search-input">
            </div>
            <div class="chat-history-filters">
                <span class="filter-tag active" data-page="">全部</span>
                <span class="filter-tag" data-page="code_generator">代码生成</span>
                <span class="filter-tag" data-page="analysis_report">运营报告</span>
                <span class="filter-tag" data-page="compare">物流对比</span>
            </div>
            <div class="chat-history-list">
                <div class="chat-history-loading" style="text-align:center;padding:20px;color:rgba(255,255,255,0.5);">
                    加载中...
                </div>
            </div>
        `;
        document.body.appendChild(this.sidebar);

        // 创建历史按钮容器 - 左上角悬浮样式
        this.historyContainer = document.createElement('div');
        this.historyContainer.className = 'chat-history-container';

        this.toggleBtn = document.createElement('button');
        this.toggleBtn.className = 'chat-history-toggle';
        this.toggleBtn.innerHTML = '&#128172; 对话历史';
        this.toggleBtn.title = '对话历史';

        this.historyContainer.appendChild(this.toggleBtn);
        document.body.appendChild(this.historyContainer);

        // 缓存DOM引用
        this.listContainer = this.sidebar.querySelector('.chat-history-list');
        this.searchInput = this.sidebar.querySelector('.chat-search-input');
        this.closeBtn = this.sidebar.querySelector('.chat-history-close');
        this.filterTags = this.sidebar.querySelectorAll('.filter-tag');
    }

    bindEvents() {
        // 切换按钮
        this.toggleBtn.addEventListener('click', () => this.toggle());

        // 关闭按钮
        this.closeBtn.addEventListener('click', () => this.close());

        // 遮罩层点击
        this.overlay.addEventListener('click', () => this.close());

        // 搜索
        let searchTimeout;
        this.searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                this.search(e.target.value);
            }, 300);
        });

        // 筛选标签
        this.filterTags.forEach(tag => {
            tag.addEventListener('click', () => {
                this.filterTags.forEach(t => t.classList.remove('active'));
                tag.classList.add('active');
                this.currentFilter = tag.dataset.page;
                this.loadChats();
            });
        });
    }

    toggle() {
        this.sidebar.classList.toggle('open');
        this.overlay.classList.toggle('visible');
        if (this.sidebar.classList.contains('open')) {
            this.loadChats();  // 打开时加载
        }
    }

    open() {
        this.sidebar.classList.add('open');
        this.overlay.classList.add('visible');
        this.loadChats();  // 打开时加载
    }

    close() {
        this.sidebar.classList.remove('open');
        this.overlay.classList.remove('visible');
    }

    async loadChats() {
        try {
            const params = new URLSearchParams();
            if (this.currentFilter) {
                params.append('page', this.currentFilter);
            }
            params.append('limit', '50');

            const response = await fetch(`/api/chat_history/list?${params}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const result = await response.json();
            if (result.success && result.chats) {
                this.renderChats(result.chats || []);
            } else if (result.success && result.data) {
                this.renderChats(result.data.chats || []);
            } else {
                console.error('[ChatHistory] 加载失败:', result.message);
                this.renderEmpty('加载失败，请重试');
            }
        } catch (error) {
            console.error('加载对话历史失败:', error);
            this.renderEmpty('加载失败，请重试');
        }
    }

    async search(keyword) {
        if (!keyword.trim()) {
            this.loadChats();
            return;
        }

        try {
            const params = new URLSearchParams({ keyword, limit: '20' });
            const response = await fetch(`/api/chat_history/search?${params}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const result = await response.json();
            if (result.success && result.chats) {
                this.renderChats(result.chats || []);
            } else if (result.success && result.data) {
                this.renderChats(result.data.chats || []);
            }
        } catch (error) {
            console.error('搜索对话历史失败:', error);
        }
    }

    renderChats(chats) {
        if (!chats || chats.length === 0) {
            this.renderEmpty('暂无对话历史');
            return;
        }

        const pageNames = {
            'code_generator': '代码生成',
            'analysis_report': '运营报告',
            'compare': '物流对比'
        };

        this.listContainer.innerHTML = chats.map(chat => `
            <div class="chat-history-item" data-id="${chat.id}">
                <div class="chat-item-header">
                    <span class="chat-item-page ${chat.page}">${pageNames[chat.page] || chat.page}</span>
                    <button class="chat-item-delete" data-id="${chat.id}" title="删除">&#128465;</button>
                </div>
                <div class="chat-item-title">${this.escapeHtml(chat.title || '无标题')}</div>
                <div class="chat-item-preview">${this.escapeHtml(chat.user_input || '')}</div>
                <div class="chat-item-time">${this.formatTime(chat.created_at)}</div>
            </div>
        `).join('');

        // 绑定点击事件
        this.listContainer.querySelectorAll('.chat-history-item').forEach(item => {
            item.addEventListener('click', (e) => {
                if (e.target.classList.contains('chat-item-delete')) {
                    e.stopPropagation();
                    this.deleteChat(e.target.dataset.id);
                    return;
                }
                this.loadChatDetail(item.dataset.id);
            });
        });
    }

    renderEmpty(message) {
        this.listContainer.innerHTML = `
            <div class="chat-history-empty">
                <div class="chat-history-empty-icon">&#128172;</div>
                <div class="chat-history-empty-text">${message}</div>
            </div>
        `;
    }

    async loadChatDetail(chatId) {
        try {
            const response = await fetch(`/api/chat_history/get/${chatId}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const result = await response.json();
            if (result.success) {
                const chat = result.chat || (result.data && result.data.chat);
                if (chat) {
                    // 将对话数据存储到 sessionStorage
                    sessionStorage.setItem('chat_to_load', JSON.stringify(chat));
                    // 跳转到对应页面
                    const pageUrls = {
                        'code_generator': '/page/code_generator',
                        'analysis_report': '/page/analysis_report',
                        'compare': '/page/compare'
                    };
                    const url = pageUrls[chat.page] || '/page/code_generator';
                    window.location.href = url;
                }
            }
        } catch (error) {
            console.error('加载对话详情失败:', error);
        }
    }

    async deleteChat(chatId) {
        if (!confirm('确定要删除这条对话记录吗？')) {
            return;
        }

        try {
            const response = await fetch(`/api/chat_history/delete/${chatId}`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const result = await response.json();
            if (result.success) {
                this.loadChats();
            } else {
                alert(result.message || '删除失败');
            }
        } catch (error) {
            console.error('删除对话失败:', error);
            alert('删除失败，请重试');
        }
    }

    // 保存对话到历史
    async saveChat(page, title, userInput, aiResponse) {
        try {
            const response = await fetch('/api/chat_history/create', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    page: page,
                    title: title,
                    user_input: userInput,
                    ai_response: aiResponse
                })
            });

            const result = await response.json();
            if (result.success) {
                // 刷新列表
                this.loadChats();
                return result.id;
            }
        } catch (error) {
            console.error('[ChatHistory] 保存对话失败:', error);
        }
        return null;
    }

    formatTime(dateStr) {
        if (!dateStr) return '未知时间';
        // 处理多种日期格式
        let date;
        try {
            // 先尝试直接解析
            date = new Date(dateStr);
            if (isNaN(date.getTime())) {
                // 如果解析失败，尝试替换GMT格式
                const fixedStr = dateStr.replace(/(\d{2}), (\d{2}) (\w{3}) (\d{4}) (\d{2}):(\d{2}):(\d{2}) GMT/, function(m, d1, d2, mon, y, h, min, s) {
                    const months = {'Jan':0,'Feb':1,'Mar':2,'Apr':3,'May':4,'Jun':5,'Jul':6,'Aug':7,'Sep':8,'Oct':9,'Nov':10,'Dec':11};
                    return `${y}-${(months[mon]+1).toString().padStart(2,'0')}-${d2}T${h}:${min}:${s}Z`;
                });
                date = new Date(fixedStr);
            }
        } catch (e) {
            return '时间格式错误';
        }

        if (isNaN(date.getTime())) {
            return '时间格式错误';
        }

        // 转为本地时间显示
        const now = new Date();
        const diff = now - date;

        // 如果是未来时间或差异太大，显示具体时间
        if (diff < 0 || diff > 86400000 * 30) {
            return `${date.getMonth() + 1}/${date.getDate()} ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;
        }

        // 一天内显示相对时间
        if (Math.abs(diff) < 60000) {
            return '刚刚';
        }
        if (Math.abs(diff) < 3600000) {
            return Math.floor(Math.abs(diff) / 60000) + '分钟前';
        }
        if (Math.abs(diff) < 86400000) {
            return Math.floor(Math.abs(diff) / 3600000) + '小时前';
        }

        // 超过一天显示日期
        return `${date.getMonth() + 1}/${date.getDate()} ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;
    }

    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // 更新当前页面上下文（切换页面时调用）
    setPage(page) {
        this.currentPage = page;
    }

    // 更新角标数量
    updateBadge(count) {
        let badge = this.toggleBtn.querySelector('.badge');
        if (count > 0) {
            if (!badge) {
                badge = document.createElement('span');
                badge.className = 'badge';
                this.toggleBtn.appendChild(badge);
            }
            badge.textContent = count > 99 ? '99+' : count;
        } else if (badge) {
            badge.remove();
        }
    }
}

// 导出全局函数，供各页面使用
window.ChatHistoryManager = ChatHistoryManager;
