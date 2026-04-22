// code_generator.js - Python代码生成器页面

function setQuestion(question) {
    document.getElementById('questionInput').value = question;
}

// 页面加载时恢复缓存数据
$(function(){
    // 检查是否有需要恢复的对话
    const chatData = sessionStorage.getItem('chat_to_load');
    if (chatData) {
        sessionStorage.removeItem('chat_to_load');
        try {
            const chat = JSON.parse(chatData);
            if (chat.page === 'code_generator') {
                document.getElementById('questionInput').value = chat.user_input || '';
                document.getElementById('generatedCode').textContent = chat.ai_response || '';
                document.getElementById('codeContainer').style.display = chat.ai_response ? 'block' : 'none';
                document.getElementById('executeBtn').disabled = !chat.ai_response;
            }
        } catch (e) {
            console.error('恢复对话数据失败:', e);
        }
    }

    const savedCode = cacheGet('generated_code');
    if (savedCode && !chatData) {
        document.getElementById('questionInput').value = savedCode.question || '';
        document.getElementById('generatedCode').textContent = savedCode.code || '';
        if (savedCode.code) {
            document.getElementById('codeContainer').style.display = 'block';
            document.getElementById('executeBtn').disabled = false;
        }
    }

    const savedOutput = cacheGet('code_output');
    if (savedOutput) {
        const outputDiv = document.getElementById('executionOutput');
        outputDiv.textContent = savedOutput;
        outputDiv.className = 'output-container';
        document.getElementById('outputContainer').style.display = 'block';
    }
});

async function generateCode() {
    const question = document.getElementById('questionInput').value.trim();
    if (!question) {
        alert('请输入您的问题！');
        return;
    }

    const loading = document.getElementById('loading');
    const codeContainer = document.getElementById('codeContainer');
    const executeBtn = document.getElementById('executeBtn');
    const generatedCode = document.getElementById('generatedCode');

    loading.style.display = 'block';
    codeContainer.style.display = 'block';
    generatedCode.textContent = '';
    executeBtn.disabled = true;

    // 使用流式接口
    try {
        const response = await fetch('/generate_code_stream', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ question: question })
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let fullCode = '';
        let isThinking = true;  // 标记当前是否在thinking阶段

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
                            // thinking阶段：显示在代码框内
                            generatedCode.textContent += data.content;
                            generatedCode.scrollTop = generatedCode.scrollHeight;
                        } else if (data.type === 'text') {
                            // text阶段：thinking结束
                            if (isThinking) {
                                isThinking = false;
                                generatedCode.textContent = fullCode + '\n\n// 思考完成，正在生成代码...\n\n';
                            }
                            fullCode += data.content;
                            generatedCode.textContent = fullCode;
                            generatedCode.scrollTop = generatedCode.scrollHeight;
                        } else if (data.type === 'done') {
                            generatedCode.textContent = data.code;
                            loading.style.display = 'none';
                            executeBtn.disabled = false;
                            cacheSet('generated_code', { question: question, code: data.code });
                            console.log('[CodeGen] 生成完成，后端自动保存到对话历史');
                        } else if (data.type === 'error') {
                            loading.style.display = 'none';
                            generatedCode.textContent = '生成失败：' + data.content;
                        }
                    } catch (e) {
                        // 忽略解析错误
                    }
                }
            }
        }

        loading.style.display = 'none';
    } catch (error) {
        loading.style.display = 'none';
        generatedCode.textContent = '请求失败：' + error.message;
    }
}

async function executeCode() {
    const code = document.getElementById('generatedCode').textContent;
    if (!code) {
        alert('没有可执行的代码！');
        return;
    }

    const loading = document.getElementById('loading');
    const outputContainer = document.getElementById('outputContainer');
    const executeBtn = document.getElementById('executeBtn');

    loading.style.display = 'block';
    executeBtn.disabled = true;

    try {
        const response = await fetch('/execute_code', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ code: code })
        });

        const result = await response.json();

        const outputDiv = document.getElementById('executionOutput');
        outputDiv.className = 'output-container';

        if (result.success) {
            outputDiv.classList.add('success-output');
            outputDiv.textContent = result.output || '代码执行成功，无输出内容';

            // 如果有图像数据，显示图像
            let imageContainer = document.getElementById('imageContainer');
            if (result.image) {
                if (!imageContainer) {
                    imageContainer = document.createElement('div');
                    imageContainer.id = 'imageContainer';
                    imageContainer.style.marginTop = '15px';
                    imageContainer.style.textAlign = 'center';
                    outputDiv.parentNode.insertBefore(imageContainer, outputDiv.nextSibling);
                }
                imageContainer.innerHTML = `<img src="data:image/png;base64,${result.image}" style="max-width:100%; border:1px solid #ddd; border-radius:8px;" />`;
            } else if (imageContainer) {
                imageContainer.remove();
            }

            cacheSet('code_output', result.output || '代码执行成功，无输出内容');
        } else {
            outputDiv.classList.add('error-output');
            outputDiv.textContent = result.error || '代码执行失败';
            cacheSet('code_output', result.error || '代码执行失败');
        }

        outputContainer.style.display = 'block';
    } catch (error) {
        const outputDiv = document.getElementById('executionOutput');
        outputDiv.className = 'output-container error-output';
        outputDiv.textContent = '执行请求失败：' + error.message;
        outputContainer.style.display = 'block';
    } finally {
        loading.style.display = 'none';
        executeBtn.disabled = false;
    }
}

function clearAll() {
    document.getElementById('questionInput').value = '';
    document.getElementById('generatedCode').textContent = '';
    document.getElementById('executionOutput').textContent = '';
    const imageContainer = document.getElementById('imageContainer');
    if (imageContainer) imageContainer.remove();
    document.getElementById('codeContainer').style.display = 'none';
    document.getElementById('outputContainer').style.display = 'none';
    document.getElementById('executeBtn').disabled = true;
    cacheRemove('generated_code');
    cacheRemove('code_output');
}
