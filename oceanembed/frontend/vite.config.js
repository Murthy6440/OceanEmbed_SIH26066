import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// OceanEmbed frontend (SIH26066 prototype)
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    open: false,
  },
});
