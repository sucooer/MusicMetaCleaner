const methodModules = (typeof window !== 'undefined' && window.MusicMetaCleanerMethodModules)
    ? window.MusicMetaCleanerMethodModules
    : {
        common: require('./methods/common.js').commonMethods,
        settings: require('./methods/settings.js').settingsMethods,
        upload: require('./methods/upload.js').uploadMethods,
        path: require('./methods/path.js').pathMethods,
        files: require('./methods/files.js').filesMethods
    };

const appMethods = {
    ...methodModules.common,
    ...methodModules.settings,
    ...methodModules.upload,
    ...methodModules.path,
    ...methodModules.files
};

if (typeof module !== 'undefined' && module.exports) {
    module.exports = { appMethods };
}

if (typeof window !== 'undefined') {
    window.MusicMetaCleanerMethods = { appMethods };
}
