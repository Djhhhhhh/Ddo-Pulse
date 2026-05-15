<script setup lang="ts">
import { onMounted, ref } from "vue";
import { RouterLink, RouterView } from "vue-router";
import { loadAppConfig } from "../config";

const brand = ref("Ddo-Pulse");

onMounted(async () => {
  const cfg = await loadAppConfig();
  brand.value = cfg.title || "Ddo-Pulse";
  document.title = brand.value;
});
</script>

<template>
  <div class="layout">
    <header class="header">
      <RouterLink to="/" class="brand">{{ brand }}</RouterLink>
      <nav class="nav">
        <RouterLink to="/">仪表盘</RouterLink>
        <RouterLink to="/articles">文章</RouterLink>
        <RouterLink to="/settings">配置</RouterLink>
      </nav>
    </header>
    <main class="main">
      <RouterView v-slot="{ Component }">
        <transition name="fade-slide" mode="out-in">
          <component :is="Component" />
        </transition>
      </RouterView>
    </main>
  </div>
</template>

<style scoped>
.layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 32px;
  border-bottom: 1px solid var(--border);
}
.brand {
  font-size: 1.25rem;
  font-weight: 500;
  text-decoration: none;
  color: var(--text);
}
.nav {
  display: flex;
  gap: 24px;
}
.nav a {
  text-decoration: none;
  color: var(--text-secondary);
  font-size: 1rem;
}
.nav a.router-link-active {
  color: var(--text);
}
.main {
  flex: 1;
  max-width: 1320px;
  width: 100%;
  margin: 0 auto;
  padding: 32px 24px 64px;
}
</style>
