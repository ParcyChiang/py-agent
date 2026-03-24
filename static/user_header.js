// 获取当前登录用户并显示
fetch('/api/current_user')
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            const roleText = data.user.role === 'admin' ? '管理员' : '用户';
            document.getElementById('currentUser').textContent = `${data.user.username} (${roleText})`;

            // 如果是管理员，添加查看日志和用户管理按钮
            if (data.user.role === 'admin') {
                const userHeader = document.querySelector('.user-header');
                if (userHeader) {
                    const logsBtn = document.createElement('a');
                    logsBtn.className = 'btn-logs';
                    logsBtn.href = '/page/logs';
                    logsBtn.textContent = '日志';

                    const usersBtn = document.createElement('a');
                    usersBtn.className = 'btn-user';
                    usersBtn.href = '/page/users';
                    usersBtn.textContent = '用户';

                    // 在退出按钮前插入
                    const logoutBtn = userHeader.querySelector('.btn-logout');
                    userHeader.insertBefore(logsBtn, logoutBtn);
                    userHeader.insertBefore(usersBtn, logoutBtn);
                }
            }
        } else {
            // 未登录，跳转登录页
            window.location.href = '/login';
        }
    })
    .catch(() => {
        window.location.href = '/login';
    });
