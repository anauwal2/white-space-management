import { createApp } from "vue";
import ElementPlus from 'element-plus';
import 'element-plus/dist/index.css';
import * as ElementPlusIconsVue from '@element-plus/icons-vue';
import router from "../router";
import App from "./app.vue";
import { initComponents } from "../components";
import "../assets/style/main.css";

const app = createApp(App);

// Register Element Plus
app.use(ElementPlus);


// Register all Element Plus icons
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component);
}

app.use(router);

initComponents(app);

app.mount("#app");