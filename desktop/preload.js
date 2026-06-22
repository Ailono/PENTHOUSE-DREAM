const { contextBridge } = require('electron');

contextBridge.exposeInMainWorld('api', {
  backendUrl: 'http://localhost:8000',
  wsUrl: 'ws://localhost:8000/ws',
});
