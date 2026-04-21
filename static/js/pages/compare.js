// compare.js - 物流对比页面

$(function(){
    // 全局变量
    var currentPage = 1;
    var pageSize = 10;

    // 页面加载时从缓存恢复数据
    var savedComparison = cacheGet('comparison_data');
    if (savedComparison) {
        currentPage = savedComparison.currentPage || 1;
        pageSize = savedComparison.pageSize || 20;
        $('#comparisonResult').html(savedComparison.html);
        generatePagination(savedComparison.total, savedComparison.page, savedComparison.pageSize);
        // 恢复筛选框值
        if (savedComparison.originFilter) {
            $('#originFilter').val(savedComparison.originFilter);
            if (savedComparison.originFilter) $('#originFilter').siblings('.clear-btn').addClass('show');
        }
        if (savedComparison.destinationFilter) {
            $('#destinationFilter').val(savedComparison.destinationFilter);
            if (savedComparison.destinationFilter) $('#destinationFilter').siblings('.clear-btn').addClass('show');
        }
        if (savedComparison.courierFilter) {
            $('#courierFilter').val(savedComparison.courierFilter);
            if (savedComparison.courierFilter) $('#courierFilter').siblings('.clear-btn').addClass('show');
        }
        $('#pageSize').val(pageSize);

        // 恢复智能分析结果
        $('.analyze-btn').each(function() {
            var index = $(this).data('index');
            var page = $(this).data('page');
            var cachedAnalysis = cacheGet('comparison_analysis_' + index + '_' + page);
            if (cachedAnalysis) {
                var markdownContent = marked.parse(cachedAnalysis);
                $('#analysis-' + index).html('<h4>智能分析结果</h4><div class="markdown-body">' + markdownContent + '</div>');
            }
        });
    }

    // 加载筛选下拉选项
    function loadFilterOptions() {
        $.getJSON('/api/shipments/filters', function(response) {
            if (response.success) {
                var origins = response.origins;
                var destinations = response.destinations;
                var couriers = response.couriers;

                // 填充下拉菜单（用于输入联想）
                fillDropdownMenu('#originDropdown', origins);
                fillDropdownMenu('#destinationDropdown', destinations);
                fillDropdownMenu('#courierDropdown', couriers);
            }
        });
    }

    // 填充下拉菜单
    function fillDropdownMenu(menuId, items) {
        var html = '';
        items.forEach(function(item) {
            html += '<div class="dropdown-item" data-value="' + item + '">' + item + '</div>';
        });
        $(menuId).html(html);
    }

    // 初始化筛选下拉框
    loadFilterOptions();

    // 下拉菜单交互
    $(document).on('click', '.dropdown-item', function() {
        var value = $(this).data('value');
        var menuId = $(this).parent().attr('id');
        var input;
        if (menuId === 'originDropdown') {
            input = $('#originFilter');
        } else if (menuId === 'destinationDropdown') {
            input = $('#destinationFilter');
        } else if (menuId === 'courierDropdown') {
            input = $('#courierFilter');
        }
        input.val(value).focus();
        input.siblings('.clear-btn').addClass('show');
        $(this).parent().removeClass('show');
        // 选中后自动触发搜索
        currentPage = 1;
        loadComparisonData(currentPage);
    });

    // 输入框事件 - 显示匹配的下拉菜单
    $('#originFilter, #destinationFilter, #courierFilter').on('input', function() {
        var inputId = $(this).attr('id');
        var menuId;

        if (inputId === 'originFilter') {
            menuId = '#originDropdown';
        } else if (inputId === 'destinationFilter') {
            menuId = '#destinationDropdown';
        } else if (inputId === 'courierFilter') {
            menuId = '#courierDropdown';
        }

        var filter = $(this).val().toLowerCase();
        var allItems = $(menuId).find('.dropdown-item').map(function() { return $(this).data('value'); }).get();
        var filtered = allItems.filter(function(item) {
            return item.toLowerCase().indexOf(filter) !== -1;
        });

        fillDropdownMenu(menuId, filtered);
        if (filtered.length > 0) {
            $(menuId).addClass('show');
        } else {
            $(menuId).removeClass('show');
        }
    });

    // 聚焦时显示下拉菜单
    $('#originFilter, #destinationFilter, #courierFilter').on('focus', function() {
        var inputId = $(this).attr('id');
        var menuId;
        if (inputId === 'originFilter') menuId = '#originDropdown';
        else if (inputId === 'destinationFilter') menuId = '#destinationDropdown';
        else if (inputId === 'courierFilter') menuId = '#courierDropdown';

        if ($(menuId).children().length > 0) {
            $(menuId).addClass('show');
        }
    });

    // 输入时显示/隐藏清除按钮
    $('#originFilter, #destinationFilter, #courierFilter').on('input', function() {
        var clearBtn = $(this).siblings('.clear-btn');
        if ($(this).val().length > 0) {
            clearBtn.addClass('show');
        } else {
            clearBtn.removeClass('show');
        }
    });

    // 清除按钮点击事件
    $(document).on('click', '.clear-btn', function() {
        var targetId = $(this).data('target');
        $('#' + targetId).val('').focus();
        $(this).removeClass('show');
        // 清除后自动触发搜索
        currentPage = 1;
        loadComparisonData(currentPage);
    });

    // 点击外部关闭下拉菜单
    $(document).on('click', function(e) {
        if (!$(e.target).closest('.custom-select').length) {
            $('.dropdown-menu').removeClass('show');
        }
    });

    // 加载对比数据
    function loadComparisonData(page) {
        var originFilter = $('#originFilter').val();
        var destinationFilter = $('#destinationFilter').val();
        var courierFilter = $('#courierFilter').val();

        $('#comparisonResult').html('加载中...');
        $.getJSON('/api/shipments/compare', {
            origin: originFilter,
            destination: destinationFilter,
            courier: courierFilter,
            page: page,
            pageSize: pageSize
        }, function(response) {
            if (response.success) {
                if (response.data.length > 0) {
                    var html = '';
                    response.data.forEach(function(group, index) {
                        html += '<div class="address-group">';
                        html += '<h3>' + (group.address_type === 'destination' ? '收件地址' : '发件地址') + ': ' + group.address + '</h3>';
                        html += '<div class="group-info">';
                        html += '<div class="info-item"><strong>物流数量</strong><span>' + group.shipment_count + '</span></div>';
                        html += '<div class="info-item"><strong>平均配送时间</strong><span>' + group.avg_delivery_time.toFixed(2) + ' 小时</span></div>';
                        html += '<div class="info-item"><strong>平均运费</strong><span>¥' + group.avg_shipping_fee.toFixed(2) + '</span></div>';
                        html += '</div>';

                        // 状态分布
                        html += '<h4>状态分布</h4>';
                        html += '<div class="status-distribution">';
                        for (var status in group.status_distribution) {
                            html += '<span>' + status + ': ' + group.status_distribution[status] + '</span> ';
                        }
                        html += '</div>';

                        // 快递公司分布
                        html += '<h4>快递公司分布</h4>';
                        html += '<div class="courier-distribution">';
                        for (var courier in group.courier_distribution) {
                            html += '<span>' + courier + ': ' + group.courier_distribution[courier] + '</span> ';
                        }
                        html += '</div>';

                        // 物流列表
                        html += '<h4>物流详情</h4>';
                        html += '<table class="shipments-table">';
                        html += '<tr><th>物流单号</th><th>状态</th><th>重量 (kg)</th><th>运费</th><th>创建时间</th><th>实际送达</th></tr>';
                        group.shipments.forEach(function(shipment) {
                            html += '<tr>';
                            html += '<td>' + shipment.id + '</td>';
                            html += '<td>' + shipment.status + '</td>';
                            html += '<td>' + shipment.weight + '</td>';
                            html += '<td>¥' + shipment.shipping_fee + '</td>';
                            html += '<td>' + shipment.created_at + '</td>';
                            html += '<td>' + (shipment.actual_delivery || '-') + '</td>';
                            html += '</tr>';
                        });
                        html += '</table>';

                        // 分析按钮
                        html += '<button class="analyze-btn" data-index="' + index + '" data-page="' + page + '">智能分析</button>';
                        html += '<div id="analysis-' + index + '" class="analysis-result" style="display: none;"></div>';
                        html += '</div>';
                    });
                    $('#comparisonResult').html(html);

                    // 缓存结果
                    cacheSet('comparison_data', {
                        html: html,
                        currentPage: page,
                        pageSize: pageSize,
                        total: response.total,
                        page: response.page,
                        originFilter: originFilter,
                        destinationFilter: destinationFilter,
                        courierFilter: courierFilter
                    });

                    // 生成分页控件
                    generatePagination(response.total, response.page, response.pageSize);
                } else {
                    $('#comparisonResult').html('没有找到符合条件的对比数据，请先上传包含多条相同地址物流信息的CSV文件');
                    $('#pagination').html('');
                }
            } else {
                $('#comparisonResult').html('加载失败: ' + response.message);
                $('#pagination').html('');
            }
        }).fail(function(){
            $('#comparisonResult').html('加载失败，请重试');
            $('#pagination').html('');
        });
    }

    // 筛选变化时自动加载
    $('#originFilter, #destinationFilter, #courierFilter').on('input', function() {
        clearTimeout(window.filterTimeout);
        window.filterTimeout = setTimeout(function() {
            currentPage = 1;
            loadComparisonData(currentPage);
        }, 300);
    });

    // 快递公司下拉选择时自动加载
    $('#courierFilter').on('change', function() {
        currentPage = 1;
        loadComparisonData(currentPage);
    });

    // 每页数量变化时自动加载
    $('#pageSize').on('change', function() {
        pageSize = $(this).val();
        currentPage = 1;
        loadComparisonData(currentPage);
    });

    // 页面加载时自动加载数据（只有没有缓存数据时才加载）
    if (!cacheGet('comparison_data')) {
        currentPage = 1;
        loadComparisonData(currentPage);
    }

    // 分页按钮点击事件
    $(document).on('click', '.pagination a', function(e) {
        e.preventDefault();
        var page = $(this).data('page');
        if (page) {
            currentPage = page;
            loadComparisonData(currentPage);
        }
    });

    // 分析按钮点击事件
    $(document).on('click', '.analyze-btn', async function() {
        var index = $(this).data('index');
        var page = $(this).data('page');
        var analysisDiv = $('#analysis-' + index);
        analysisDiv.html('<div class="loading"></div> 分析中...').show();

        // 获取当前地址组的数据
        var groupData = [];
        var originFilter = $('#originFilter').val();
        var destinationFilter = $('#destinationFilter').val();
        var courierFilter = $('#courierFilter').val();

        try {
            var compareResponse = await $.getJSON('/api/shipments/compare', {
                origin: originFilter,
                destination: destinationFilter,
                courier: courierFilter,
                page: page,
                pageSize: pageSize
            });

            if (compareResponse.success && compareResponse.data.length > index) {
                groupData.push(compareResponse.data[index]);

                // 调用流式分析API
                var response = await fetch('/api/shipments/analyze_comparison_stream', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ comparison_data: groupData })
                });

                var reader = response.body.getReader();
                var decoder = new TextDecoder();
                var fullContent = '';
                var isThinking = true;

                while (true) {
                    var { done, value } = await reader.read();
                    if (done) break;

                    var chunk = decoder.decode(value);
                    var lines = chunk.split('\n');

                    for (var line of lines) {
                        if (line.startsWith('data: ')) {
                            try {
                                var data = JSON.parse(line.slice(6));
                                if (data.type === 'thinking') {
                                    isThinking = true;
                                    analysisDiv.html('<em style="color:#666;">分析中：' + data.content + '</em>');
                                } else if (data.type === 'text') {
                                    isThinking = false;
                                    fullContent += data.content;
                                    var markdownContent = marked.parse(fullContent);
                                    analysisDiv.html('<h4>智能分析结果</h4><div class="markdown-body">' + markdownContent + '</div>');
                                } else if (data.type === 'end') {
                                    cacheSet('comparison_analysis_' + index + '_' + page, fullContent);
                                } else if (data.type === 'error') {
                                    analysisDiv.html('<h4>分析失败</h4><p>' + data.content + '</p>');
                                }
                            } catch (e) {}
                        }
                    }
                }
            }
        } catch (error) {
            analysisDiv.html('<h4>分析失败</h4><p>' + error.message + '</p>');
        }
    });
});
