import { test, expect } from "@playwright/test"

test("language toggle is present on root layout", async ({ page }) => {
  await page.goto("/")

  const toggle = page.getByTestId("language-toggle")
  await expect(toggle).toBeVisible()

  const enButton = toggle.getByText("EN")
  const ptButton = toggle.getByText("PT")
  await expect(enButton).toBeVisible()
  await expect(ptButton).toBeVisible()
})

test("clicking PT button switches language", async ({ page }) => {
  await page.goto("/")

  const toggle = page.getByTestId("language-toggle")
  const ptButton = toggle.getByText("PT")

  await ptButton.click()
  await expect(ptButton).toHaveAttribute("aria-pressed", "true")
  await expect(toggle.getByText("EN")).toHaveAttribute("aria-pressed", "false")
})