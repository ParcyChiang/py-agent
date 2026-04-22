// analysis_report.js - 运营分析报告页面

$(function(){
    // 检查是否有需要恢复的对话
    const chatData = sessionStorage.getItem('chat_to_load');
    if (chatData) {
        sessionStorage.removeItem('chat_to_load');
        try {
            const chat = JSON.parse(chatData);
            if (chat.page === 'analysis_report') {
                if (chat.title && chat.title.includes('日报')) {
                    $('#dailyReportContent').html(chat.ai_response || '');
                } else {
                    $('#analysisContent').html(chat.ai_response || '');
                }
            }
        } catch (e) {
            console.error('恢复对话数据失败:', e);
        }
    }

    // 页面加载时从缓存恢复数据
    const savedAnalysis = cacheGet('analysis_report');
    if (savedAnalysis && !chatData) {
        $('#analysisContent').html(savedAnalysis);
    }
    const savedDaily = cacheGet('daily_report');
    if (savedDaily && !chatData) {
        $('#dailyReportContent').html(savedDaily);
    }

    // AI分析报告按钮
    $('#genAnalysisBtn').off('click').on('click', async function() {
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
                                console.log('[Analysis] 生成完成，后端自动保存到对话历史');
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
    $('#genDailyReportBtn').off('click').on('click', async function() {
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
                                if (isThinking) {
                                    $content.html('<em style="color:#666;">生成中：' + data.content + '</em>');
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
                                console.log('[Daily Report] 生成完成，后端自动保存到对话历史');
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
