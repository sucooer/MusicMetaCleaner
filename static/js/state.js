function createInitialState() {
    return {
            uiMode: 'path',
            dragOver: false,
            uploadedFiles: [],
            uploadFolderStats: null,
            previewFilename: '',
            previewData: null,
            processResult: null,
            processedFiles: [],
            processingFiles: false,
            aiEnabled: true,
            aiConfig: {
                baseUrl: '',
                model: '',
                apiKey: '',
                timeout: '6'
            },
            aiConfigSavedAt: '',
            settingsExpanded: false,
            keywordSettings: {
                loading: false,
                saving: false,
                draft: '',
                keywords: [],
                defaultKeywords: [],
                savedAt: ''
            },
            uploadFailedExpanded: false,
            uploadIgnoredExpanded: false,
            pathProcessing: false,
            pathResult: null,
            pathForm: {
                path: '',
                filterExt: '',
                dryRun: true,
                backup: false
            },
            progress: {
                visible: false,
                percent: 0,
                text: '处理中...'
            },
            toastInstance: null,
            toastMessage: '',
            pathPickerModal: null,
            executionLogsModal: null,
            executionLogs: {
                loading: false,
                items: [],
                total: 0
            },
            renameTemplate: '{track}.{title}{ext}',
            renamingBatch: false,
            pathPreviewExpanded: false,
            pathRenameExpanded: false,
            pathPicker: {
                loading: false,
                currentPath: '',
                parentPath: '',
                directories: [],
                error: ''
            }
    };
}

const appComputed = {
        filesWithLyrics() {
            return this.uploadedFiles.filter(file => file.has_lyrics);
        }
};

if (typeof module !== 'undefined' && module.exports) {
    module.exports = { createInitialState, appComputed };
}

if (typeof window !== 'undefined') {
    window.MusicMetaCleanerState = { createInitialState, appComputed };
}
