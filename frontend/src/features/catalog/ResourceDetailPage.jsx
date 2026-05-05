import { useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import api from '../../shared/api.js'
import './ResourceDetailPage.css'

function DetailRow({ label, value }) {
  return (
    <div className="resource-row">
      <span>{label}</span>
      <strong>{value || 'Not specified'}</strong>
    </div>
  )
}

function availabilityText(book) {
  const available = Number(book?.available_copies || 0)
  const total = Number(book?.total_copies || 0)
  if (available > 0) return `${available} of ${total || available} available`
  return total > 0 ? 'Currently unavailable' : 'No copies listed'
}

export function ResourceDetailPage({ type }) {
  const { bookId, ebookId } = useParams()
  const [data, setData] = useState(null)
  const [status, setStatus] = useState('loading')
  const [message, setMessage] = useState('')

  const resourceId = type === 'ebook' ? ebookId : bookId

  useEffect(() => {
    let cancelled = false

    async function loadResource() {
      setStatus('loading')
      setMessage('')
      try {
        const url = type === 'ebook'
          ? `/api/ebooks/${resourceId}/detail`
          : `/books/${resourceId}/detail`
        const response = await api.get(url)
        if (!cancelled) {
          setData(response.data)
          setStatus('ready')
        }
      } catch (error) {
        if (!cancelled) {
          setStatus('error')
          setMessage(error?.response?.data?.message || 'This library resource could not be found.')
        }
      }
    }

    loadResource()
    return () => {
      cancelled = true
    }
  }, [resourceId, type])

  const book = useMemo(() => data?.book || (type === 'book' ? data?.book : null), [data, type])
  const ebook = data?.ebook
  const title = type === 'ebook' ? ebook?.title : book?.title
  const linkedBook = type === 'ebook' ? data?.book : book
  const fileAvailable = type !== 'ebook' || ebook?.file_available !== false

  if (status === 'loading') {
    return (
      <main className="resource-page">
        <section className="resource-panel">
          <div className="resource-kicker">LIBRASYS Library</div>
          <h1>Loading resource</h1>
        </section>
      </main>
    )
  }

  if (status === 'error') {
    return (
      <main className="resource-page">
        <section className="resource-panel">
          <div className="resource-kicker">Resource Not Found</div>
          <h1>{message}</h1>
          <Link className="resource-button secondary" to="/">Back to library</Link>
        </section>
      </main>
    )
  }

  return (
    <main className="resource-page">
      <section className="resource-panel">
        <div className="resource-kicker">{type === 'ebook' ? 'E-book' : 'Library Book'}</div>
        <h1>{title}</h1>

        <div className="resource-meta">
          <DetailRow label="Author" value={linkedBook?.author || ebook?.author} />
          <DetailRow label="Category" value={linkedBook?.category || ebook?.category} />
          <DetailRow label="ISBN" value={linkedBook?.isbn || ebook?.isbn} />
          <DetailRow label="Availability" value={availabilityText(linkedBook)} />
        </div>

        {type === 'ebook' && ebook && (
          fileAvailable ? (
            <div className="resource-actions">
              <a className="resource-button" href={`${ebook.access_url}?disposition=inline`} target="_blank" rel="noreferrer">Open e-book</a>
              <a className="resource-button secondary" href={ebook.access_url}>Download</a>
            </div>
          ) : (
            <div className="resource-file-message">File not available</div>
          )
        )}
      </section>
    </main>
  )
}
