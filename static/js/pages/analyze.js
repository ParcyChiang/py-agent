// analyze.js - 运营分析页面

let statusChart;

function createStatusChart(statusData) {
    const ctx = document.getElementById('statusChart').getContext('2d');
    if (statusChart) statusChart.destroy();

    statusChart = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: Object.keys(statusData),
            datasets: [{
                data: Object.values(statusData),
                backgroundColor: [
                    '#FF6384',
                    '#36A2EB',
                    '#FFCE56',
                    '#4BC0C0',
                    '#9966FF',
                    '#FF9F40'
                ]
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

function display3DCharts(chartData) {
    // 显示三维曲面图
    if (chartData.surface_3d) {
        document.getElementById('surface3D').src = 'data:image/png;base64,' + chartData.surface_3d;
    } else {
        document.getElementById('surface3D').src = '';
        document.getElementById('surface3D').alt = '暂无三维曲面图数据';
    }

    // 显示三维散点图
    if (chartData.scatter_3d) {
        document.getElementById('scatter3D').src = 'data:image/png;base64,' + chartData.scatter_3d;
    } else {
        document.getElementById('scatter3D').src = '';
        document.getElementById('scatter3D').alt = '暂无三维散点图数据';
    }

    // 显示三维线框图
    if (chartData.wireframe_3d) {
        document.getElementById('wireframe3D').src = 'data:image/png;base64,' + chartData.wireframe_3d;
    } else {
        document.getElementById('wireframe3D').src = '';
        document.getElementById('wireframe3D').alt = '暂无三维线框图数据';
    }
}

function displayDataInfo(dataInfo) {
    const dataInfoDiv = document.getElementById('dataInfo');
    if (!dataInfo) {
        dataInfoDiv.innerHTML = '<p>暂无数据信息</p>';
        return;
    }

    let html = '<h4>三维数据信息</h4>';

    if (dataInfo.error) {
        html += `<div style="color: red; padding: 10px; background: #ffe6e6; border-radius: 4px; margin: 10px 0;">错误: ${dataInfo.error}</div>`;
    }

    html += '<div style="margin: 10px 0;">';
    html += '<strong>城市列表:</strong> ';
    html += (dataInfo.cities || []).join(', ') || '无';
    html += '</div>';

    html += '<div style="margin: 10px 0;">';
    html += '<strong>时间范围:</strong> ';
    html += (dataInfo.time_labels || []).join(', ') || '无';
    html += '</div>';

    html += '<div style="margin: 10px 0;">';
    html += '<strong>状态类型:</strong> ';
    html += (dataInfo.statuses || []).join(', ') || '无';
    html += '</div>';

    if (dataInfo.surface_data) {
        html += '<h5 style="margin-top: 15px;">数据矩阵预览</h5>';
        html += '<div style="font-size: 12px; max-height: 200px; overflow-y: auto;">';
        for (const [status, matrix] of Object.entries(dataInfo.surface_data)) {
            html += `<div style="margin: 5px 0;"><strong>${status}:</strong> `;
            html += `矩阵大小: ${matrix.length} x ${matrix[0] ? matrix[0].length : 0}`;
            html += `, 最大值: ${Math.max(...matrix.flat())}`;
            html += `, 总和: ${matrix.flat().reduce((a, b) => a + b, 0)}</div>`;
        }
        html += '</div>';
    }

    dataInfoDiv.innerHTML = html;
}

$(function(){
    // 页面加载时从缓存恢复数据
    const savedAnalysis = cacheGet('analyze_data');
    if (savedAnalysis) {
        try {
            $('#statsContent').html(savedAnalysis.statsContent);
            if (savedAnalysis.statusDistribution) {
                createStatusChart(savedAnalysis.statusDistribution);
            }
            if (savedAnalysis.chartData) {
                display3DCharts(savedAnalysis.chartData);
            }
            if (savedAnalysis.dataInfo) {
                displayDataInfo(savedAnalysis.dataInfo);
            }
        } catch (e) {
            console.error('恢复数据失败:', e);
        }
    }

    $('#analyzeBtn').on('click', function() {
        $('#statsContent').html('加载中...');
        $.getJSON('/chart_data', function(response) {
            if (response.success) {
                const statsHtml = '<p>总发货量: '+response.statistics.total_shipments+'</p>'+
                    '<h4>状态分布:</h4>'+
                    '<ul>'+Object.entries(response.summary.status_distribution).map(function(e){return '<li>'+e[0]+': '+e[1]+'</li>';}).join('')+'</ul>';

                $('#statsContent').html(statsHtml);

                // 保存到缓存
                cacheSet('analyze_data', {
                    statsContent: statsHtml,
                    statusDistribution: response.summary.status_distribution,
                    chartData: response.statistics,
                    dataInfo: response.statistics.data_info
                });

                // 创建图表
                createStatusChart(response.summary.status_distribution);
                display3DCharts(response.statistics);
                displayDataInfo(response.statistics.data_info);
            } else {
                $('#statsContent').html('<div class="error">'+response.message+'</div>');
            }
        }).fail(function() {
            $('#statsContent').html('<div class="error">加载失败，请重试</div>');
        });
    });
});
