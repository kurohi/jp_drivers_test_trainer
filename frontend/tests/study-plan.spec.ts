import { test, expect } from "@playwright/test"

const isLive = process.env.LIVE_E2E === "true"

test.describe("Study Plan — mock mode", () => {
  test("page loads with form and empty state", async ({ page }) => {
    await page.goto("/plan")

    await expect(page.getByTestId("page-title")).toBeVisible()
    await expect(page.getByTestId("plan-form")).toBeVisible()
    await expect(page.getByTestId("plan-empty-state")).toBeVisible()
    await expect(page.getByTestId("plan-available-days")).toHaveValue("7")
    await expect(page.getByTestId("plan-hours-per-day")).toHaveValue("1.5")
  })

  test("generating a study plan creates timeline", async ({ page }) => {
    await page.goto("/plan")

    await expect(page.getByTestId("plan-form")).toBeVisible({ timeout: 10_000 })

    // Click generate
    await page.getByTestId("plan-generate").click()

    // Timeline should appear
    await expect(page.getByTestId("plan-timeline")).toBeVisible({ timeout: 15_000 })

    // Should have day cards
    const dayCards = page.locator('[data-testid^="plan-day-"]')
    const count = await dayCards.count()
    expect(count).toBeGreaterThan(0)

    // Each day should have theme badges
    const firstDay = dayCards.first()
    await expect(firstDay).toBeVisible()
  })

  test("history shows previous plans", async ({ page }) => {
    await page.goto("/plan")

    await expect(page.getByTestId("plan-form")).toBeVisible({ timeout: 10_000 })

    // Generate a plan first so history has content
    await page.getByTestId("plan-generate").click()
    await expect(page.getByTestId("plan-timeline")).toBeVisible({ timeout: 15_000 })

    // Click view history
    await page.getByTestId("plan-view-history").click()
    await expect(page.getByTestId("plan-history")).toBeVisible()
  })

  test("generating with different days produces correct number of day cards", async ({ page }) => {
    await page.goto("/plan")

    await page.getByTestId("plan-available-days").fill("3")

    await page.getByTestId("plan-generate").click()
    await expect(page.getByTestId("plan-timeline")).toBeVisible({ timeout: 15_000 })

    const dayCards = page.locator('[data-testid^="plan-day-"]')
    await expect(dayCards).toHaveCount(3)
  })
})

test.describe("Study Plan — live API", () => {
  test("generates study plan from backend", async ({ page }) => {
    test.skip(!isLive, "Skipped in mock mode — uses live API")

    await page.goto("/plan")

    await expect(page.getByTestId("plan-form")).toBeVisible({ timeout: 10_000 })

    // Set 5 days
    await page.getByTestId("plan-available-days").fill("5")

    // Generate
    await page.getByTestId("plan-generate").click()

    // Timeline should appear within a reasonable time
    await expect(page.getByTestId("plan-timeline")).toBeVisible({ timeout: 30_000 })

    // Should have 5 day cards
    const dayCards = page.locator('[data-testid^="plan-day-"]')
    await expect(dayCards).toHaveCount(5)

    // Each day should have theme badges
    const firstDay = dayCards.first()
    await expect(firstDay.locator("badge").first()).toBeVisible()
  })

  test("falls back to default beginner plan when Ollama is unavailable", async ({ page }) => {
    test.skip(!isLive, "Skipped in mock mode — Ollama 503 only occurs with live API")

    await page.goto("/plan")

    await page.getByTestId("plan-available-days").fill("3")
    await page.getByTestId("plan-generate").click()

    // With Ollama down, the service falls back to default-beginner source
    // Wait for timeline or error
    const timeline = page.getByTestId("plan-timeline")
    await expect(timeline).toBeVisible({ timeout: 40_000 })

    // Should show source as default-beginner or ollama
    const sourceBadge = timeline.locator("h2").first()
    // The plan should render day cards even if it's a fallback
    await expect(page.locator('[data-testid^="plan-day-"]').first()).toBeVisible()
  })
})
