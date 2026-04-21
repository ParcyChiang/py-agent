// analysis_report.js - 运营分析报告页面

$(function(){
    // 页面加载时从缓存恢复数据
    const savedReport = cacheGet('analysis_report_data');
    if (savedReport) {
        $('#analysisContent').html(savedReport.analysisContent);
        $('#dailyReportContent').html(savedReport.dailyReportContent);
    }

    $('#genReportBtn').on('click', async function() {
        const $btn = $(this);
        $btn.prop('disabled', true);

        const $analysisContent = $('#analysisContent');
        const $reportContent = $('#dailyReportContent');

        $analysisContent.html('<em style="color:#666;">正在分析数据...</em>');
        $reportContent.html('<em style="color:#666;">正在生成日报...</em>');

        try {
            const response = await fetch('/analysis_report_stream');
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let analysisContent = '';
            let reportContent = '';
            let currentReport = null;
            let isThinking = true;

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value);
                const lines = chunk.split('\n');

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));
                            if (data.type === 'report_start') {
                                currentReport = data.content;
                                isThinking = true;
                                if (data.content === 'analysis') {
                                    analysisContent = '';
                                } else {
                                    reportContent = '';
                                }
                            } else if (data.type === 'thinking') {
                                if (currentReport === 'analysis') {
                                    $analysisContent.html('<em style="color:#666;">分析中：' + data.content + '</em>');
                                } else {
                                    $reportContent.html('<em style="color:#666;">生成中：' + data.content + '</em>');
                                }
                            } else if (data.type === 'text') {
                                isThinking = false;
                                if (currentReport === 'analysis') {
                                    analysisContent += data.content;
                                    $analysisContent.html(analysisContent);
                                } else {
                                    reportContent += data.content;
                                    $reportContent.html(reportContent);
                                }
                            } else if (data.type === 'done') {
                                $analysisContent.html(data.analysis);
                                $reportContent.html(data.daily_report);
                                cacheSet('analysis_report_data', {
                                    analysisContent: data.analysis,
                                    dailyReportContent: data.daily_report
                                });
                            } else if (data.type === 'error') {
                                $analysisContent.html('<div class="error">生成失败：' + data.content + '</div>');
                            }
                        } catch (e) {}
                    }
                }
            }
        } catch (error) {
            $analysisContent.html('<div class="error">请求失败：' + error.message + '</div>');
        } finally {
            $btn.prop('disabled', false);
        }
    });
});
