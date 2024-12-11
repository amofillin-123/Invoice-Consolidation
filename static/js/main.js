document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('uploadForm');
    const submitBtn = document.getElementById('submitBtn');
    const spinner = submitBtn.querySelector('.spinner-border');
    const messageArea = document.getElementById('messageArea');
    const downloadArea = document.getElementById('downloadArea');
    const downloadLink = document.getElementById('downloadLink');
    const progressArea = document.getElementById('progressArea');
    const progressBar = progressArea.querySelector('.progress-bar');
    const progressMessage = document.getElementById('progressMessage');

    let progressCheckInterval = null;

    function showMessage(message, type) {
        messageArea.textContent = message;
        messageArea.className = `alert alert-${type}`;
        messageArea.classList.remove('d-none');
    }

    function showError(message) {
        showMessage(message, 'danger');
        downloadArea.classList.add('d-none');
        progressArea.classList.add('d-none');
        clearInterval(progressCheckInterval);
    }

    function showSuccess(message) {
        showMessage(message, 'success');
    }

    function updateProgress(progress, message) {
        progressBar.style.width = `${progress}%`;
        progressBar.setAttribute('aria-valuenow', progress);
        progressBar.textContent = `${progress}%`;
        if (message) {
            progressMessage.textContent = message;
        }
    }

    function checkProgress(taskId) {
        fetch(`/progress/${taskId}`)
            .then(response => response.json())
            .then(data => {
                if (data.status === 'unknown') {
                    clearInterval(progressCheckInterval);
                    showError('无法获取处理进度');
                    return;
                }

                updateProgress(data.progress, data.message);

                if (data.status === 'completed') {
                    clearInterval(progressCheckInterval);
                    showSuccess('文件处理完成！');
                    downloadArea.classList.remove('d-none');
                } else if (data.status === 'error') {
                    clearInterval(progressCheckInterval);
                    showError(data.message);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                clearInterval(progressCheckInterval);
                showError('检查进度时出错');
            });
    }

    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const files = document.getElementById('files').files;
        if (files.length === 0) {
            showError('请选择至少一个PDF文件');
            return;
        }

        // 检查文件大小
        for (let file of files) {
            if (file.size > 16 * 1024 * 1024) {
                showError(`文件 ${file.name} 太大，请确保每个文件不超过16MB`);
                return;
            }
        }

        // 准备表单数据
        const formData = new FormData();
        for (let file of files) {
            formData.append('files[]', file);
        }

        // 开始上传
        submitBtn.disabled = true;
        spinner.classList.remove('d-none');
        downloadArea.classList.add('d-none');
        messageArea.classList.add('d-none');
        progressArea.classList.remove('d-none');
        updateProgress(0, '准备处理文件...');

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (response.ok) {
                // 开始检查进度
                progressCheckInterval = setInterval(() => checkProgress(result.task_id), 500);
                downloadLink.href = result.download_url;
            } else {
                showError(result.error || '处理文件时出错');
                submitBtn.disabled = false;
                spinner.classList.add('d-none');
            }
        } catch (error) {
            showError('上传文件时发生错误');
            console.error('Error:', error);
            submitBtn.disabled = false;
            spinner.classList.add('d-none');
        } finally {
            submitBtn.disabled = false;
            spinner.classList.add('d-none');
        }
    });
});
