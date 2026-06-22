import { createRoute } from "@tanstack/react-router"
import { useTranslation } from "react-i18next"
import { Route as rootRoute } from "../__root"
import { Button } from "@/components/ui/button"
import { useUIStore } from "@/store/ui"

export const Route = createRoute({
  getParentRoute: () => rootRoute,
  path: "/settings",
  component: SettingsPage,
})

function SettingsPage() {
  const { t } = useTranslation()
  const language = useUIStore((s) => s.language)
  const setLanguage = useUIStore((s) => s.setLanguage)
  const theme = useUIStore((s) => s.theme)
  const toggleTheme = useUIStore((s) => s.toggleTheme)

  return (
    <div className="container mx-auto py-8">
      <h1 data-testid="page-title" className="text-3xl font-bold">
        {t("pageTitle.settings")}
      </h1>

      <div className="mt-6 space-y-6">
        <section>
          <h2 className="text-xl font-semibold">Language</h2>
          <div className="mt-2 flex items-center gap-2">
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
          </div>
        </section>

        <section>
          <h2 className="text-xl font-semibold">Theme</h2>
          <div className="mt-2 flex items-center gap-2">
            <Button
              variant={theme === "light" ? "default" : "ghost"}
              size="sm"
              onClick={() => {
                if (theme === "dark") toggleTheme()
              }}
              aria-pressed={theme === "light"}
            >
              Light
            </Button>
            <Button
              variant={theme === "dark" ? "default" : "ghost"}
              size="sm"
              onClick={() => {
                if (theme === "light") toggleTheme()
              }}
              aria-pressed={theme === "dark"}
            >
              Dark
            </Button>
          </div>
        </section>
      </div>
    </div>
  )
}