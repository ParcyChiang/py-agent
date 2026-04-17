// upload.js - 数据导入页面

var currentPage = 1;
var pageSize = 10;
var total = 0;

$(function(){
    // 页面加载时自动检查并展示数据
    loadShipments();

    // 点击上传按钮触发文件选择
    $('#uploadBtn').on('click', function(){
        $('#file').click();
    });

    // 文件选择后自动上传
    $('#file').on('change', function(){
        var fileName = $(this).val().split('\\').pop();
        if (fileName) {
            $('#uploadResult').html('<div class="success">已选择文件: ' + fileName + '，正在上传...</div>');
            var formData = new FormData();
            formData.append('file', this.files[0]);
            $.ajax({
                url: '/upload',
                type: 'POST',
                data: formData,
                processData: false,
                contentType: false,
                success: function(response) {
                    if (response.success) {
                        $('#uploadResult').html('<div class="success">'+response.message+'</div><p>导入记录数: '+response.count+'</p>');
                        loadShipments();
                    } else {
                        $('#uploadResult').html('<div class="error">'+response.message+'</div>');
                    }
                },
                error: function() {
                    $('#uploadResult').html('<div class="error">上传失败，请重试</div>');
                }
            });
        }
    });

    $('#deleteCsvBtn').on('click', function(){
        if(!confirm('确定要删除所有已导入的CSV数据吗？此操作不可恢复。')) return;
        $.ajax({
            url: '/delete_csv',
            type: 'POST',
            success: function(response){
                if(response.success){
                    $('#uploadResult').html('<div class="success">'+response.message+'</div>');
                    $('#shipmentsTip').html('<div style="padding:10px;background:rgba(255,255,255,0.1);border-radius:4px;">暂无数据，请上传CSV文件</div>');
                    $('#shipmentsList').html('');
                } else {
                    $('#uploadResult').html('<div class="error">'+response.message+'</div>');
                }
            },
            error: function(){
                $('#uploadResult').html('<div class="error">删除失败，请重试</div>');
            }
        });
    });
});
