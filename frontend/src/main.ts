import { createApp } from "vue"

import App from "./App.vue"
import { router } from "./app/router"
import { pinia } from "./app/stores"
import "./styles/index.css"

createApp(App).use(pinia).use(router).mount("#app")

import { installTaskTooltips } from "./shared/table/task-tooltip"
installTaskTooltips()

