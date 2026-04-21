/// <reference types="vite/client" />

import type { OrbitDesktopBridge } from "./desktop";

declare global {
  interface Window {
    orbitDesktop?: OrbitDesktopBridge;
  }
}
