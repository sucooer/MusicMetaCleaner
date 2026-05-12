const createVueApp = (typeof Vue !== 'undefined' && Vue.createApp) ? Vue.createApp : null;
const stateModule = (typeof window !== 'undefined' && window.MusicMetaCleanerState)
    ? window.MusicMetaCleanerState
    : require('./js/state.js');
const methodsModule = (typeof window !== 'undefined' && window.MusicMetaCleanerMethods)
    ? window.MusicMetaCleanerMethods
    : require('./js/methods.js');

const createInitialStateFn = stateModule.createInitialState;
const appComputedMap = stateModule.appComputed;
const appMethodsMap = methodsModule.appMethods;

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
        data: createInitialStateFn,
        computed: appComputedMap,
        mounted: handleMounted,
        methods: appMethodsMap
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
        createInitialState: createInitialStateFn,
        createAppOptions,
        appMethods: appMethodsMap,
        mountBrowserApp
    };
}

if (typeof window !== 'undefined' && createVueApp) {
    mountBrowserApp();
}
