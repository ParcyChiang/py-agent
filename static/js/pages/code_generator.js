// code_generator.js - Python代码生成器页面

function setQuestion(question) {
    document.getElementById('questionInput').value = question;
}

// 页面加载时恢复缓存数据
$(function(){
    const savedCode = cacheGet('generated_code');
    if (savedCode) {
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
    const thinkingContainer = document.getElementById('thinkingContainer');
    const thinkingContent = document.getElementById('thinkingContent');
    const executeBtn = document.getElementById('executeBtn');

    loading.style.display = 'block';
    codeContainer.style.display = 'none';
    thinkingContainer.style.display = 'block';
    thinkingContent.textContent = '正在思考...\n';
    executeBtn.disabled = true;

    // 使用 fetch + 非流式接口
    try {
        const response = await fetch('/generate_code', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ question: question })
        });

        const result = await response.json();

        loading.style.display = 'none';

        if (result.success) {
            thinkingContent.textContent = result.thinking || '（无思考过程）';
            document.getElementById('generatedCode').textContent = result.code;
            codeContainer.style.display = 'block';
            executeBtn.disabled = false;
            cacheSet('generated_code', { question: question, code: result.code });
        } else {
            thinkingContent.textContent = '生成失败：' + (result.message || '未知错误');
        }
    } catch (error) {
        loading.style.display = 'none';
        thinkingContent.textContent = '请求失败：' + error.message;
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
    document.getElementById('thinkingContent').textContent = '';
    const imageContainer = document.getElementById('imageContainer');
    if (imageContainer) imageContainer.remove();
    document.getElementById('codeContainer').style.display = 'none';
    document.getElementById('thinkingContainer').style.display = 'none';
    document.getElementById('outputContainer').style.display = 'none';
    document.getElementById('executeBtn').disabled = true;
    cacheRemove('generated_code');
    cacheRemove('code_output');
}
