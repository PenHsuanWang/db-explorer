import { useEffect, useState, useCallback } from 'react'
import styles from './Toast.module.css'

export type ToastVariant = 'success' | 'error' | 'info'

export interface ToastMessage {
  id: number
  text: string
  variant: ToastVariant
}

const ICONS: Record<ToastVariant, string> = {
  success: '✓',
  error: '✕',
  info: 'ℹ',
}

interface ToastItemProps {
  message: ToastMessage
  onDismiss: (id: number) => void
  duration?: number
}

function ToastItem({ message, onDismiss, duration = 4000 }: ToastItemProps) {
  useEffect(() => {
    const timer = setTimeout(() => onDismiss(message.id), duration)
    return () => clearTimeout(timer)
  }, [message.id, onDismiss, duration])

  return (
    <div className={`${styles.toast} ${styles[message.variant]}`}>
      <span className={styles.icon}>{ICONS[message.variant]}</span>
      <span className={styles.content}>{message.text}</span>
      <button className={styles.close} onClick={() => onDismiss(message.id)} aria-label="Dismiss">
        ✕
      </button>
    </div>
  )
}

let addToastGlobal: ((text: string, variant?: ToastVariant) => void) | null = null

export function toast(text: string, variant: ToastVariant = 'info') {
  addToastGlobal?.(text, variant)
}

let nextId = 0

export function ToastContainer() {
  const [messages, setMessages] = useState<ToastMessage[]>([])

  const addToast = useCallback((text: string, variant: ToastVariant = 'info') => {
    const id = Date.now() + ++nextId
    setMessages((prev) => [...prev, { id, text, variant }])
  }, [])

  const dismiss = useCallback((id: number) => {
    setMessages((prev) => prev.filter((m) => m.id !== id))
  }, [])

  useEffect(() => {
    addToastGlobal = addToast
    return () => {
      addToastGlobal = null
    }
  }, [addToast])

  if (messages.length === 0) return null

  const latest = messages[messages.length - 1]
  return <ToastItem message={latest} onDismiss={dismiss} />
}
