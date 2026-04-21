// analysis_report.js - 运营分析报告页面

$(function(){
    // 页面加载时从缓存恢复数据
    const savedAnalysis = cacheGet('analysis_report');
    if (savedAnalysis) {
        $('#analysisContent').html(savedAnalysis);
    }
    const savedDaily = cacheGet('daily_report');
    if (savedDaily) {
        $('#dailyReportContent').html(savedDaily);
    }

    // AI分析报告按钮
    $('#genAnalysisBtn').on('click', async function() {
        const $btn = $(this);
        const $content = $('#analysisContent');
        $btn.prop('disabled', true);
        $content.html('<em style="color:#666;">正在分析数据...</em>');

        try {
            const response = await fetch('/analysis_stream');
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let fullContent = '';
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
                            if (data.type === 'thinking') {
                                $content.html('<em style="color:#666;">分析中：' + data.content + '</em>');
                            } else if (data.type === 'text') {
                                isThinking = false;
                                fullContent += data.content;
                                $content.html(fullContent);
                            } else if (data.type === 'done') {
                                $content.html(data.content);
                                cacheSet('analysis_report', data.content);
                            } else if (data.type === 'error') {
                                $content.html('<div class="error">生成失败：' + data.content + '</div>');
                            }
                        } catch (e) {}
                    }
                }
            }
        } catch (error) {
            $content.html('<div class="error">请求失败：' + error.message + '</div>');
        } finally {
            $btn.prop('disabled', false);
        }
    });

    // 每日运营报告按钮
    $('#genDailyReportBtn').on('click', async function() {
        const $btn = $(this);
        const $content = $('#dailyReportContent');
        $btn.prop('disabled', true);
        $content.html('<em style="color:#666;">正在生成日报...</em>');

        try {
            const response = await fetch('/report_stream');
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let fullContent = '';
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
                            if (data.type === 'thinking') {
                                $content.html('<em style="color:#666;">生成中：' + data.content + '</em>');
                            } else if (data.type === 'text') {
                                isThinking = false;
                                fullContent += data.content;
                                $content.html(fullContent);
                            } else if (data.type === 'done') {
                                $content.html(data.content);
                                cacheSet('daily_report', data.content);
                            } else if (data.type === 'error') {
                                $content.html('<div class="error">生成失败：' + data.content + '</div>');
                            }
                        } catch (e) {}
                    }
                }
            }
        } catch (error) {
            $content.html('<div class="error">请求失败：' + error.message + '</div>');
        } finally {
            $btn.prop('disabled', false);
        }
    });
});
