import { createRootRoute, Outlet } from "@tanstack/react-router"
import { Button } from "@/components/ui/button"
import { useUIStore } from "@/store/ui"

export const Route = createRootRoute({
  component: RootLayout,
})

function RootLayout() {
  const language = useUIStore((s) => s.language)
  const setLanguage = useUIStore((s) => s.setLanguage)

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
      </header>
      <main>
        <Outlet />
      </main>
    </div>
  )
}