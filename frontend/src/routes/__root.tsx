import { useEffect } from "react"
import { createRootRoute, Link, Outlet } from "@tanstack/react-router"
import { useTranslation } from "react-i18next"
import { Button } from "@/components/ui/button"
import { useUIStore } from "@/store/ui"
import i18n from "@/i18n/i18n"

export const Route = createRootRoute({
  component: RootLayout,
})

function RootLayout() {
  const { t } = useTranslation()
  const language = useUIStore((s) => s.language)
  const setLanguage = useUIStore((s) => s.setLanguage)

  useEffect(() => {
    i18n.changeLanguage(language)
  }, [language])

  const navItems = [
    { to: "/", label: t("nav.home") },
    { to: "/study", label: t("nav.study") },
    { to: "/mock-test", label: t("nav.mockTest") },
    { to: "/skill-test", label: t("nav.skillTest") },
    { to: "/teacher", label: t("nav.teacher") },
    { to: "/plan", label: t("nav.plan") },
    { to: "/settings", label: t("nav.settings") },
  ]

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b">
        <div className="container mx-auto flex h-14 items-center justify-between px-4">
          <span className="text-lg font-bold">JP Drivers Test Trainer</span>
          <nav data-testid="language-toggle" className="flex items-center gap-1">
            <Button
              variant={language === "en" ? "default" : "ghost"}
              size="sm"
              onClick={() => setLanguage("en")}
              aria-pressed={language === "en"}
            >
              EN
            </Button>
            <Button
              variant={language === "pt" ? "default" : "ghost"}
              size="sm"
              onClick={() => setLanguage("pt")}
              aria-pressed={language === "pt"}
            >
              PT
            </Button>
          </nav>
        </div>
        <nav className="container mx-auto flex h-10 items-center gap-4 px-4">
          {navItems.map((item) => (
            <Link
              key={item.to}
              to={item.to}
              className="text-sm font-medium text-muted-foreground hover:text-foreground"
              activeProps={{ className: "text-foreground" }}
            >
              {item.label}
            </Link>
          ))}
        </nav>
      </header>
      <main>
        <Outlet />
      </main>
    </div>
  )
}