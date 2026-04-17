// analysis_report.js - 运营分析报告页面

$(function(){
    // 页面加载时从缓存恢复数据
    const savedReport = cacheGet('analysis_report_data');
    if (savedReport) {
        $('#analysisContent').html(savedReport.analysisContent);
        $('#dailyReportContent').html(savedReport.dailyReportContent);
    }

    $('#genReportBtn').on('click', function() {
        $('#analysisContent').html('分析中，请稍候...');
        $('#dailyReportContent').html('生成报告中...');
        $.getJSON('/analysis_report', function(response) {
            if (response.success) {
                $('#analysisContent').html(response.analysis);
                $('#dailyReportContent').html(response.daily_report);
                cacheSet('analysis_report_data', {
                    analysisContent: response.analysis,
                    dailyReportContent: response.daily_report
                });
            } else {
                $('#analysisContent').html('<div class="error">'+response.message+'</div>');
            }
        }).fail(function(){
            $('#analysisContent').html('<div class="error">生成失败，请重试</div>');
        });
    });
});
