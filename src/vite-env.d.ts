/// <reference types="vite/client" />

declare module 'primevue/config' {
  import { Plugin } from 'vue'
  const plugin: Plugin
  export default plugin
}

declare module '@primevue/themes/aura' {
  const theme: any
  export default theme
}

declare module 'primevue/*' {
  import { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}
