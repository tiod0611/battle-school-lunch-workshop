import { type FormEvent, useState } from 'react'

import { searchSchools, type SchoolSummary } from '../api/client'

interface SchoolSearchProps {
  selectedSchool: SchoolSummary | null
  onSelectSchool: (school: SchoolSummary) => void
}

function SchoolSearch({ selectedSchool, onSelectSchool }: SchoolSearchProps) {
  const [keyword, setKeyword] = useState('')
  const [results, setResults] = useState<SchoolSummary[]>([])
  const [page, setPage] = useState(1)
  const [totalCount, setTotalCount] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [searched, setSearched] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    const trimmed = keyword.trim()

    if (!trimmed) {
      setError('학교명을 1글자 이상 입력해 주세요.')
      setResults([])
      setSearched(false)
      return
    }

    try {
      setLoading(true)
      setError(null)
      const response = await searchSchools(trimmed, 1, 20)
      setResults(response.items)
      setPage(response.page)
      setTotalCount(response.totalCount)
      setSearched(true)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : '학교 검색에 실패했습니다.')
      setResults([])
      setSearched(true)
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="search-box">
      <h3>▶ 1단계: 우리 학교 찾기</h3>
      <form onSubmit={handleSubmit} className="school-search-form">
        <label htmlFor="school-keyword">학교명</label>
        <input
          id="school-keyword"
          type="text"
          value={keyword}
          placeholder="예: 서울고등학교"
          onChange={(event) => setKeyword(event.target.value)}
        />
        <button type="submit" disabled={loading}>
          {loading ? '검색중...' : '검 색'}
        </button>
      </form>

      {error ? <p className="error-message">{error}</p> : null}
      {searched && !loading && !error && results.length === 0 ? (
        <p className="status-message">검색 결과가 없습니다.</p>
      ) : null}

      {results.length > 0 ? (
        <div className="school-results">
          <p className="result-summary">
            검색 결과 {results.length}건 / 전체 {totalCount}건 (페이지 {page})
          </p>
          <ul className="school-list" aria-label="학교 검색 결과">
            {results.map((school) => {
              const isSelected = selectedSchool?.schoolCode === school.schoolCode

              return (
                <li key={`${school.schoolCode}-${school.officeCode}`}>
                  <button
                    type="button"
                    className={`school-item ${isSelected ? 'selected' : ''}`}
                    onClick={() => onSelectSchool(school)}
                  >
                    <strong>{school.schoolName}</strong>
                    <span>
                      {school.officeName} · {school.schoolKind}
                      {school.region ? ` · ${school.region}` : ''}
                    </span>
                  </button>
                </li>
              )
            })}
          </ul>
        </div>
      ) : null}
    </section>
  )
}

export default SchoolSearch
