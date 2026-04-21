// report.js - 日报中心页面

$(function(){
    // 页面加载时从缓存恢复数据
    const savedReport = cacheGet('daily_report');
    if (savedReport) {
        $('#dailyReportContent').html(savedReport);
    }

    $('#genReportBtn').on('click', async function() {
        const $content = $('#dailyReportContent');
        const $btn = $(this);
        $btn.prop('disabled', true);
        $content.html('正在生成日报...');

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
                                if (isThinking) {
                                    $content.html('<em style="color:#666;">思考中：' + data.content + '</em>');
                                } else {
                                    $content.html(fullContent + '\n\n<em style="color:#666;">继续生成...</em>');
                                }
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
