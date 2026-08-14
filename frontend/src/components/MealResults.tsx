import { useState } from 'react'

import { getMeals, type MealSearchResponse, type SchoolSummary } from '../api/client'
import type { DateRangeValue } from './DateRangePicker'

interface MealResultsProps {
  selectedSchool: SchoolSummary | null
  dateRange: DateRangeValue
  onValidationError: (message: string | null) => void
}

function toDateValue(raw: string) {
  return new Date(`${raw}T00:00:00`)
}

function validateDateRange({ from, to }: DateRangeValue) {
  if (!from || !to) {
    return '시작일과 종료일을 모두 선택해 주세요.'
  }

  const fromDate = toDateValue(from)
  const toDate = toDateValue(to)

  if (toDate < fromDate) {
    return '종료일은 시작일보다 빠를 수 없습니다.'
  }

  const diffDays = Math.floor((toDate.getTime() - fromDate.getTime()) / 86400000) + 1
  if (diffDays > 31) {
    return '날짜 범위는 최대 31일까지 조회할 수 있습니다.'
  }

  return null
}

function MealResults({
  selectedSchool,
  dateRange,
  onValidationError,
}: MealResultsProps) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<MealSearchResponse | null>(null)

  async function handleLookup() {
    if (!selectedSchool) {
      onValidationError('먼저 학교를 선택해 주세요.')
      setResult(null)
      return
    }

    const nextError = validateDateRange(dateRange)
    onValidationError(nextError)

    if (nextError) {
      setResult(null)
      return
    }

    try {
      setLoading(true)
      setError(null)
      const response = await getMeals(
        selectedSchool.schoolCode,
        selectedSchool.officeCode,
        dateRange.from,
        dateRange.to,
      )
      setResult(response)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : '급식 정보를 불러오지 못했습니다.')
      setResult(null)
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="result-box">
      <h3>▶ 3단계: 급식 조회 결과</h3>
      <div className="lookup-actions">
        <button type="button" onClick={handleLookup} disabled={loading}>
          {loading ? '조회중...' : '급식 조회'}
        </button>
        {selectedSchool ? (
          <p className="selected-school">
            선택 학교: <strong>{selectedSchool.schoolName}</strong> ({selectedSchool.officeName})
          </p>
        ) : (
          <p className="selected-school">선택된 학교가 없습니다.</p>
        )}
      </div>

      {error ? <p className="error-message">{error}</p> : null}
      {loading ? <p className="status-message">급식표를 교무실에서 받아오는 중입니다...</p> : null}

      {!loading && result?.isEmpty ? (
        <p className="status-message">해당 기간에는 등록된 중식 급식 정보가 없습니다.</p>
      ) : null}

      {!loading && result && !result.isEmpty ? (
        <table className="retro-table" aria-label="급식 조회 결과">
          <thead>
            <tr>
              <th>날짜</th>
              <th>요일</th>
              <th>중식 메뉴</th>
              <th>칼로리</th>
            </tr>
          </thead>
          <tbody>
            {result.meals.map((meal) => (
              <tr key={meal.date}>
                <td>{meal.date}</td>
                <td>{meal.dayOfWeek}</td>
                <td>{meal.menuItems.join(', ')}</td>
                <td>{meal.calorie ?? '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : null}
    </section>
  )
}

export { validateDateRange }
export default MealResults
