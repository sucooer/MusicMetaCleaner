const createVueApp = (typeof Vue !== 'undefined' && Vue.createApp) ? Vue.createApp : null;
const stateModule = (typeof window !== 'undefined' && window.MusicMetaCleanerState)
    ? window.MusicMetaCleanerState
    : require('./js/state.js');
const methodsModule = (typeof window !== 'undefined' && window.MusicMetaCleanerMethods)
    ? window.MusicMetaCleanerMethods
    : require('./js/methods.js');

const { createInitialState, appComputed } = stateModule;
const { appMethods } = methodsModule;

function handleMounted() {
    this.toastInstance = new bootstrap.Toast(this.$refs.toastEl, { delay: 2600 });
    this.pathPickerModal = new bootstrap.Modal(this.$refs.pathPickerModalEl);
    this.executionLogsModal = new bootstrap.Modal(this.$refs.executionLogsModalEl);
    this.loadRuntimeConfig();
    this.loadAiConfigFromStorage();
    this.loadKeywordSettings();
    this.loadExecutionLogs();
}

function createAppOptions() {
    return {
        data: createInitialState,
        computed: appComputed,
        mounted: handleMounted,
        methods: appMethods
    };
}

function mountBrowserApp() {
    if (!createVueApp) return null;
    const vueApp = createVueApp(createAppOptions());
    vueApp.mount('#app');
    return vueApp;
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        createInitialState,
        createAppOptions,
        appMethods,
        mountBrowserApp
    };
}

if (typeof window !== 'undefined' && createVueApp) {
    mountBrowserApp();
}
