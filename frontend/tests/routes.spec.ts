import { test, expect } from "@playwright/test"

const routes = [
  { path: "/", en: "Dashboard", pt: "Painel" },
  { path: "/study", en: "Study by Theme", pt: "Estudo por Tema" },
  { path: "/mock-test", en: "Mock Test", pt: "Simulado" },
  { path: "/skill-test", en: "Skill Test", pt: "Teste de Habilidade" },
  { path: "/teacher", en: "Teacher", pt: "Professor" },
  { path: "/plan", en: "Study Plan", pt: "Plano de Estudo" },
  { path: "/settings", en: "Settings", pt: "Configurações" },
]

for (const route of routes) {
  test(`page title on ${route.path} renders EN text by default`, async ({ page }) => {
    await page.addInitScript(() => localStorage.clear())
    await page.goto(route.path)

    await expect(page.getByTestId("page-title")).toHaveText(route.en)
  })

  test(`page title on ${route.path} switches to PT when language toggled`, async ({ page }) => {
    await page.addInitScript(() => localStorage.clear())
    await page.goto(route.path)

    await expect(page.getByTestId("page-title")).toHaveText(route.en)

    const ptButton = page.getByTestId("language-toggle").getByText("PT")
    await ptButton.click()

    await expect(page.getByTestId("page-title")).toHaveText(route.pt)
  })
}