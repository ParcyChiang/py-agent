// 公共函数库

/**
 * 显示 Toast 提示消息
 * @param {string} message - 提示文本
 * @param {string} type - 类型 ('success' | 'error')
 */
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

/**
 * 加载物流数据列表 (upload 页面)
 * @param {number} page - 页码
 */
function loadShipments(page) {
    if (page) currentPage = page;
    $('#shipmentsTip').html('加载中...');
    $('#shipmentsList').html('');
    $('#tablePagination').html('');

    $.getJSON('/shipments?page=' + currentPage + '&pageSize=' + pageSize, function(response) {
        if (response.success && response.data.length > 0) {
            total = response.total || response.data.length;
            var html = '<table><tr><th>ID</th><th>起始地</th><th>目的地</th><th>状态</th><th>重量 (kg)</th></tr>';
            response.data.forEach(function(shipment){
                html += '<tr>'+
                    '<td>'+shipment.id+'</td>'+
                    '<td>'+shipment.origin+'</td>'+
                    '<td>'+shipment.destination+'</td>'+
                    '<td>'+shipment.status+'</td>'+
                    '<td>'+shipment.weight+'</td>'+
                '</tr>';
            });
            html += '</table>';
            $('#shipmentsList').html(html);
            $('#shipmentsTip').html('');
            renderPagination();
        } else {
            $('#shipmentsTip').html('<div style="padding:10px;background:rgba(255,255,255,0.1);border-radius:4px;">暂无数据，请上传CSV文件</div>');
            $('#shipmentsList').html('');
        }
    }).fail(function(){
        $('#shipmentsTip').html('<div style="padding:10px;background:rgba(255,100,100,0.2);border-radius:4px;">加载失败，请重试</div>');
        $('#shipmentsList').html('');
    });
}

/**
 * 渲染分页控件 (upload 页面)
 */
function renderPagination() {
    var pagination = $('#tablePagination');
    pagination.html('');

    var totalPages = Math.ceil(total / pageSize);
    if (totalPages <= 1) return;

    var paginationContainer = $('<div class="pagination-container"></div>');

    // 左侧：总记录数
    var totalInfo = $('<div class="total-info">共 ' + total + ' 条记录</div>');
    paginationContainer.append(totalInfo);

    // 中间：页码按钮
    var pageButtons = $('<div class="page-buttons"></div>');

    // 计算显示的页码范围
    var startPage = Math.max(1, currentPage - 2);
    var endPage = Math.min(totalPages, startPage + 5);
    if (endPage - startPage < 5) {
        startPage = Math.max(1, endPage - 5);
    }

    // 上一页按钮
    if (currentPage > 1) {
        var prevBtn = $('<button class="pagination-btn">上一页</button>');
        prevBtn.on('click', function() {
            currentPage = Math.max(1, currentPage - 1);
            loadShipments();
        });
        pageButtons.append(prevBtn);
    }

    // 页码按钮
    for (var i = startPage; i <= endPage; i++) {
        var btn = $('<button class="pagination-btn ' + (i === currentPage ? 'active' : '') + '">' + i + '</button>');
        btn.on('click', function() {
            currentPage = parseInt($(this).text());
            loadShipments();
        });
        pageButtons.append(btn);
    }

    // 下一页按钮
    if (currentPage < totalPages) {
        var nextBtn = $('<button class="pagination-btn">下一页</button>');
        nextBtn.on('click', function() {
            currentPage = Math.min(totalPages, currentPage + 1);
            loadShipments();
        });
        pageButtons.append(nextBtn);
    }

    paginationContainer.append(pageButtons);

    // 右侧：跳转到指定页
    var jumpToPage = $('<div class="jump-to-page"></div>');
    jumpToPage.html('前往第 <input type="number" id="jumpPageInput" min="1" max="' + totalPages + '" value="' + currentPage + '" style="width: 60px; margin: 0 5px; padding: 2px 4px; border: 1px solid rgba(255,255,255,0.3); border-radius: 4px; background: rgba(255,255,255,0.1); color: #fff;"> 页 <button id="jumpPageBtn" class="pagination-btn" style="margin-left: 5px;">确定</button>');
    paginationContainer.append(jumpToPage);

    pagination.append(paginationContainer);

    // 添加跳转按钮事件
    $('#jumpPageBtn').on('click', function() {
        var jumpPage = parseInt($('#jumpPageInput').val());
        if (jumpPage >= 1 && jumpPage <= totalPages) {
            currentPage = jumpPage;
            loadShipments();
        }
    });

    // 添加回车键事件
    $('#jumpPageInput').on('keypress', function(e) {
        if (e.key === 'Enter') {
            $('#jumpPageBtn').click();
        }
    });
}

/**
 * 生成分页控件 (compare 页面)
 * @param {number} total - 总记录数
 * @param {number} currentPage - 当前页
 * @param {number} pageSize - 每页数量
 */
function generatePagination(total, currentPage, pageSize) {
    var totalPages = Math.ceil(total / pageSize);
    var paginationHtml = '<ul class="pagination">';

    // 上一页
    if (currentPage > 1) {
        paginationHtml += '<li><a href="#" data-page="' + (currentPage - 1) + '">上一页</a></li>';
    } else {
        paginationHtml += '<li class="disabled"><a href="#">上一页</a></li>';
    }

    // 页码
    var startPage = Math.max(1, currentPage - 2);
    var endPage = Math.min(totalPages, startPage + 4);

    if (startPage > 1) {
        paginationHtml += '<li><a href="#" data-page="1">1</a></li>';
        if (startPage > 2) {
            paginationHtml += '<li class="disabled"><a href="#">...</a></li>';
        }
    }

    for (var i = startPage; i <= endPage; i++) {
        if (i === currentPage) {
            paginationHtml += '<li class="active"><a href="#" data-page="' + i + '">' + i + '</a></li>';
        } else {
            paginationHtml += '<li><a href="#" data-page="' + i + '">' + i + '</a></li>';
        }
    }

    if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
            paginationHtml += '<li class="disabled"><a href="#">...</a></li>';
        }
        paginationHtml += '<li><a href="#" data-page="' + totalPages + '">' + totalPages + '</a></li>';
    }

    // 下一页
    if (currentPage < totalPages) {
        paginationHtml += '<li><a href="#" data-page="' + (currentPage + 1) + '">下一页</a></li>';
    } else {
        paginationHtml += '<li class="disabled"><a href="#">下一页</a></li>';
    }

    paginationHtml += '</ul>';
    $('#pagination').html(paginationHtml);
}
