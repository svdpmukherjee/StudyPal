import { useEffect, useRef, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

const API_URL = 'http://localhost:8000/chat'
const PROFILE_URL = 'http://localhost:8000/profile'
const SUMMARIZE_URL = 'http://localhost:8000/summarize'
const EVALUATE_URL = 'http://localhost:8000/evaluate'

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
              {msg.skill && <span className="msg-skill">via {msg.skill}</span>}
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

  const [facts, setFacts] = useState([])
  const [profileError, setProfileError] = useState('')
  const [factInput, setFactInput] = useState('')
  const [savingFact, setSavingFact] = useState(false)
  const [summarizing, setSummarizing] = useState(false)
  const [added, setAdded] = useState([])
  const [hasSummarized, setHasSummarized] = useState(false)

  const [evaluating, setEvaluating] = useState(false)
  const [verdict, setVerdict] = useState(null)
  const [hasEvaluated, setHasEvaluated] = useState(false)
  const [evalError, setEvalError] = useState('')

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [messages, thinking])

  useEffect(() => {
    const loadProfile = async () => {
      try {
        const res = await fetch(PROFILE_URL)
        if (!res.ok) {
          throw new Error(`Request failed (${res.status})`)
        }
        const data = await res.json()
        setFacts(data.facts || [])
        setProfileError('')
      } catch (err) {
        setProfileError(
          `Could not load StudyPal's memory: ${err.message || 'unknown error'}`
        )
      }
    }
    loadProfile()
  }, [])

  const addFact = async (e) => {
    e.preventDefault()
    const fact = factInput.trim()
    if (!fact || savingFact) return

    setSavingFact(true)
    try {
      const res = await fetch(PROFILE_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ fact }),
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
      setFacts(data.facts || [])
      setFactInput('')
      setProfileError('')
    } catch (err) {
      setProfileError(
        `Could not save that fact: ${err.message || 'unknown error'}`
      )
    } finally {
      setSavingFact(false)
    }
  }

  const summarizeSession = async () => {
    if (summarizing) return

    setSummarizing(true)
    try {
      const res = await fetch(SUMMARIZE_URL, { method: 'POST' })

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
      setFacts(data.facts || [])
      setAdded(data.added || [])
      setHasSummarized(true)
      setProfileError('')
    } catch (err) {
      setProfileError(
        `Could not summarize the session: ${err.message || 'unknown error'}`
      )
    } finally {
      setSummarizing(false)
    }
  }

  const evaluateLastAnswer = async () => {
    if (evaluating) return

    setEvaluating(true)
    try {
      const res = await fetch(EVALUATE_URL, { method: 'POST' })

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
      setVerdict(data.evaluated ? data.verdict : null)
      setHasEvaluated(true)
      setEvalError('')
    } catch (err) {
      setEvalError(
        `Could not evaluate the last answer: ${err.message || 'unknown error'}`
      )
    } finally {
      setEvaluating(false)
    }
  }

  const sendMessage = async (skill = null) => {
    const text = input.trim()
    if (!text || thinking) return

    setMessages((prev) => [...prev, { role: 'user', text }])
    setInput('')
    setThinking(true)

    try {
      const body = skill ? { message: text, skill } : { message: text }
      const res = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
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
          skill: data.skill,
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

      {(facts.length > 0 || profileError) && (
        <section className="memory-panel" aria-label="StudyPal remembers">
          {facts.length > 0 && (
            <>
              <span className="memory-label">StudyPal remembers</span>
              <div className="memory-chips">
                {facts.map((fact, i) => (
                  <span className="memory-chip" key={i}>
                    {fact}
                  </span>
                ))}
              </div>
            </>
          )}
          {profileError && <div className="memory-error">{profileError}</div>}
        </section>
      )}

      <div className="summarize-row">
        <button
          type="button"
          className="summarize-btn"
          onClick={summarizeSession}
          disabled={summarizing}
        >
          {summarizing ? 'Summarizing…' : 'Summarize session'}
        </button>
        {hasSummarized && (
          <span className="summarize-added">
            {added.length > 0
              ? `Added ${added.length}: ${added.join(', ')}`
              : 'Nothing new to remember'}
          </span>
        )}
        <button
          type="button"
          className="eval-btn"
          onClick={evaluateLastAnswer}
          disabled={evaluating}
        >
          {evaluating ? 'Evaluating…' : 'Evaluate last answer'}
        </button>
      </div>

      {(hasEvaluated || evalError) && (
        <section className="eval-panel" aria-label="Evaluation of last answer">
          {evalError && <div className="memory-error">{evalError}</div>}
          {!evalError && hasEvaluated && verdict && (
            <>
              <span className="eval-score">Score: {verdict.score}/5</span>
              <span className="eval-subscores">
                Accuracy {verdict.accuracy}/5 · Clarity {verdict.clarity}/5
              </span>
              <p className="eval-rationale">{verdict.rationale}</p>
            </>
          )}
          {!evalError && hasEvaluated && !verdict && (
            <p className="eval-rationale">Nothing to evaluate yet</p>
          )}
        </section>
      )}

      <form className="add-fact-bar" onSubmit={addFact}>
        <label className="add-fact-label" htmlFor="add-fact-input">
          Remember something about you
        </label>
        <div className="add-fact-row">
          <input
            id="add-fact-input"
            type="text"
            placeholder="e.g. weak on recursion"
            value={factInput}
            onChange={(e) => setFactInput(e.target.value)}
            disabled={savingFact}
          />
          <button type="submit" disabled={savingFact || !factInput.trim()}>
            Remember
          </button>
        </div>
      </form>

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

      <div className="skill-bar" aria-label="Tutoring moves">
        <button
          type="button"
          className="skill-btn"
          onClick={() => sendMessage('explain-simply')}
          disabled={thinking || !input.trim()}
        >
          Explain simply
        </button>
        <button
          type="button"
          className="skill-btn"
          onClick={() => sendMessage('quiz-me')}
          disabled={thinking || !input.trim()}
        >
          Quiz me
        </button>
      </div>
    </div>
  )
}
