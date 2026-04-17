// new_dashboard.js - 实时监控仪表板页面

// 全局变量
let currentPage = 1;
const pageSize = 10;
let sortField = 'time';
let sortDirection = 'desc';
let currentCardIndex = 0;
let totalCardGroups = 1;
let chartInterval;
let metricsInterval;
let tableInterval;
let timeGranularity = 'realtime';

// 从API获取趋势数据
const fetchTrendData = async () => {
    try {
        const response = await fetch(`/api/dashboard/trend?granularity=${timeGranularity}`);
        const result = await response.json();
        if (result.success) {
            return result.data;
        } else {
            console.error('获取趋势数据失败:', result.message);
            return [];
        }
    } catch (error) {
        console.error('获取趋势数据出错:', error);
        return [];
    }
};

// 从API获取指标数据
const fetchMetricsData = async () => {
    try {
        const response = await fetch('/api/dashboard/metrics');
        const result = await response.json();
        if (result.success) {
            return result.data;
        } else {
            console.error('获取指标数据失败:', result.message);
            return [];
        }
    } catch (error) {
        console.error('获取指标数据出错:', error);
        return [];
    }
};

// 从API获取表格数据
const fetchTableData = async () => {
    try {
        const statusFilter = document.getElementById('statusFilter').value;
        const searchTerm = document.getElementById('searchInput').value;

        const params = new URLSearchParams({
            page: currentPage,
            pageSize: pageSize,
            status: statusFilter,
            search: searchTerm,
            sortField: sortField,
            sortDirection: sortDirection
        });

        const response = await fetch(`/api/dashboard/table?${params}`);
        const result = await response.json();
        if (result.success) {
            return result;
        } else {
            console.error('获取表格数据失败:', result.message);
            return { data: [], total: 0 };
        }
    } catch (error) {
        console.error('获取表格数据出错:', error);
        return { data: [], total: 0 };
    }
};

// 初始化图表
const initChart = () => {
    const chartDom = document.getElementById('trendChart');
    const myChart = echarts.init(chartDom);

    const updateChart = async () => {
        const chartData = await fetchTrendData();

        if (chartData.length > 0) {
            const option = {
                title: {
                    text: '实时数据趋势',
                    left: 'center'
                },
                tooltip: {
                    trigger: 'axis'
                },
                xAxis: {
                    type: 'category',
                    data: chartData.map(d => d.time),
                    axisLine: {
                        lineStyle: {
                            color: '#333'
                        }
                    },
                    axisLabel: {
                        color: '#333',
                        rotate: 45
                    }
                },
                yAxis: {
                    type: 'value',
                    axisLine: {
                        lineStyle: {
                            color: '#333'
                        }
                    },
                    axisLabel: {
                        color: '#333'
                    }
                },
                series: [{
                    type: 'line',
                    data: chartData.map(d => d.value),
                    smooth: true,
                    areaStyle: {
                        opacity: 0.3
                    },
                    itemStyle: {
                        color: '#0d6efd'
                    }
                }]
            };

            myChart.setOption(option);
        }

        document.getElementById('chartRefresh').textContent = '最后更新：' + new Date().toLocaleString();
    };

    updateChart();
    chartInterval = setInterval(updateChart, 1000);

    window.addEventListener('resize', () => {
        myChart.resize();
    });

    document.getElementById('timeGranularity').addEventListener('change', (e) => {
        timeGranularity = e.target.value;
        updateChart();
    });
};

// 初始化指标卡片
const initMetrics = () => {
    const updateMetrics = async () => {
        const metrics = await fetchMetricsData();

        if (metrics.length > 0) {
            const metricCardsContainer = document.getElementById('metricCards');
            metricCardsContainer.innerHTML = '';

            metrics.forEach(metric => {
                const card = document.createElement('div');
                card.className = 'metric-card';
                card.innerHTML = `
                    <div class="metric-name">${metric.name}</div>
                    <div class="metric-value">${metric.value}</div>
                    <div class="metric-trend ${metric.trendUp ? 'trend-up' : 'trend-down'}">
                        ${metric.trendUp ? '↑' : '↓'} ${metric.trend}%
                    </div>
                `;
                metricCardsContainer.appendChild(card);
            });

            totalCardGroups = Math.ceil(metrics.length / 4);
            if (totalCardGroups < 1) totalCardGroups = 1;
            currentCardIndex = 0;
        }

        document.getElementById('metricsRefresh').textContent = '最后更新：' + new Date().toLocaleString();
    };

    updateMetrics();
    metricsInterval = setInterval(updateMetrics, 5000);

    document.getElementById('prevCard').addEventListener('click', () => {
        currentCardIndex = (currentCardIndex - 1 + totalCardGroups) % totalCardGroups;
        updateCardPosition();
    });

    document.getElementById('nextCard').addEventListener('click', () => {
        currentCardIndex = (currentCardIndex + 1) % totalCardGroups;
        updateCardPosition();
    });

    setInterval(() => {
        currentCardIndex = (currentCardIndex + 1) % totalCardGroups;
        updateCardPosition();
    }, 5000);
};

// 更新卡片位置
const updateCardPosition = () => {
    const metricCardsContainer = document.getElementById('metricCards');
    metricCardsContainer.style.transform = `translateX(-${currentCardIndex * 100}%)`;
};

// 初始化数据表格
const initTable = () => {
    const updateTable = async () => {
        await renderTable();
        document.getElementById('tableRefresh').textContent = '最后更新：' + new Date().toLocaleString();
    };

    updateTable();
    tableInterval = setInterval(updateTable, 10000);

    // 排序
    document.querySelectorAll('th[data-sort]').forEach(th => {
        th.addEventListener('click', () => {
            const field = th.getAttribute('data-sort');
            if (sortField === field) {
                sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
            } else {
                sortField = field;
                sortDirection = 'asc';
            }
            currentPage = 1; // 重置到第一页
            renderTable();
        });
    });

    // 筛选
    document.getElementById('statusFilter').addEventListener('change', () => {
        currentPage = 1; // 重置到第一页
        renderTable();
    });
    document.getElementById('searchInput').addEventListener('input', () => {
        currentPage = 1; // 重置到第一页
        renderTable();
    });
};

// 渲染表格
const renderTable = async () => {
    const result = await fetchTableData();
    const tableData = result.data || [];
    const total = result.total || 0;

    // 渲染表格数据
    const tableBody = document.getElementById('dataTableBody');
    tableBody.innerHTML = '';

    if (tableData.length === 0) {
        const row = document.createElement('tr');
        row.innerHTML = `<td colspan="7" class="text-center">暂无数据</td>`;
        tableBody.appendChild(row);
    } else {
        tableData.forEach(item => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${item.orderId}</td>
                <td>${item.company}</td>
                <td>
                    <span class="badge ${item.status === '已交付' ? 'bg-success' : item.status === '运输中' ? 'bg-warning' : 'bg-secondary'}">
                        ${item.status}
                    </span>
                </td>
                <td>${item.origin}</td>
                <td>${item.destination}</td>
                <td>${item.time}</td>
                <td>¥${item.value}</td>
            `;
            tableBody.appendChild(row);
        });
    }

    // 渲染分页
    const pagination = document.getElementById('tablePagination');
    pagination.innerHTML = '';

    const totalPages = Math.ceil(total / pageSize);
    if (totalPages > 0) {
        // 分页容器
        const paginationContainer = document.createElement('div');
        paginationContainer.className = 'd-flex justify-content-between align-items-center w-100';

        // 左侧：总记录数
        const totalInfo = document.createElement('div');
        totalInfo.className = 'total-info';
        totalInfo.textContent = `共 ${total} 条记录`;
        paginationContainer.appendChild(totalInfo);

        // 中间：页码按钮
        const pageButtons = document.createElement('div');
        pageButtons.className = 'page-buttons';

        // 计算显示的页码范围
        let startPage = Math.max(1, currentPage - 2);
        let endPage = Math.min(totalPages, startPage + 5);

        // 调整起始页码，确保显示6个页码
        if (endPage - startPage < 5) {
            startPage = Math.max(1, endPage - 5);
        }

        // 上一页按钮
        if (currentPage > 1) {
            const prevBtn = document.createElement('button');
            prevBtn.className = 'pagination-btn';
            prevBtn.textContent = '上一页';
            prevBtn.addEventListener('click', () => {
                currentPage = Math.max(1, currentPage - 1);
                renderTable();
            });
            pageButtons.appendChild(prevBtn);
        }

        // 页码按钮
        for (let i = startPage; i <= endPage; i++) {
            const btn = document.createElement('button');
            btn.className = `pagination-btn ${i === currentPage ? 'active' : ''}`;
            btn.textContent = i;
            btn.addEventListener('click', () => {
                currentPage = i;
                renderTable();
            });
            pageButtons.appendChild(btn);
        }

        // 下一页按钮
        if (currentPage < totalPages) {
            const nextBtn = document.createElement('button');
            nextBtn.className = 'pagination-btn';
            nextBtn.textContent = '下一页';
            nextBtn.addEventListener('click', () => {
                currentPage = Math.min(totalPages, currentPage + 1);
                renderTable();
            });
            pageButtons.appendChild(nextBtn);
        }

        paginationContainer.appendChild(pageButtons);

        // 右侧：跳转到指定页
        const jumpToPage = document.createElement('div');
        jumpToPage.className = 'jump-to-page';
        jumpToPage.innerHTML = `
            <span>前往第</span>
            <input type="number" id="jumpPageInput" min="1" max="${totalPages}" value="${currentPage}" style="width: 60px; margin: 0 5px; padding: 2px 4px; border: 1px solid #dee2e6; border-radius: 4px;">
            <span>页</span>
            <button id="jumpPageBtn" class="pagination-btn" style="margin-left: 5px;">确定</button>
        `;
        paginationContainer.appendChild(jumpToPage);

        pagination.appendChild(paginationContainer);

        // 添加跳转按钮事件
        document.getElementById('jumpPageBtn').addEventListener('click', () => {
            const jumpPage = parseInt(document.getElementById('jumpPageInput').value);
            if (jumpPage >= 1 && jumpPage <= totalPages) {
                currentPage = jumpPage;
                renderTable();
            }
        });

        // 添加回车键事件
        document.getElementById('jumpPageInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                document.getElementById('jumpPageBtn').click();
            }
        });
    }
};

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    initChart();
    initMetrics();
    initTable();
});

// 清理定时器
window.addEventListener('beforeunload', () => {
    clearInterval(chartInterval);
    clearInterval(metricsInterval);
    clearInterval(tableInterval);
});
