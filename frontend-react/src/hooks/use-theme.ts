import { useTheme } from "next-themes"
import { useEffect, useState } from "react"

export function useThemeAdvanced() {
  const { theme, setTheme, resolvedTheme } = useTheme()
  const [mounted, setMounted] = useState(false)

  // Evita hidratação incorreta
  useEffect(() => {
    setMounted(true)
  }, [])

  const isDark = mounted && (resolvedTheme === "dark")
  const isLight = mounted && (resolvedTheme === "light")
  const isSystem = mounted && (theme === "system")

  const toggleTheme = () => {
    if (isDark) {
      setTheme("light")
    } else {
      setTheme("dark")
    }
  }

  const setLightTheme = () => setTheme("light")
  const setDarkTheme = () => setTheme("dark")
  const setSystemTheme = () => setTheme("system")

  return {
    theme,
    resolvedTheme,
    setTheme,
    mounted,
    isDark,
    isLight,
    isSystem,
    toggleTheme,
    setLightTheme,
    setDarkTheme,
    setSystemTheme,
  }
}

// Hook para detectar preferência do sistema
export function useSystemTheme() {
  const [systemTheme, setSystemTheme] = useState<"light" | "dark">("light")

  useEffect(() => {
    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)")
    
    const handleChange = (e: MediaQueryListEvent) => {
      setSystemTheme(e.matches ? "dark" : "light")
    }

    setSystemTheme(mediaQuery.matches ? "dark" : "light")
    mediaQuery.addEventListener("change", handleChange)

    return () => mediaQuery.removeEventListener("change", handleChange)
  }, [])

  return systemTheme
}

// Hook para animações baseadas no tema
export function useThemeAnimation() {
  const { isDark } = useThemeAdvanced()

  const getAnimationClass = (lightClass: string, darkClass: string) => {
    return isDark ? darkClass : lightClass
  }

  const getTransitionClass = () => {
    return "transition-all duration-300 ease-in-out"
  }

  return {
    getAnimationClass,
    getTransitionClass,
    isDark,
  }
} 