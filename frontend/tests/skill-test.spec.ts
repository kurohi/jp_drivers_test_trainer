import { test, expect } from "@playwright/test"

const isLive = process.env.LIVE_E2E === "true"

test.describe("Skill Test — mock mode", () => {
  test("skill grid loads with module cards", async ({ page }) => {
    await page.goto("/skill-test")

    await expect(page.getByTestId("page-title")).toBeVisible()
    await expect(page.getByTestId("skill-grid")).toBeVisible({ timeout: 10_000 })

    const cards = page.locator('[data-testid^="skill-card-"]')
    const count = await cards.count()
    expect(count).toBeGreaterThan(0)
  })

  test("clicking a card navigates to detail page", async ({ page }) => {
    await page.goto("/skill-test")

    await expect(page.getByTestId("skill-grid")).toBeVisible({ timeout: 10_000 })

    // Click the first card
    const firstCard = page.locator('[data-testid^="skill-card-"]').first()
    await firstCard.click()

    // Should navigate to skill detail page
    await expect(page).toHaveURL(/\/skill-test\/\w+/)
    await expect(page.getByTestId("page-title")).toBeVisible()
    await expect(page.getByTestId("skill-diagram-card")).toBeVisible({ timeout: 10_000 })
  })

  test("detail page shows diagram, checklist, mistakes, and pro tip", async ({ page }) => {
    await page.goto("/skill-test")

    await expect(page.getByTestId("skill-grid")).toBeVisible({ timeout: 10_000 })

    const firstCard = page.locator('[data-testid^="skill-card-"]').first()
    await firstCard.click()

    await expect(page.getByTestId("skill-diagram-card")).toBeVisible({ timeout: 10_000 })
    await expect(page.getByTestId("skill-diagram-svg")).toBeVisible()
    await expect(page.getByTestId("skill-checklist-card")).toBeVisible()
    await expect(page.getByTestId("skill-mistakes-card")).toBeVisible()
    await expect(page.getByTestId("skill-protip-card")).toBeVisible()
  })

  test("checklist advances on click", async ({ page }) => {
    await page.goto("/skill-test")

    await expect(page.getByTestId("skill-grid")).toBeVisible({ timeout: 10_000 })

    const firstCard = page.locator('[data-testid^="skill-card-"]').first()
    await firstCard.click()

    await expect(page.getByTestId("skill-checklist-card")).toBeVisible({ timeout: 10_000 })
    await expect(page.getByTestId("checklist-step")).toBeVisible()

    // Click through all checklist steps
    let stepVisible = await page.getByTestId("checklist-step").isVisible().catch(() => false)
    while (stepVisible) {
      await page.getByTestId("checklist-next").click()
      await page.waitForTimeout(300)
      stepVisible = await page.getByTestId("checklist-step").isVisible().catch(() => false)
    }

    // Should show complete state
    await expect(page.getByTestId("checklist-complete")).toBeVisible()
    await expect(page.getByTestId("checklist-reset")).toBeVisible()
  })

  test("back to modules button navigates to skill list", async ({ page }) => {
    await page.goto("/skill-test")

    await expect(page.getByTestId("skill-grid")).toBeVisible({ timeout: 10_000 })

    const firstCard = page.locator('[data-testid^="skill-card-"]').first()
    await firstCard.click()

    await expect(page.getByTestId("back-to-modules")).toBeVisible({ timeout: 10_000 })
    await page.getByTestId("back-to-modules").click()

    await expect(page).toHaveURL(/\/skill-test$/)
    await expect(page.getByTestId("skill-grid")).toBeVisible({ timeout: 10_000 })
  })
})

test.describe("Skill Test — live data", () => {
  test("detail page shows correct data for S-curve module", async ({ page }) => {
    test.skip(!isLive, "Skipped in mock mode — uses live API data")

    await page.goto("/skill-test/s-curve")

    await expect(page.getByTestId("page-title")).toBeVisible({ timeout: 10_000 })
    await expect(page.getByTestId("page-title")).toContainText(/S-Curve|Curva em S/)
    await expect(page.getByTestId("skill-diagram-card")).toBeVisible()
    await expect(page.getByTestId("skill-diagram-svg")).toBeVisible()
  })
})
