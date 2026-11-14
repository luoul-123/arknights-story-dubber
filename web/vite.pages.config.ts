import {defineConfig} from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  root: "pages",
  base: "/voice-of-terra-for-arknights/",
  plugins: [react()],
  build: {outDir: "../dist-pages", emptyOutDir: true},
});
