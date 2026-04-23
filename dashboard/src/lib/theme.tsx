import React, { createContext, useContext, useEffect, useState } from "react";

// ─── Types ───
export type Theme = "night" | "light";

interface ThemeContextValue {
  theme: Theme;
  toggleTheme: (event?: React.MouseEvent) => void;
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

  const toggleTheme = (event?: React.MouseEvent) => {
    const newTheme = theme === "night" ? "light" : "night";

    // Fallback for browsers that don't support View Transitions
    if (!document.startViewTransition || !event) {
      setTheme(newTheme);
      return;
    }

    // Get click position or fallback to center
    const x = event.clientX;
    const y = event.clientY;
    const endRadius = Math.hypot(
      Math.max(x, innerWidth - x),
      Math.max(y, innerHeight - y)
    );

    const transition = document.startViewTransition(() => {
      setTheme(newTheme);
    });

    transition.ready.then(() => {
      const clipPath = [
        `circle(0px at ${x}px ${y}px)`,
        `circle(${endRadius}px at ${x}px ${y}px)`,
      ];

      document.documentElement.animate(
        {
          clipPath: clipPath,
        },
        {
          duration: 400,
          easing: "ease-in-out",
          pseudoElement: "::view-transition-new(root)",
        }
      );
    });
  };

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}
