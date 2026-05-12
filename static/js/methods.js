const appMethods = {
        loadRuntimeConfig() {
            const config = window.__MUSIC_META_CLEANER_RUNTIME__ || {};
            const defaultPath = String(config.defaultPath || config.default_path || '').trim();
            if (!this.pathForm.path && defaultPath) {
                this.pathForm.path = defaultPath;
            }
        },
        async loadExecutionLogs(showToast = false) {
            this.executionLogs.loading = true;
            try {
                const response = await fetch('/execution_logs?limit=20');
                const data = await response.json();
                if (!response.ok || data.error) {
                    throw new Error(data.error || `HTTP ${response.status}`);
                }
                this.executionLogs.items = Array.isArray(data.logs) ? data.logs : [];
                this.executionLogs.total = Number(data.total || 0);
                if (showToast) {
                    this.showToast('执行日志已刷新', 'success');
                }
            } catch (error) {
                this.showToast(`加载执行日志失败: ${error.message}`, 'error');
            } finally {
                this.executionLogs.loading = false;
            }
        },
        async openExecutionLogs() {
            await this.loadExecutionLogs();
            this.executionLogsModal.show();
        },
        splitKeywordDraft(rawValue) {
            if (!rawValue) return [];
            return String(rawValue)
                .split(/[\n,，]+/)
                .map(item => item.trim())
                .filter(Boolean);
        },
        mergeKeywords(items) {
            const merged = [];
            const seen = new Set();
            (items || []).forEach((item) => {
                const keyword = String(item || '').trim();
                if (!keyword || seen.has(keyword)) return;
                seen.add(keyword);
                merged.push(keyword);
            });
            return merged;
        },
        appendKeywordDraft() {
            const incoming = this.splitKeywordDraft(this.keywordSettings.draft);
            if (incoming.length === 0) {
                this.showToast('请输入要添加的关键词', 'warning');
                return;
            }
            this.keywordSettings.keywords = this.mergeKeywords([
                ...this.keywordSettings.keywords,
                ...incoming
            ]);
            this.keywordSettings.draft = '';
        },
        removeKeyword(keyword) {
            this.keywordSettings.keywords = this.keywordSettings.keywords.filter(item => item !== keyword);
        },
        async loadKeywordSettings(showToast = false) {
            this.keywordSettings.loading = true;
            try {
                const response = await fetch('/settings/lyrics_keywords');
                const data = await response.json();
                if (!response.ok || data.error) {
                    throw new Error(data.error || `HTTP ${response.status}`);
                }
                this.keywordSettings.keywords = this.mergeKeywords(data.keywords || []);
                this.keywordSettings.defaultKeywords = this.mergeKeywords(data.default_keywords || []);
                this.keywordSettings.savedAt = data.saved_at || '';
                if (showToast) {
                    this.showToast('关键词设置已刷新', 'success');
                }
            } catch (error) {
                this.showToast(`加载关键词失败: ${error.message}`, 'error');
            } finally {
                this.keywordSettings.loading = false;
            }
        },
        async restoreDefaultKeywords() {
            if (!this.keywordSettings.defaultKeywords.length) {
                this.showToast('没有可恢复的默认关键词', 'warning');
                return;
            }
            this.keywordSettings.keywords = [...this.keywordSettings.defaultKeywords];
            await this.saveKeywordSettings();
        },
        async saveKeywordSettings() {
            this.keywordSettings.saving = true;
            try {
                const response = await fetch('/settings/lyrics_keywords', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        keywords: this.mergeKeywords(this.keywordSettings.keywords)
                    })
                });
                const data = await response.json();
                if (!response.ok || data.error) {
                    throw new Error(data.error || `HTTP ${response.status}`);
                }
                this.keywordSettings.keywords = this.mergeKeywords(data.keywords || []);
                this.keywordSettings.defaultKeywords = this.mergeKeywords(data.default_keywords || []);
                this.keywordSettings.savedAt = data.saved_at || '';
                this.keywordSettings.draft = '';
                this.showToast('关键词设置已保存到服务器', 'success');
            } catch (error) {
                this.showToast(`保存关键词失败: ${error.message}`, 'error');
            } finally {
                this.keywordSettings.saving = false;
            }
        },
        loadAiConfigFromStorage() {
            try {
                const raw = window.localStorage.getItem('music_meta_cleaner_ai_config');
                if (!raw) return;
                const parsed = JSON.parse(raw);
                if (!parsed || typeof parsed !== 'object') return;
                this.aiEnabled = parsed.aiEnabled !== false;
                this.aiConfig.baseUrl = String(parsed.baseUrl || '');
                this.aiConfig.model = String(parsed.model || '');
                this.aiConfig.apiKey = String(parsed.apiKey || '');
                this.aiConfig.timeout = String(parsed.timeout || '6');
                this.aiConfigSavedAt = String(parsed.savedAt || '');
            } catch (_) {}
        },
        saveAiConfigToStorage() {
            try {
                const savedAt = new Date().toLocaleString();
                const payload = {
                    aiEnabled: this.aiEnabled,
                    baseUrl: this.aiConfig.baseUrl,
                    model: this.aiConfig.model,
                    apiKey: this.aiConfig.apiKey,
                    timeout: this.aiConfig.timeout,
                    savedAt
                };
                window.localStorage.setItem('music_meta_cleaner_ai_config', JSON.stringify(payload));
                this.aiConfigSavedAt = savedAt;
                this.showToast('AI 配置已保存到浏览器', 'success');
            } catch (_) {}
        },
        clearAiConfigStorage() {
            try {
                window.localStorage.removeItem('music_meta_cleaner_ai_config');
            } catch (_) {}
            this.aiEnabled = true;
            this.aiConfig.baseUrl = '';
            this.aiConfig.model = '';
            this.aiConfig.apiKey = '';
            this.aiConfig.timeout = '6';
            this.aiConfigSavedAt = '';
            this.showToast('已清空 AI 配置', 'warning');
        },
        basename(path) {
            if (!path) return '';
            return String(path).split(/[/\\]/).pop();
        },
        showToast(message, type = 'info') {
            this.toastMessage = message;
            const el = this.$refs.toastEl;
            el.className = 'toast';
            if (type === 'success') {
                el.classList.add('bg-success', 'text-white');
            } else if (type === 'warning') {
                el.classList.add('bg-warning');
            } else if (type === 'error') {
                el.classList.add('bg-danger', 'text-white');
            }
            this.toastInstance.show();
        },
        showProgress(text = '处理中...', percent = 0) {
            this.progress.visible = true;
            this.progress.text = text;
            this.progress.percent = percent;
        },
        updateProgress(percent, text = '') {
            this.progress.percent = percent;
            if (text) this.progress.text = text;
        },
        hideProgress(delay = 0) {
            setTimeout(() => {
                this.progress.visible = false;
                this.progress.percent = 0;
            }, delay);
        },
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
        parseFilterExtInput(rawValue) {
            if (!rawValue) return null;
            const items = rawValue
                .split(',')
                .map(item => item.trim().toLowerCase())
                .filter(Boolean);
            const normalized = items.map(ext => ext.startsWith('.') ? ext : `.${ext}`);
            return normalized.length ? normalized : null;
        },
        async processPath() {
            if (!this.pathForm.path) {
                this.showToast('请输入路径', 'warning');
                return;
            }

            this.pathProcessing = true;
            this.showProgress(`按路径处理: ${this.pathForm.path}`, 10);

            try {
                const payload = {
                    path: this.pathForm.path,
                    dry_run: this.pathForm.dryRun,
                    backup: this.pathForm.backup,
                    ai_enabled: this.aiEnabled,
                    ai_config: this.aiConfig,
                    filter_ext: this.parseFilterExtInput(this.pathForm.filterExt)
                };

                const response = await fetch('/process_path', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });

                const data = await response.json();
                if (!response.ok || data.error) {
                    throw new Error(data.error || `HTTP ${response.status}`);
                }

                this.pathResult = data;
                this.pathPreviewExpanded = false;
                this.pathRenameExpanded = false;
                this.saveAiConfigToStorage();
                this.updateProgress(100, '路径模式完成');
                this.hideProgress(600);
                this.showToast('路径模式执行完成', 'success');
            } catch (error) {
                this.hideProgress();
                this.showToast(`路径模式失败: ${error.message}`, 'error');
            } finally {
                this.pathProcessing = false;
            }
        },
        async browsePath(targetPath = '') {
            this.pathPicker.loading = true;
            this.pathPicker.error = '';
            try {
                const response = await fetch('/browse_path', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ path: targetPath || this.pathForm.path || '' })
                });
                const data = await response.json();
                if (!response.ok || data.error) {
                    throw new Error(data.error || `HTTP ${response.status}`);
                }
                this.pathPicker.currentPath = data.current_path || '';
                this.pathPicker.parentPath = data.parent_path || '';
                this.pathPicker.directories = data.directories || [];
            } catch (error) {
                this.pathPicker.error = error.message;
            } finally {
                this.pathPicker.loading = false;
            }
        },
        async openPathPicker() {
            await this.browsePath(this.pathForm.path);
            this.pathPickerModal.show();
        },
        selectCurrentPath() {
            if (!this.pathPicker.currentPath) return;
            this.pathForm.path = this.pathPicker.currentPath;
            this.pathPickerModal.hide();
            this.showToast('已选择路径', 'success');
        },
        async renameProcessedFile(file) {
            const currentName = this.basename(file.display_name || file.original_filename || '');
            const newName = window.prompt('请输入新文件名（可不带扩展名）', currentName);
            if (!newName || !newName.trim()) return;

            try {
                const response = await fetch('/rename_processed', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        processed_filename: file.processed_filename,
                        new_name: newName.trim()
                    })
                });
                const data = await response.json();
                if (!response.ok || data.error) {
                    throw new Error(data.error || `HTTP ${response.status}`);
                }

                file.processed_filename = data.processed_filename;
                file.display_name = data.display_name || file.display_name;
                this.showToast('重命名成功', 'success');
            } catch (error) {
                this.showToast(`重命名失败: ${error.message}`, 'error');
            }
        },
        async renamePathFile(item) {
            const currentName = this.basename(item.display_name || item.path || '');
            const newName = window.prompt('请输入新文件名（可不带扩展名）', currentName);
            if (!newName || !newName.trim()) return;

            try {
                const response = await fetch('/rename_path_file', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        path: item.path,
                        new_name: newName.trim()
                    })
                });
                const data = await response.json();
                if (!response.ok || data.error) {
                    throw new Error(data.error || `HTTP ${response.status}`);
                }

                item.path = data.path || item.path;
                item.display_name = data.display_name || this.basename(item.path);
                this.showToast('重命名成功', 'success');
            } catch (error) {
                this.showToast(`重命名失败: ${error.message}`, 'error');
            }
        },
        buildTemplateName(item, template, index) {
            const sourceName = this.basename(item.display_name || item.path || '');
            const extMatch = sourceName.match(/(\.[^.]+)$/);
            const ext = extMatch ? extMatch[1] : '';
            const stem = ext ? sourceName.slice(0, -ext.length) : sourceName;

            const parts = stem.split(/\s*-\s*/).map(s => s.trim()).filter(Boolean);
            const trackMatch = stem.match(/^\s*(\d{1,3})\b/);
            const track = trackMatch ? trackMatch[1].padStart(2, '0') : String(index + 1).padStart(2, '0');
            const title = parts.length >= 2 ? parts[1] : stem;
            const artist = parts.length >= 3 ? parts[2] : '';

            let result = (template || '{track}.{title}')
                .replaceAll('{track}', track)
                .replaceAll('{title}', title)
                .replaceAll('{artist}', artist)
                .replaceAll('{index}', String(index + 1))
                .replaceAll('{ext}', ext);

            result = result.replace(/[\\/:*?"<>|\x00-\x1f]+/g, '_').trim();
            return result || stem;
        },
        async renamePathFilesByTemplate() {
            if (!this.pathResult || this.pathResult.dry_run || !this.pathResult.processed_files?.length) return;
            if (!this.renameTemplate) {
                this.showToast('请先输入模板', 'warning');
                return;
            }

            this.renamingBatch = true;
            let ok = 0;
            let fail = 0;

            for (let i = 0; i < this.pathResult.processed_files.length; i += 1) {
                const item = this.pathResult.processed_files[i];
                const newName = this.buildTemplateName(item, this.renameTemplate, i);
                try {
                    const response = await fetch('/rename_path_file', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ path: item.path, new_name: newName })
                    });
                    const data = await response.json();
                    if (!response.ok || data.error) {
                        throw new Error(data.error || `HTTP ${response.status}`);
                    }
                    item.path = data.path || item.path;
                    item.display_name = data.display_name || this.basename(item.path);
                    ok += 1;
                } catch (error) {
                    fail += 1;
                }
            }

            this.renamingBatch = false;
            this.showToast(`批量重命名完成：成功 ${ok}，失败 ${fail}`, fail ? 'warning' : 'success');
        },
        downloadBlob(blob, filename) {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
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
    module.exports = { appMethods };
}

if (typeof window !== 'undefined') {
    window.MusicMetaCleanerMethods = { appMethods };
}
