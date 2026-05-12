const settingsMethods = {
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
};

if (typeof module !== 'undefined' && module.exports) {
    module.exports = { settingsMethods };
}

if (typeof window !== 'undefined') {
    window.MusicMetaCleanerMethodModules = window.MusicMetaCleanerMethodModules || {};
    window.MusicMetaCleanerMethodModules['settings'] = settingsMethods;
}
