const pathMethods = {
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
};

if (typeof module !== 'undefined' && module.exports) {
    module.exports = { pathMethods };
}

if (typeof window !== 'undefined') {
    window.MusicMetaCleanerMethodModules = window.MusicMetaCleanerMethodModules || {};
    window.MusicMetaCleanerMethodModules['path'] = pathMethods;
}
