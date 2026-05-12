const uploadMethods = {
        chooseFiles() {
            this.$refs.fileInput.click();
        },
        chooseFolder() {
            this.$refs.folderInput.click();
        },
        onFilesSelected(event) {
            const files = Array.from(event.target.files || []);
            if (files.length === 0) return;
            this.uploadToServer(files, false);
        },
        onFolderSelected(event) {
            const files = Array.from(event.target.files || []);
            if (files.length === 0) return;
            this.uploadToServer(files, true);
        },
        onDrop(event) {
            this.dragOver = false;
            const files = Array.from(event.dataTransfer.files || []);
            if (files.length === 0) {
                this.showToast('没有检测到有效文件', 'warning');
                return;
            }
            this.uploadToServer(files, false);
        },
        resetPipeline() {
            this.previewFilename = '';
            this.previewData = null;
            this.processResult = null;
            this.processedFiles = [];
            this.uploadFailedExpanded = false;
            this.uploadIgnoredExpanded = false;
        },
        uploadToServer(files, isFolder) {
            const endpoint = isFolder ? '/upload_folder' : '/upload';
            const formData = new FormData();
            files.forEach(file => {
                if (isFolder) {
                    formData.append('files', file, file.webkitRelativePath || file.name);
                } else {
                    formData.append('files', file);
                }
            });

            this.resetPipeline();
            this.showProgress(isFolder ? `正在上传文件夹，共 ${files.length} 个文件` : `正在上传文件，共 ${files.length} 个文件`, 0);

            const xhr = new XMLHttpRequest();
            xhr.upload.addEventListener('progress', (e) => {
                if (!e.lengthComputable) return;
                const p = Math.round((e.loaded / e.total) * 100);
                this.updateProgress(p, `上传中 ${p}%`);
            });

            xhr.addEventListener('load', () => {
                this.hideProgress();
                if (xhr.status < 200 || xhr.status >= 300) {
                    this.showToast(`上传失败: HTTP ${xhr.status}`, 'error');
                    return;
                }

                let data;
                try {
                    data = JSON.parse(xhr.responseText);
                } catch (error) {
                    this.showToast('服务器响应解析失败', 'error');
                    return;
                }

                if (data.error) {
                    this.showToast(data.error, 'error');
                    return;
                }

                this.uploadedFiles = data.files || [];
                this.uploadFolderStats = isFolder ? data : null;
                this.$refs.fileInput.value = '';
                this.$refs.folderInput.value = '';

                this.showToast(`上传完成，共 ${this.uploadedFiles.length} 个文件`, 'success');

                if (data.warnings && data.warnings.length > 0) {
                    this.showToast(`有 ${data.warnings.length} 个文件上传失败`, 'warning');
                }
            });

            xhr.addEventListener('error', () => {
                this.hideProgress();
                this.showToast('上传失败：网络错误', 'error');
            });

            xhr.open('POST', endpoint);
            xhr.send(formData);
        },
        async previewFile(index) {
            const file = this.uploadedFiles[index];
            if (!file || !file.has_lyrics) {
                this.showToast('该文件没有歌词可预览', 'warning');
                return;
            }

            try {
                const response = await fetch('/preview', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ filename: file.filename, ai_enabled: this.aiEnabled, ai_config: this.aiConfig })
                });

                const data = await response.json();
                if (!response.ok || data.error) {
                    throw new Error(data.error || `HTTP ${response.status}`);
                }

                this.previewFilename = file.original_name;
                this.previewData = data;
                this.saveAiConfigToStorage();
                this.showToast(`已预览: ${this.basename(file.original_name)}`, 'success');
            } catch (error) {
                this.showToast(`预览失败: ${error.message}`, 'error');
            }
        },
        previewFirstWithLyrics() {
            const idx = this.uploadedFiles.findIndex(f => f.has_lyrics);
            if (idx === -1) {
                this.showToast('没有包含歌词的文件', 'warning');
                return;
            }
            this.previewFile(idx);
        },
        async processFiles() {
            const filenames = this.filesWithLyrics.map(f => f.filename);
            if (filenames.length === 0) {
                this.showToast('没有可处理文件', 'warning');
                return;
            }

            this.processingFiles = true;
            this.showProgress(`开始处理 ${filenames.length} 个文件`, 5);

            try {
                const response = await fetch('/process', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ filenames, ai_enabled: this.aiEnabled, ai_config: this.aiConfig })
                });

                this.updateProgress(80, '正在汇总处理结果...');

                const data = await response.json();
                if (!response.ok || data.error) {
                    throw new Error(data.error || `HTTP ${response.status}`);
                }

                this.processResult = data;
                this.processedFiles = data.processed_files || [];
                this.uploadFailedExpanded = Boolean(data.failed_files && data.failed_files.length);
                this.uploadIgnoredExpanded = false;
                this.saveAiConfigToStorage();

                this.updateProgress(100, '处理完成');
                this.hideProgress(600);
                this.showToast(`处理完成：成功 ${data.success_count} 个`, 'success');
            } catch (error) {
                this.hideProgress();
                this.showToast(`处理失败: ${error.message}`, 'error');
            } finally {
                this.processingFiles = false;
            }
        },
        clearUploads() {
            this.uploadedFiles = [];
            this.uploadFolderStats = null;
            this.resetPipeline();
            this.$refs.fileInput.value = '';
            this.$refs.folderInput.value = '';
            this.showToast('已清空上传状态', 'info');
        }
};

if (typeof module !== 'undefined' && module.exports) {
    module.exports = { uploadMethods };
}

if (typeof window !== 'undefined') {
    window.MusicMetaCleanerMethodModules = window.MusicMetaCleanerMethodModules || {};
    window.MusicMetaCleanerMethodModules['upload'] = uploadMethods;
}
