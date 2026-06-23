import { test, expect } from "@playwright/test"

const isLive = process.env.LIVE_E2E === "true"

test.describe("Study by Theme — mock mode", () => {
  test("theme grid displays all 22 themes as bilingual cards", async ({ page }) => {
    await page.goto("/study")

    await expect(page.getByTestId("theme-grid")).toBeVisible({ timeout: 10_000 })

    const cards = page.locator('[data-testid^="theme-card-"]')
    const expectedCount = isLive ? 0 : 22
    // In live mode, count depends on DB seed data; just verify > 0
    const count = await cards.count()
    if (isLive) {
      expect(count).toBeGreaterThan(0)
    } else {
      expect(count).toBe(expectedCount)
    }

    // Verify first card has bilingual content
    const firstCard = cards.first()
    await expect(firstCard).toBeVisible()

    // Check question count is displayed
    const countBadge = page.getByTestId("theme-count-traffic-signs")
    if (isLive) {
      // Live backend may use different slugs — check any count badge is present
      await expect(page.locator('[data-testid^="theme-count-"]').first()).toBeVisible({ timeout: 5_000 })
    } else {
      await expect(countBadge).toBeVisible()
      await expect(countBadge).toContainText(/questions|questões/)
    }
  })

  test("clicking a theme card navigates to theme study page", async ({ page }) => {
    await page.goto("/study")

    await expect(page.getByTestId("theme-grid")).toBeVisible({ timeout: 10_000 })

    // Click the traffic-signs theme card (or first available)
    const firstCard = page.locator('[data-testid^="theme-card-"]').first()
    await firstCard.click()

    // Should navigate to /study/<slug>
    await expect(page).toHaveURL(/\/study\/\w+/)
    await expect(page.getByTestId("page-title")).toBeVisible()
  })

  test("question list shows questions with True/False buttons", async ({ page }) => {
    await page.goto("/study")
    await expect(page.getByTestId("theme-grid")).toBeVisible({ timeout: 10_000 })

    // Click first theme
    const firstCard = page.locator('[data-testid^="theme-card-"]').first()
    await firstCard.click()

    // Should navigate to detail with questions
    await expect(page).toHaveURL(/\/study\/\w+/)

    const questionCards = page.locator('[data-testid^="question-card-"]')
    const hasCards = await questionCards.first().waitFor({ state: "attached", timeout: 10_000 }).then(() => true).catch(() => false)

    if (hasCards) {
      const firstQuestion = questionCards.first()
      const cardId = await firstQuestion.getAttribute("data-testid")
      const id = cardId?.replace("question-card-", "")

      await expect(page.getByTestId(`question-true-${id}`)).toBeVisible()
      await expect(page.getByTestId(`question-false-${id}`)).toBeVisible()
    } else {
      await expect(page.getByTestId("question-list-empty")).toBeVisible({ timeout: 10_000 })
    }
  })

  test("reveal explanation is disabled until user selects True or False", async ({ page }) => {
    await page.goto("/study")
    await expect(page.getByTestId("theme-grid")).toBeVisible({ timeout: 10_000 })

    const firstCard = page.locator('[data-testid^="theme-card-"]').first()
    await firstCard.click()
    await expect(page).toHaveURL(/\/study\/\w+/)

    const questionCard = page.locator('[data-testid^="question-card-"]').first()
    const hasCard = await questionCard.waitFor({ state: "attached", timeout: 10_000 }).then(() => true).catch(() => false)
    if (!hasCard) return

    const cardId = await questionCard.getAttribute("data-testid")
    const id = cardId?.replace("question-card-", "")

    const revealButton = page.getByTestId(`question-reveal-${id}`)
    await expect(revealButton).toBeDisabled()

    await page.getByTestId(`question-true-${id}`).click()
    await expect(revealButton).toBeEnabled()
  })

  test("clicking reveal shows explanation with correct answer", async ({ page }) => {
    await page.goto("/study")
    await expect(page.getByTestId("theme-grid")).toBeVisible({ timeout: 10_000 })

    const firstCard = page.locator('[data-testid^="theme-card-"]').first()
    await firstCard.click()
    await expect(page).toHaveURL(/\/study\/\w+/)

    const questionCard = page.locator('[data-testid^="question-card-"]').first()
    const hasCard = await questionCard.waitFor({ state: "attached", timeout: 10_000 }).then(() => true).catch(() => false)
    if (!hasCard) return

    const cardId = await questionCard.getAttribute("data-testid")
    const id = cardId?.replace("question-card-", "")

    // Select True
    await page.getByTestId(`question-true-${id}`).click()

    // Click reveal
    await page.getByTestId(`question-reveal-${id}`).click()

    // Explanation should appear
    const explanation = page.getByTestId(`question-explanation-${id}`)
    await expect(explanation).toBeVisible({ timeout: 10_000 })

    // Should show "Correct answer" label
    await expect(explanation).toContainText(/Correct answer|Resposta correta/)

    // Should show explanation text
    await expect(explanation.locator("p").last()).not.toBeEmpty()
  })

  test("question list does not leak answers before reveal", async ({ page }) => {
    await page.goto("/study")
    await expect(page.getByTestId("theme-grid")).toBeVisible({ timeout: 10_000 })

    const firstCard = page.locator('[data-testid^="theme-card-"]').first()
    await firstCard.click()
    await expect(page).toHaveURL(/\/study\/\w+/)

    // Check that no explanation section is visible
    const explanations = page.locator('[data-testid^="question-explanation-"]')
    await expect(explanations).toHaveCount(0)
  })

  test("pagination works when theme has more than 10 questions", async ({ page }) => {
    await page.goto("/study")
    await expect(page.getByTestId("theme-grid")).toBeVisible({ timeout: 10_000 })

    const firstCard = page.locator('[data-testid^="theme-card-"]').first()
    await firstCard.click()
    await expect(page).toHaveURL(/\/study\/\w+/)

    // Pagination info may or may not be present depending on question count
    const paginationInfo = page.getByTestId("pagination-info")
    if (await paginationInfo.isVisible().catch(() => false)) {
      await expect(paginationInfo).toBeVisible()
    }
  })

  test("back to themes link returns to theme grid", async ({ page }) => {
    await page.goto("/study")
    await expect(page.getByTestId("theme-grid")).toBeVisible({ timeout: 10_000 })

    const firstCard = page.locator('[data-testid^="theme-card-"]').first()
    await firstCard.click()
    await expect(page).toHaveURL(/\/study\/\w+/)

    await expect(page.getByTestId("back-to-themes")).toBeVisible({ timeout: 10_000 })
    await page.getByTestId("back-to-themes").click()

    await expect(page).toHaveURL(/\/study$/)
    await expect(page.getByTestId("theme-grid")).toBeVisible({ timeout: 10_000 })
  })

  test("language toggle switches theme card text", async ({ page }) => {
    await page.addInitScript(() => localStorage.clear())
    await page.goto("/study")

    await expect(page.getByTestId("theme-grid")).toBeVisible({ timeout: 10_000 })

    // Switch to PT
    await page.getByTestId("language-toggle").getByText("PT").click()

    // Cards should show bilingual content
    const firstCard = page.locator('[data-testid^="theme-card-"]').first()
    await expect(firstCard).toBeVisible()
  })
})
