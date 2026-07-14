import { createRouter, createWebHistory } from "vue-router";
import DashboardView from "../views/DashboardView.vue";
import ArticlesView from "../views/ArticlesView.vue";
import ArticleDetailView from "../views/ArticleDetailView.vue";
import SettingsView from "../views/SettingsView.vue";
import ReportsView from "../views/ReportsView.vue";
import ReportDetailView from "../views/ReportDetailView.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", name: "dashboard", component: DashboardView },
    { path: "/articles", name: "articles", component: ArticlesView },
    { path: "/articles/:id", name: "article", component: ArticleDetailView },
    { path: "/settings", name: "settings", component: SettingsView },
    { path: "/reports", name: "reports", component: ReportsView },
    { path: "/reports/:timestamp", name: "report-detail", component: ReportDetailView },
  ],
});

export default router;
