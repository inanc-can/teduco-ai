"use client"

import * as React from "react"
import { Sun, Moon } from "lucide-react"
import { useTheme } from "next-themes"

export default function DarkToggle() {
  const { theme, setTheme, resolvedTheme } = useTheme()
  const [mounted, setMounted] = React.useState(false)

  React.useEffect(() => setMounted(true), [])

  if (!mounted) {
    return (
      <button className="ml-auto inline-flex items-center justify-center rounded-md p-1 text-sm">
        <Moon className="w-4 h-4" />
      </button>
    )
  }

  const isDark = resolvedTheme === "dark"

  return (
    <button
      aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
      onClick={() => setTheme(isDark ? "light" : "dark")}
      className="ml-auto inline-flex items-center justify-center rounded-md p-1 text-sm hover:bg-gray-100 dark:hover:bg-gray-800"
    >
      {isDark ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
    </button>
  )
}
