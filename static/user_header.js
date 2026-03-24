// 获取当前登录用户并显示
fetch('/api/current_user')
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            const roleText = data.user.role === 'admin' ? '管理员' : '用户';
            document.getElementById('currentUser').textContent = `${data.user.username} (${roleText})`;
        } else {
            // 未登录，跳转登录页
            window.location.href = '/login';
        }
    })
    .catch(() => {
        window.location.href = '/login';
    });
