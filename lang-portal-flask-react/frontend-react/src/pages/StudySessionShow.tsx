import React, { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import WordsTable from '@/components/WordsTable'
import Pagination from '@/components/Pagination'
import type { Word, WordSortKey } from '@/services/api'

interface StudySession {
  id: number
  group_id: number
  group_name: string
  activity_id: number
  activity_name: string
  start_time: string
  end_time: string
  review_items_count: number
  total_correct: number
  total_wrong: number
  accuracy: number
  grade: string
  feedback: string
}

interface SessionResponse {
  session: StudySession
  words: Word[]
  total: number
  page: number
  per_page: number
  total_pages: number
}

export default function StudySessionShow() {
  const { id } = useParams<{ id: string }>()
  const [session, setSession] = useState<StudySession | null>(null)
  const [words, setWords] = useState<Word[]>([])
  const [currentPage, setCurrentPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [sortKey, setSortKey] = useState<WordSortKey>('kanji')
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Nouvelle variable d'état pour les révisions
  const [reviewAnswers, setReviewAnswers] = useState<{ word_id: number, correct: boolean }[]>([])

  useEffect(() => {
    const fetchData = async () => {
      if (!id) return

      setLoading(true)
      setError(null)
      try {
        const response = await fetch(
          `http://localhost:5000/api/study-sessions/${id}?page=${currentPage}&per_page=10`
        )
        if (!response.ok) {
          throw new Error('Failed to fetch session data')
        }
        const data: SessionResponse = await response.json()
        setSession(data.session)
        setWords(data.words)
        setTotalPages(data.total_pages)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred')
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [id, currentPage])

  const handleSort = (key: WordSortKey) => {
    if (key === sortKey) {
      setSortDirection(prev => prev === 'asc' ? 'desc' : 'asc')
    } else {
      setSortKey(key)
      setSortDirection('asc')
    }
  }

  // Fonction pour soumettre les révisions
  const submitReviews = async () => {
    if (reviewAnswers.length === 0) {
      return
    }

    try {
      const response = await fetch(`http://127.0.0.1:5000/study_sessions/${id}/review`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          answers: reviewAnswers,
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to submit reviews')
      }

      const data = await response.json()
      console.log("Review submitted:", data)
      // Vous pouvez mettre à jour l'état ou rediriger l'utilisateur si nécessaire
      alert("Révisions soumises avec succès !")
    } catch (err) {
      console.error("Error submitting review:", err)
    }
  }

  // Fonction pour gérer le changement de réponse d'un mot
  const handleReviewChange = (word_id: number, correct: boolean) => {
    setReviewAnswers((prev) => {
      const newAnswers = prev.filter((answer) => answer.word_id !== word_id)
      newAnswers.push({ word_id, correct })
      return newAnswers
    })
  }

  if (loading) {
    return <div className="text-center py-4">Loading...</div>
  }

  if (error || !session) {
    return <div className="text-red-500 text-center py-4">{error || 'Session not found'}</div>
  }

  return (
    <div className="space-y-8">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-800 dark:text-white">Study Session Details</h1>
        <Link
          to="/sessions"
          className="px-4 py-2 text-sm font-medium text-gray-600 bg-gray-100 rounded-md hover:bg-gray-200 dark:text-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600"
        >
          Back to Sessions
        </Link>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <h2 className="text-sm font-medium text-gray-500 dark:text-gray-400">Activity</h2>
            <Link to={`/study-activities/${session.activity_id}`} className="text-blue-600 dark:text-blue-400 hover:underline">
              {session.activity_name}
            </Link>
          </div>
          <div>
            <h2 className="text-sm font-medium text-gray-500 dark:text-gray-400">Group</h2>
            <Link to={`/groups/${session.group_id}`} className="text-blue-600 dark:text-blue-400 hover:underline">
              {session.group_name}
            </Link>
          </div>
          <div>
            <h2 className="text-sm font-medium text-gray-500 dark:text-gray-400">Start Time</h2>
            <p className="text-gray-900 dark:text-gray-100">{session.start_time}</p>
          </div>
          <div>
            <h2 className="text-sm font-medium text-gray-500 dark:text-gray-400">Review Items</h2>
            <p className="text-gray-900 dark:text-gray-100">{session.review_items_count}</p>
          </div>
        </div>
      </div>

      <div className="space-y-4">
        <h2 className="text-xl font-semibold text-gray-800 dark:text-white">Words Reviewed</h2>
        <WordsTable
          words={words}
          sortKey={sortKey}
          sortDirection={sortDirection}
          onSort={handleSort}
          onReviewChange={handleReviewChange}  // Pass the function to handle review changes
        />
        {totalPages > 1 && (
          <div className="mt-4">
            <Pagination
              currentPage={currentPage}
              totalPages={totalPages}
              onPageChange={setCurrentPage}
            />
          </div>
        )}
      </div>

      {/* Ajouter un bouton pour soumettre les révisions */}
      <div className="flex justify-end mt-4">
        <button
          onClick={submitReviews}
          className="px-6 py-2 text-white bg-blue-600 rounded-md hover:bg-blue-700"
        >
          Submit Reviews
        </button>
      </div>
    </div>
  )
}