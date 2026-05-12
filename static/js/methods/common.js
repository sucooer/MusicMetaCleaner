const commonMethods = {
        loadRuntimeConfig() {
            const config = window.__MUSIC_META_CLEANER_RUNTIME__ || {};
            const defaultPath = String(config.defaultPath || config.default_path || '').trim();
            if (!this.pathForm.path && defaultPath) {
                this.pathForm.path = defaultPath;
            }
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
};

if (typeof module !== 'undefined' && module.exports) {
    module.exports = { commonMethods };
}

if (typeof window !== 'undefined') {
    window.MusicMetaCleanerMethodModules = window.MusicMetaCleanerMethodModules || {};
    window.MusicMetaCleanerMethodModules['common'] = commonMethods;
}
