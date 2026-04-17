// logs.js - 操作日志页面

function loadLogs() {
    document.getElementById('logsContent').innerHTML = '<div class="loading">加载中...</div>';
    fetch('/api/logs')
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                renderLogs(data.logs);
            } else {
                document.getElementById('logsContent').innerHTML =
                    '<div class="no-logs">无权限查看日志或加载失败</div>';
            }
        })
        .catch(() => {
            document.getElementById('logsContent').innerHTML =
                '<div class="no-logs">加载失败，请重试</div>';
        });
}

function renderLogs(logs) {
    if (!logs || logs.length === 0) {
        document.getElementById('logsContent').innerHTML =
            '<div class="no-logs">暂无日志记录</div>';
        return;
    }

    let html = `
        <table class="logs-table">
            <thead>
                <tr>
                    <th>时间</th>
                    <th>用户</th>
                    <th>操作</th>
                    <th>详情</th>
                    <th>IP</th>
                </tr>
            </thead>
            <tbody>
    `;

    logs.forEach(log => {
        const time = new Date(log.timestamp).toLocaleString('zh-CN');
        html += `
            <tr>
                <td class="log-time">${time}</td>
                <td class="log-user">${log.username || '系统'}</td>
                <td><span class="log-action">${log.action}</span></td>
                <td class="log-detail" title="${log.detail || ''}">${log.detail || '-'}</td>
                <td class="log-ip">${log.ip_address || '-'}</td>
            </tr>
        `;
    });

    html += '</tbody></table>';
    document.getElementById('logsContent').innerHTML = html;
}

document.getElementById('refreshBtn').addEventListener('click', loadLogs);

// 初始加载
loadLogs();
