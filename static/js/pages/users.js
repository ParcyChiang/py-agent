// users.js - 用户管理页面

function loadUsers() {
    document.getElementById('usersContent').innerHTML = '<div class="loading">加载中...</div>';
    fetch('/api/users')
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                renderUsers(data.users);
            } else {
                document.getElementById('usersContent').innerHTML =
                    '<div class="no-users">无权限查看用户列表</div>';
            }
        })
        .catch(() => {
            document.getElementById('usersContent').innerHTML =
                '<div class="no-users">加载失败，请重试</div>';
        });
}

function renderUsers(users) {
    if (!users || users.length === 0) {
        document.getElementById('usersContent').innerHTML =
            '<div class="no-users">暂无用户</div>';
        return;
    }

    let html = `
        <table class="users-table">
            <thead>
                <tr>
                    <th>ID</th>
                    <th>用户名</th>
                    <th>角色</th>
                    <th>注册时间</th>
                    <th>操作</th>
                </tr>
            </thead>
            <tbody>
    `;

    users.forEach(user => {
        const roleClass = user.role === 'admin' ? 'admin' : 'user';
        const roleText = user.role === 'admin' ? '管理员' : '普通用户';
        const createdAt = new Date(user.created_at).toLocaleString('zh-CN');
        const isAdmin = user.role === 'admin';
        const deleteBtn = isAdmin
            ? '<button class="btn-delete" disabled>不可删除</button>'
            : `<button class="btn-delete" onclick="deleteUser(${user.id}, '${user.username}')">删除</button>`;

        html += `
            <tr>
                <td>${user.id}</td>
                <td>${user.username}</td>
                <td><span class="user-role ${roleClass}">${roleText}</span></td>
                <td class="log-time">${createdAt}</td>
                <td>${deleteBtn}</td>
            </tr>
        `;
    });

    html += '</tbody></table>';
    document.getElementById('usersContent').innerHTML = html;
}

function deleteUser(userId, username) {
    if (!confirm(`确定要删除用户 "${username}" 吗？此操作不可恢复。`)) {
        return;
    }

    fetch(`/api/users/${userId}`, { method: 'DELETE' })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                showToast('用户已删除', 'success');
                loadUsers();
            } else {
                showToast(data.message || '删除失败', 'error');
            }
        })
        .catch(() => {
            showToast('删除失败，请重试', 'error');
        });
}

document.getElementById('refreshBtn').addEventListener('click', loadUsers);

// 初始加载
loadUsers();
