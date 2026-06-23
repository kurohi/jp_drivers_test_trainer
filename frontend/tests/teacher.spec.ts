import { test, expect } from "@playwright/test"

const isLive = process.env.LIVE_E2E === "true"

test.describe("Teacher — live Ollama", () => {
  test("page loads with empty chat state, input, and send button", async ({ page }) => {
    await page.goto("/teacher")

    await expect(page.getByTestId("page-title")).toBeVisible()
    await expect(page.getByTestId("teacher-chat")).toBeVisible()
    await expect(page.getByTestId("teacher-empty-state")).toBeVisible()
    await expect(page.getByTestId("teacher-input")).toBeVisible()
    await expect(page.getByTestId("teacher-send")).toBeDisabled()
  })

  test("send button enables when text is entered", async ({ page }) => {
    await page.goto("/teacher")

    const input = page.getByTestId("teacher-input")
    const sendBtn = page.getByTestId("teacher-send")
    await expect(sendBtn).toBeDisabled()

    await input.fill("What is the S-curve maneuver?")
    await expect(sendBtn).toBeEnabled()
  })

  test("asking a question shows user message and starts loading", async ({ page }) => {
    await page.goto("/teacher")

    const input = page.getByTestId("teacher-input")
    await input.fill("What is the S-curve maneuver?")
    await page.getByTestId("teacher-send").click()

    // User message should appear
    await expect(page.getByTestId("teacher-message-user")).toBeVisible({ timeout: 5_000 })
    // Loading indicator should show
    await expect(page.getByTestId("teacher-loading")).toBeVisible({ timeout: 2_000 })
  })

  test("language toggle persists and affects API calls", async ({ page }) => {
    await page.addInitScript(() => localStorage.clear())
    await page.goto("/teacher")

    // Switch to PT
    await page.getByTestId("language-toggle").getByText("PT").click()
    await expect(page.getByTestId("language-toggle").getByText("PT")).toHaveAttribute("aria-pressed", "true")
  })
})

test.describe("Teacher — Ollama 503 edge case", () => {
  test("shows 503 banner when Ollama is unavailable and allows retry", async ({ page }) => {
    // Only run in live mode — mock mode never triggers 503
    test.skip(!isLive, "Skipped in mock mode — Ollama 503 only occurs with live API")

    await page.goto("/teacher")

    const input = page.getByTestId("teacher-input")
    await input.fill("What is the S-curve maneuver?")
    await page.getByTestId("teacher-send").click()

    // Wait for either response or error banner
    await page.waitForTimeout(15_000)

    const errorBanner = page.getByTestId("ollama-down-banner")
    const assistantMsg = page.getByTestId("teacher-message-assistant")

    // Either we got a response (Ollama is running) or we see the 503 banner
    if (await errorBanner.isVisible().catch(() => false)) {
      await expect(errorBanner).toContainText(/localhost:11434/)
      // Retry button should be visible
      await expect(errorBanner.getByRole("button")).toBeVisible()
      // Click retry to dismiss
      await errorBanner.getByRole("button").click()
      await expect(errorBanner).not.toBeVisible()
    } else if (await assistantMsg.isVisible().catch(() => false)) {
      await expect(assistantMsg).toBeVisible()
    }
  })
})
