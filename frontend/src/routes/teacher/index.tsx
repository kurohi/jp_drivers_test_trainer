import { createRoute } from "@tanstack/react-router"
import { useTranslation } from "react-i18next"
import { useState, useRef, useEffect, useCallback } from "react"
import { Route as rootRoute } from "../__root"
import { api } from "@/lib/api"
import { useUIStore } from "@/store/ui"
import { useChatStore, type ChatMessage } from "@/store/chat"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"
import type { RagApiError } from "@/lib/api/fetch"

export const Route = createRoute({
  getParentRoute: () => rootRoute,
  path: "/teacher",
  component: TeacherPage,
})

function TeacherPage() {
  const { t } = useTranslation()
  const language = useUIStore((s) => s.language)
  const messages = useChatStore((s) => s.messages)
  const isLoading = useChatStore((s) => s.isLoading)
  const ollamaError = useChatStore((s) => s.ollamaError)
  const addMessage = useChatStore((s) => s.addMessage)
  const setLoading = useChatStore((s) => s.setLoading)
  const setOllamaError = useChatStore((s) => s.setOllamaError)

  const [input, setInput] = useState("")
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages, isLoading])

  const handleSend = useCallback(async () => {
    const question = input.trim()
    if (!question || isLoading) return

    setInput("")
    setLoading(true)
    setOllamaError(null)

    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: question,
    }
    addMessage(userMsg)

    try {
      const result = await api.rag.ask({
        question,
        language,
        k: 5,
      })

      const assistantMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: result.answer,
        sources: result.sources,
        isRefusal: result.sources.length === 0,
      }
      addMessage(assistantMsg)
    } catch (err) {
      const apiErr = err as RagApiError
      if (apiErr?.status === 503 && apiErr.detail?.host) {
        setOllamaError({ host: apiErr.detail.host })
      } else {
        const errorMsg: ChatMessage = {
          id: crypto.randomUUID(),
          role: "assistant",
          content: "An error occurred. Please try again.",
        }
        addMessage(errorMsg)
      }
    } finally {
      setLoading(false)
    }
  }, [input, isLoading, language, addMessage, setLoading, setOllamaError])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="container mx-auto py-8">
      <h1 data-testid="page-title" className="text-3xl font-bold">
        {t("pageTitle.teacher")}
      </h1>
      <p className="mt-2 text-muted-foreground">{t("teacher.subtitle")}</p>

      {ollamaError && (
        <div
          data-testid="ollama-down-banner"
          className="mt-4 rounded-lg border border-destructive/50 bg-destructive/10 p-4"
        >
          <div className="flex items-start gap-3">
            <div className="flex-1">
              <p className="font-semibold text-destructive">
                {t("teacher.ollamaDown")}
              </p>
              <p className="mt-1 text-sm text-muted-foreground">
                {t("teacher.ollamaDownDescription")}{" "}
                <code className="rounded bg-muted px-1.5 py-0.5 text-xs">
                  {ollamaError.host}
                </code>
              </p>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setOllamaError(null)}
            >
              {t("teacher.retry")}
            </Button>
          </div>
        </div>
      )}

      <Card
        data-testid="teacher-chat"
        className="mt-4 flex h-[600px] flex-col"
      >
        <ScrollArea className="flex-1" data-testid="teacher-messages">
          <div ref={scrollRef} className="space-y-4 p-4">
            {messages.length === 0 && !isLoading && (
              <div
                className="flex h-full items-center justify-center text-center"
                data-testid="teacher-empty-state"
              >
                <p className="text-muted-foreground">
                  {t("teacher.emptyState")}
                </p>
              </div>
            )}

            {messages.map((msg) => (
              <MessageBubble
                key={msg.id}
                message={msg}
                t={t}
              />
            ))}

            {isLoading && (
              <div
                className="flex items-center gap-2 text-sm text-muted-foreground"
                data-testid="teacher-loading"
              >
                <span className="animate-pulse">{t("teacher.thinking")}</span>
              </div>
            )}
          </div>
        </ScrollArea>

        <Separator />

        <div className="p-4">
          <div className="flex items-center gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={t("teacher.placeholder")}
              disabled={isLoading}
              data-testid="teacher-input"
              className="flex-1 rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
            />
            <Button
              onClick={handleSend}
              disabled={!input.trim() || isLoading}
              data-testid="teacher-send"
              size="default"
            >
              {t("teacher.send")}
            </Button>
          </div>
        </div>
      </Card>
    </div>
  )
}

interface MessageBubbleProps {
  message: ChatMessage
  t: (key: string, opts?: Record<string, unknown>) => string
}

function MessageBubble({ message, t }: MessageBubbleProps) {
  const isUser = message.role === "user"
  const [showSources, setShowSources] = useState(false)

  return (
    <div
      className={`flex ${isUser ? "justify-end" : "justify-start"}`}
      data-testid={`teacher-message-${message.role}`}
    >
      <div
        className={`max-w-[80%] rounded-lg p-3 ${
          isUser
            ? "bg-primary text-primary-foreground"
            : "bg-muted text-foreground"
        }`}
      >
        <p className="mb-1 text-xs font-semibold opacity-70">
          {isUser ? t("teacher.you") : t("teacher.teacher")}
        </p>

        {message.isRefusal && (
          <div
            data-testid="teacher-refusal"
            className="mb-2 rounded-md border border-amber-500/50 bg-amber-500/10 p-2"
          >
            <p className="text-xs font-semibold text-amber-600 dark:text-amber-400">
              {t("teacher.outOfScope")}
            </p>
          </div>
        )}

        <p className="text-sm leading-relaxed whitespace-pre-wrap">
          {message.content}
        </p>

        {!isUser && message.sources && message.sources.length > 0 && (
          <div className="mt-3" data-testid="teacher-sources">
            <button
              onClick={() => setShowSources(!showSources)}
              className="text-xs font-semibold text-primary underline-offset-4 hover:underline"
            >
              {t("teacher.sources")} ({message.sources.length})
            </button>
            {showSources && (
              <div className="mt-2 space-y-2">
                {message.sources.map((src, idx) => (
                  <div
                    key={idx}
                    className="rounded-md border bg-background/50 p-2"
                  >
                    <a
                      href={src.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs font-medium text-primary hover:underline"
                    >
                      {src.title}
                    </a>
                    <p className="mt-1 text-xs text-muted-foreground line-clamp-2">
                      {src.snippet}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
