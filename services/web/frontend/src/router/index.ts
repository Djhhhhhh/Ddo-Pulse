import { createRouter, createWebHistory } from "vue-router";
import DashboardView from "../views/DashboardView.vue";
import ArticlesView from "../views/ArticlesView.vue";
import ArticleDetailView from "../views/ArticleDetailView.vue";
import SettingsView from "../views/SettingsView.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", name: "dashboard", component: DashboardView },
    { path: "/articles", name: "articles", component: ArticlesView },
    { path: "/articles/:id", name: "article", component: ArticleDetailView },
    { path: "/settings", name: "settings", component: SettingsView },
  ],
});

export default router;
