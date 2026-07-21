import { useEffect, useRef, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

const API_URL = 'http://localhost:8000/chat'

function Bubble({ msg }) {
  if (msg.role === 'error') {
    return (
      <div className="msg-row msg-row-assistant">
        <div className="msg-bubble msg-error">{msg.text}</div>
      </div>
    )
  }

  if (msg.role === 'assistant') {
    return (
      <div className="msg-row msg-row-assistant">
        <div className="msg-bubble msg-assistant">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.text}</ReactMarkdown>
          {msg.tier && msg.model && (
            <span className="msg-tag">
              {msg.tier} · {msg.model}
            </span>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="msg-row msg-row-user">
      <div className="msg-bubble msg-user">{msg.text}</div>
    </div>
  )
}

export default function App() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [thinking, setThinking] = useState(false)
  const scrollRef = useRef(null)

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [messages, thinking])

  const sendMessage = async () => {
    const text = input.trim()
    if (!text || thinking) return

    setMessages((prev) => [...prev, { role: 'user', text }])
    setInput('')
    setThinking(true)

    try {
      const res = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text }),
      })

      if (!res.ok) {
        let detail = `Request failed (${res.status})`
        try {
          const body = await res.json()
          if (body?.detail) detail = body.detail
        } catch {
          // response wasn't JSON; keep the generic message
        }
        throw new Error(detail)
      }

      const data = await res.json()
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          text: data.reply,
          tier: data.tier,
          model: data.model,
        },
      ])
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'error',
          text: `Could not reach StudyPal: ${err.message || 'unknown error'}`,
        },
      ])
    } finally {
      setThinking(false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <h1>StudyPal</h1>
        <p className="tagline">Your friendly AI study buddy</p>
      </header>

      <main className="message-area">
        {messages.map((msg, i) => (
          <Bubble key={i} msg={msg} />
        ))}
        {thinking && (
          <div className="msg-row msg-row-assistant">
            <div className="msg-bubble msg-thinking">StudyPal is thinking…</div>
          </div>
        )}
        <div ref={scrollRef} />
      </main>

      <form
        className="input-bar"
        onSubmit={(e) => {
          e.preventDefault()
          sendMessage()
        }}
      >
        <input
          type="text"
          aria-label="Message StudyPal"
          placeholder="Ask StudyPal anything…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={thinking}
        />
        <button type="submit" disabled={thinking || !input.trim()}>
          Send
        </button>
      </form>
    </div>
  )
}
