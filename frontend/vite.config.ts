import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";
import { VitePWA } from "vite-plugin-pwa";

export default defineConfig({
  define: {
    __APP_VERSION__: JSON.stringify("0.1.0"),
  },
  plugins: [
    react(),
    VitePWA({
      registerType: "prompt",
      injectRegister: null,
      includeAssets: ["icon-192.png", "icon-512.png", "icon-maskable-512.png", "apple-touch-icon.png"],
      manifest: {
        id: "/",
        name: "一造学伴",
        short_name: "一造学伴",
        description: "一级造价工程师学习与复习平台",
        theme_color: "#173453",
        background_color: "#f5f7f8",
        display: "standalone",
        lang: "zh-CN",
        start_url: "/",
        scope: "/",
        icons: [
          { src: "/icon-192.png", sizes: "192x192", type: "image/png", purpose: "any" },
          { src: "/icon-512.png", sizes: "512x512", type: "image/png", purpose: "any" },
          { src: "/icon-maskable-512.png", sizes: "512x512", type: "image/png", purpose: "maskable" },
        ],
      },
      workbox: {
        globPatterns: ["**/*.{js,css,html}"],
        cleanupOutdatedCaches: true,
        navigateFallback: "/index.html",
        navigateFallbackDenylist: [
          /^\/api(?:\/|$)/,
          /^\/admin(?:\/|$)/,
          /^\/login(?:\/|$)/,
          /^\/user(?:\/|$)/,
          /^\/submit(?:\/|$)/,
        ],
        runtimeCaching: [],
      },
    }),
  ],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://127.0.0.1:8000",
    },
  },
  preview: {
    port: 4173,
    proxy: {
      "/api": "http://127.0.0.1:8000",
    },
  },
});
