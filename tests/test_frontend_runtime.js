const assert = require('node:assert');

global.window = {
  __MUSIC_META_CLEANER_RUNTIME__: {
    defaultPath: '/media'
  }
};

const frontend = require('../static/app.js');

const state = frontend.createInitialState();
const methods = frontend.appMethods;

methods.loadRuntimeConfig.call({
  pathForm: state.pathForm
});

assert.equal(state.pathForm.path, '/media');

console.log('frontend runtime config ok');
