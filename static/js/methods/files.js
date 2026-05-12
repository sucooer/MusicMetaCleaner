const filesMethods = {
        resetRenameDialog() {
            this.renameDialog.mode = '';
            this.renameDialog.title = '';
            this.renameDialog.newName = '';
            this.renameDialog.processedFilename = '';
            this.renameDialog.path = '';
            this.renameDialog.fileRef = null;
            this.renameDialog.itemRef = null;
            this.renameDialog.submitting = false;
        },
        openRenameProcessedDialog(file) {
            this.resetRenameDialog();
            this.renameDialog.mode = 'processed';
            this.renameDialog.title = '重命名处理后文件';
            this.renameDialog.newName = this.basename(file.display_name || file.original_filename || '');
            this.renameDialog.processedFilename = file.processed_filename;
            this.renameDialog.fileRef = file;
            this.renameModal.show();
        },
        openRenamePathDialog(item) {
            this.resetRenameDialog();
            this.renameDialog.mode = 'path';
            this.renameDialog.title = '重命名路径模式文件';
            this.renameDialog.newName = this.basename(item.display_name || item.path || '');
            this.renameDialog.path = item.path;
            this.renameDialog.itemRef = item;
            this.renameModal.show();
        },
        async submitRenameDialog() {
            const newName = String(this.renameDialog.newName || '').trim();
            if (!newName) {
                this.showToast('请输入新文件名', 'warning');
                return;
            }

            this.renameDialog.submitting = true;
            try {
                if (this.renameDialog.mode === 'processed') {
                    const response = await fetch('/rename_processed', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            processed_filename: this.renameDialog.processedFilename,
                            new_name: newName
                        })
                    });
                    const data = await response.json();
                    if (!response.ok || data.error) {
                        throw new Error(data.error || `HTTP ${response.status}`);
                    }
                    if (this.renameDialog.fileRef) {
                        this.renameDialog.fileRef.processed_filename = data.processed_filename;
                        this.renameDialog.fileRef.display_name = data.display_name || this.renameDialog.fileRef.display_name;
                    }
                } else if (this.renameDialog.mode === 'path') {
                    const response = await fetch('/rename_path_file', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            path: this.renameDialog.path,
                            new_name: newName
                        })
                    });
                    const data = await response.json();
                    if (!response.ok || data.error) {
                        throw new Error(data.error || `HTTP ${response.status}`);
                    }
                    if (this.renameDialog.itemRef) {
                        this.renameDialog.itemRef.path = data.path || this.renameDialog.itemRef.path;
                        this.renameDialog.itemRef.display_name = data.display_name || this.basename(this.renameDialog.itemRef.path);
                    }
                } else {
                    throw new Error('未知重命名模式');
                }
                this.renameModal.hide();
                this.showToast('重命名成功', 'success');
            } catch (error) {
                this.showToast(`重命名失败: ${error.message}`, 'error');
            } finally {
                this.renameDialog.submitting = false;
            }
        },
        async downloadAll() {
            if (this.processedFiles.length === 0) {
                this.showToast('没有可下载文件', 'warning');
                return;
            }

            const filenames = this.processedFiles.map(f => f.processed_filename);
            this.showProgress('正在打包 ZIP...', 15);

            try {
                const response = await fetch('/download_all', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ filenames })
                });

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }

                this.updateProgress(80, '正在下载 ZIP...');
                const blob = await response.blob();
                const stamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
                this.downloadBlob(blob, `cleaned_audio_files_${stamp}.zip`);
                this.updateProgress(100, '下载完成');
                this.hideProgress(500);
                this.showToast('ZIP 下载完成', 'success');
            } catch (error) {
                this.hideProgress();
                this.showToast(`下载失败: ${error.message}`, 'error');
            }
        },
        downloadSingle(file) {
            const url = `/download/${encodeURIComponent(file.processed_filename)}`;
            const a = document.createElement('a');
            a.href = url;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            this.showToast(`开始下载 ${this.basename(file.display_name || file.original_filename)}`, 'info');
        },
        async exportFailedFiles(failedFiles) {
            if (!failedFiles || failedFiles.length === 0) {
                this.showToast('没有失败文件可导出', 'warning');
                return;
            }

            this.showProgress('导出失败文件列表...', 10);
            try {
                const response = await fetch('/export_failed_files', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ failed_files: failedFiles })
                });

                if (!response.ok) {
                    const data = await response.json();
                    throw new Error(data.error || `HTTP ${response.status}`);
                }

                const blob = await response.blob();
                const stamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
                this.downloadBlob(blob, `failed_files_${stamp}.txt`);
                this.updateProgress(100, '导出完成');
                this.hideProgress(400);
                this.showToast('失败文件列表已导出', 'success');
            } catch (error) {
                this.hideProgress();
                this.showToast(`导出失败: ${error.message}`, 'error');
            }
        },
        async cleanup() {
            this.showProgress('正在清理临时文件...', 20);
            try {
                const response = await fetch('/cleanup', { method: 'POST' });
                const data = await response.json();
                if (!response.ok || data.error) {
                    throw new Error(data.error || `HTTP ${response.status}`);
                }

                this.uploadedFiles = [];
                this.uploadFolderStats = null;
                this.pathResult = null;
                this.resetPipeline();
                this.$refs.fileInput.value = '';
                this.$refs.folderInput.value = '';

                this.updateProgress(100, '清理完成');
                this.hideProgress(500);
                this.showToast('临时文件清理完成', 'success');
            } catch (error) {
                this.hideProgress();
                this.showToast(`清理失败: ${error.message}`, 'error');
            }
        },
};

if (typeof module !== 'undefined' && module.exports) {
    module.exports = { filesMethods };
}

if (typeof window !== 'undefined') {
    window.MusicMetaCleanerMethodModules = window.MusicMetaCleanerMethodModules || {};
    window.MusicMetaCleanerMethodModules['files'] = filesMethods;
}
