import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: "autoUpdate",
      includeAssets: ["icons/*.png", "splash/*.png"],
      manifest: {
        name: "Precifica.AI",
        short_name: "Precifica",
        description: "Automação de design para joalherias",
        start_url: "/",
        display: "standalone",
        orientation: "portrait",
        background_color: "#F8F9FA",
        theme_color: "#C9A96E",
        icons: [
          {
            src: "/icons/icon-192.png",
            sizes: "192x192",
            type: "image/png",
          },
          {
            src: "/icons/icon-512.png",
            sizes: "512x512",
            type: "image/png",
            purpose: "any maskable",
          },
        ],
        categories: ["business", "productivity", "design"],
        lang: "pt-BR",
      },
      workbox: {
        globPatterns: ["**/*.{js,css,html,woff2,png,jpg}"],
        runtimeCaching: [
          {
            urlPattern: /^https:\/\/fonts\.googleapis\.com/,
            handler: "CacheFirst",
            options: {
              cacheName: "google-fonts",
              expiration: {
                maxEntries: 10,
                maxAgeSeconds: 60 * 60 * 24 * 365,
              },
            },
          },
          {
            urlPattern: /\/output\/.+\.(jpg|png)$/,
            handler: "CacheFirst",
            options: {
              cacheName: "processed-images",
              expiration: { maxEntries: 50, maxAgeSeconds: 60 * 60 * 24 * 7 },
            },
          },
        ],
      },
    }),
  ],
  server: {
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
      "/output": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
