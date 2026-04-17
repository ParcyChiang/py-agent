// admin_log.js - 日志中心页面

$(function(){
    $('#loadLogsBtn').on('click', function() {
        $('#logsContent').html('加载中...');
        $.getJSON('/admin_log', function(response) {
            if (response.success) {
                var logsHtml = '';
                response.logs.forEach(function(log) {
                    logsHtml += '<p><strong>' + log.timestamp + '</strong> - ' + log.user + ' - ' + log.action + '</p>';
                });
                $('#logsContent').html(logsHtml);
            } else {
                $('#logsContent').html('<div class="error">' + response.message + '</div>');
            }
        }).fail(function() {
            $('#logsContent').html('<div class="error">加载失败，请重试</div>');
        });
    });
});
