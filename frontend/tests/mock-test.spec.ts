import { test, expect, type Page } from "@playwright/test"

const isLive = process.env.LIVE_E2E === "true"

async function answerAllQuestions(
  page: Page,
  strategy: "all-true" | "correct-first-N" | "incorrect-first-N",
  correctCount?: number,
) {
  const total = 50

  const correctAnswers = (await page.evaluate(() => {
    const ordered = (window as unknown as Record<string, unknown>).__mockTestCorrectAnswersOrdered
    return ordered ? (ordered as string[]) : null
  })) as string[] | null

  for (let i = 0; i < total; i++) {
    let answer: "true" | "false"

    if (strategy === "all-true") {
      answer = "true"
    } else if (strategy === "correct-first-N" && correctAnswers) {
      const correct = correctAnswers[i] as "true" | "false"
      if (i < (correctCount ?? 0)) {
        answer = correct
      } else {
        answer = correct === "true" ? "false" : "true"
      }
    } else if (strategy === "incorrect-first-N" && correctAnswers) {
      const correct = correctAnswers[i] as "true" | "false"
      if (i < (correctCount ?? 0)) {
        answer = correct === "true" ? "false" : "true"
      } else {
        answer = correct
      }
    } else {
      answer = "true"
    }

    await page.getByTestId(`answer-${answer}`).click()

    if (i < total - 1) {
      await page.getByTestId("nav-next").click()
    }
  }
}

async function startMockTest(page: Page) {
  await page.addInitScript(() => localStorage.clear())
  await page.goto("/mock-test")

  await expect(page.getByTestId("mock-test-start-card")).toBeVisible({ timeout: 10_000 })

  await page.getByTestId("start-mock-test-btn").click()

  await expect(page).toHaveURL(/\/mock-test\/\d+/, { timeout: 15_000 })
  await expect(page.getByTestId("question-card")).toBeVisible({ timeout: 10_000 })
}

async function submitTest(page: Page) {
  await page.getByTestId("submit-btn").click()
  await expect(page.getByTestId("submit-confirm-yes")).toBeVisible()
  await page.getByTestId("submit-confirm-yes").click()

  await expect(page).toHaveURL(/\/mock-test\/\d+\/result/, { timeout: 20_000 })
  await expect(page.getByTestId("result-banner")).toBeVisible({ timeout: 10_000 })
}

// ─── Start Screen Tests ─────────────────────────────────────────────────────

test.describe("Mock Test — Start Screen", () => {
  test("displays difficulty slider, locked format notice, and start button", async ({ page }) => {
    await page.addInitScript(() => localStorage.clear())
    await page.goto("/mock-test")

    await expect(page.getByTestId("page-title")).toBeVisible()
    await expect(page.getByTestId("difficulty-slider")).toBeVisible()
    await expect(page.getByTestId("difficulty-label")).toBeVisible()
    await expect(page.getByTestId("locked-format-notice")).toBeVisible()
    await expect(page.getByTestId("exam-format-badge")).toBeVisible()
    await expect(page.getByTestId("start-mock-test-btn")).toBeVisible()
  })

  test("difficulty slider has 5 stops and changes label", async ({ page }) => {
    await page.addInitScript(() => localStorage.clear())
    await page.goto("/mock-test")

    const slider = page.getByTestId("difficulty-slider")
    await expect(slider).toHaveAttribute("min", "0")
    await expect(slider).toHaveAttribute("max", "4")
    await expect(slider).toHaveAttribute("step", "1")

    // Default should be Standard (index 2)
    await expect(page.getByTestId("difficulty-label")).toContainText(/Standard|Padrão/)

    // Move to Expert (index 4)
    await slider.fill("4")
    await expect(page.getByTestId("difficulty-label")).toContainText(/Expert|Especialista/)

    // Move to Beginner (index 0)
    await slider.fill("0")
    await expect(page.getByTestId("difficulty-label")).toContainText(/Beginner|Iniciante/)
  })

  test("locked format notice shows 50 questions, 30 minutes, 90% threshold", async ({ page }) => {
    await page.addInitScript(() => localStorage.clear())
    await page.goto("/mock-test")

    const notice = page.getByTestId("locked-format-notice")
    await expect(notice).toContainText(/50/)
    await expect(notice).toContainText(/30/)
    await expect(notice).toContainText(/90%|45/)
  })
})

// ─── Runner Tests ───────────────────────────────────────────────────────────

test.describe("Mock Test — Runner", () => {
  test("start button navigates to runner with question card and timer", async ({ page }) => {
    await startMockTest(page)

    await expect(page.getByTestId("question-card")).toBeVisible()
    await expect(page.getByTestId("question-prompt")).not.toBeEmpty()
    await expect(page.getByTestId("answer-true")).toBeVisible()
    await expect(page.getByTestId("answer-false")).toBeVisible()
    await expect(page.getByTestId("timer-display")).toBeVisible()
    await expect(page.getByTestId("progress-bar")).toBeVisible()
    await expect(page.getByTestId("progress-text")).toContainText(/1.*50/)
  })

  test("answering a question highlights the choice and updates progress", async ({ page }) => {
    await startMockTest(page)

    await page.getByTestId("answer-true").click()
    await expect(page.getByTestId("answer-true")).toHaveAttribute("aria-pressed", "true")
    await expect(page.getByTestId("answer-false")).toHaveAttribute("aria-pressed", "false")

    await expect(page.getByTestId("answered-count")).toContainText(/1.*50/)
  })

  test("next and previous buttons navigate between questions", async ({ page }) => {
    await startMockTest(page)

    await expect(page.getByTestId("nav-prev")).toBeDisabled()
    await expect(page.getByTestId("nav-next")).toBeEnabled()

    await page.getByTestId("answer-true").click()
    await page.getByTestId("nav-next").click()

    await expect(page.getByTestId("progress-text")).toContainText(/2.*50/)
    await expect(page.getByTestId("nav-prev")).toBeEnabled()

    await page.getByTestId("nav-prev").click()
    await expect(page.getByTestId("progress-text")).toContainText(/1.*50/)
  })

  test("submit is disabled until all 50 questions are answered", async ({ page }) => {
    await startMockTest(page)

    await expect(page.getByTestId("submit-btn")).toBeDisabled()

    // Answer first question
    await page.getByTestId("answer-true").click()
    await expect(page.getByTestId("submit-btn")).toBeDisabled()
  })

  test("question dots show answered state", async ({ page }) => {
    await startMockTest(page)

    await page.getByTestId("answer-true").click()
    await expect(page.getByTestId("dot-0")).toHaveClass(/bg-primary/)
    await expect(page.getByTestId("dot-1")).toHaveClass(/bg-muted/)
  })

  test("answers are not shown during active test", async ({ page }) => {
    await startMockTest(page)

    const content = await page.content()
    expect(content).not.toMatch(/explanation|explicação/i)
    expect(content).not.toMatch(/Correct answer|Resposta correta/i)
  })
})

// ─── Result Screen Tests ────────────────────────────────────────────────────

test.describe("Mock Test — Result Screen", () => {
  test("happy path: start → answer all → submit → result with PASS/FAIL", async ({ page }) => {
    await startMockTest(page)

    await answerAllQuestions(page, "all-true")

    await expect(page.getByTestId("submit-btn")).toBeEnabled()
    await submitTest(page)

    await expect(page.getByTestId("pass-fail-label")).toBeVisible()
    await expect(page.getByTestId("score-display")).toBeVisible()
    await expect(page.getByTestId("score-percentage")).toBeVisible()
    await expect(page.getByTestId("review-list")).toBeVisible()
  })

  test("result shows per-question review with color chips", async ({ page }) => {
    await startMockTest(page)
    await answerAllQuestions(page, "all-true")
    await submitTest(page)

    const reviewItems = page.locator('[data-testid^="review-item-"]')
    await expect(reviewItems).toHaveCount(50)

    const firstChip = page.getByTestId("review-chip-0")
    await expect(firstChip).toBeVisible()
  })

  test("expandable explanation toggles on click", async ({ page }) => {
    await startMockTest(page)
    await answerAllQuestions(page, "all-true")
    await submitTest(page)

    const whyButton = page.getByTestId("review-why-0")
    await expect(whyButton).toBeVisible()
    await expect(page.getByTestId("review-explanation-0")).toHaveCount(0)

    await whyButton.click()
    await expect(page.getByTestId("review-explanation-0")).toBeVisible()

    await whyButton.click()
    await expect(page.getByTestId("review-explanation-0")).toHaveCount(0)
  })

  test("take another test button navigates to /mock-test", async ({ page }) => {
    await startMockTest(page)
    await answerAllQuestions(page, "all-true")
    await submitTest(page)

    await page.getByTestId("take-another-btn").click()
    await expect(page).toHaveURL(/\/mock-test$/)
  })

  test("generate study plan button navigates to /plan", async ({ page }) => {
    await startMockTest(page)
    await answerAllQuestions(page, "all-true")
    await submitTest(page)

    await page.getByTestId("generate-plan-btn").click()
    await expect(page).toHaveURL(/\/plan$/)
  })
})

// ─── Boundary Tests (44=FAIL, 45=PASS) — mock only ─────────────────────────

test.describe("Mock Test — Boundary (44=FAIL, 45=PASS)", () => {
  test("44 correct answers → FAIL", async ({ page, browserName }) => {
    test.skip(isLive, "Boundary test requires mock correct answers — skip in live mode")

    await startMockTest(page)

    await answerAllQuestions(page, "correct-first-N", 44)

    await submitTest(page)

    await expect(page.getByTestId("pass-fail-label")).toContainText(/FAIL|REPROVADO/)
    await expect(page.getByTestId("score-display")).toContainText(/44/)
  })

  test("45 correct answers → PASS", async ({ page }) => {
    test.skip(isLive, "Boundary test requires mock correct answers — skip in live mode")

    await startMockTest(page)

    await answerAllQuestions(page, "correct-first-N", 45)

    await submitTest(page)

    await expect(page.getByTestId("pass-fail-label")).toContainText(/PASS|APROVADO/)
    await expect(page.getByTestId("score-display")).toContainText(/45/)
  })
})
