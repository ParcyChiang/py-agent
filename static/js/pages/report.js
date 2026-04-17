// report.js - 日报中心页面

$(function(){
    // 页面加载时从缓存恢复数据
    const savedReport = cacheGet('daily_report');
    if (savedReport) {
        $('#dailyReportContent').html(savedReport);
    }

    $('#genReportBtn').on('click', function() {
        $('#dailyReportContent').html('生成中...');
        $.getJSON('/report', function(response) {
            if (response.success) {
                $('#dailyReportContent').html(response.daily_report);
                cacheSet('daily_report', response.daily_report);
            } else {
                $('#dailyReportContent').html('<div class="error">'+response.message+'</div>');
            }
        }).fail(function(){
            $('#dailyReportContent').html('<div class="error">生成失败，请重试</div>');
        });
    });
});
