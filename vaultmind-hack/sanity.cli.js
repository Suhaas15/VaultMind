import { defineCliConfig } from 'sanity/cli'
export default defineCliConfig({
  api: {
    projectId: '5dsw0p1j',
    dataset: 'production'
  },
  deployment: {
    autoUpdates: true,
    appId: 'ioprtsb2sf4mhh68h6h4t5je',
  }
})