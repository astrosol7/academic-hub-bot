import React, { createContext, useContext, useEffect, useState } from "react";

// ─── Types ───
export type Theme = "night" | "light";

interface ThemeContextValue {
  theme: Theme;
  toggleTheme: () => void;
}

// ─── Context ───
const ThemeContext = createContext<ThemeContextValue | null>(null);

export function useTheme(): ThemeContextValue {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error("useTheme must be used within ThemeProvider");
  return ctx;
}

const THEME_KEY = "orbit_theme";

function getStoredTheme(): Theme {
  if (typeof window === "undefined") return "night";
  const stored = window.localStorage.getItem(THEME_KEY);
  if (stored === "light") return "light";
  if (stored === "night") return "night";
  // System preference
  return window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "night";
}

// ─── Provider ───
export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<Theme>(getStoredTheme);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    window.localStorage.setItem(THEME_KEY, theme);
  }, [theme]);

  const toggleTheme = () => setTheme((t) => (t === "night" ? "light" : "night"));

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}
