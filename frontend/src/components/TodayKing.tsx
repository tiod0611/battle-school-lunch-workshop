import { useEffect, useState } from 'react'

import { ApiError, getTodayKing, type TodayKingResponse } from '../api/client'

function TodayKing() {
  const [data, setData] = useState<TodayKingResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [notReady, setNotReady] = useState(false)

  useEffect(() => {
    let active = true

    async function loadTodayKing() {
      try {
        setLoading(true)
        setError(null)
        setNotReady(false)
        const response = await getTodayKing()
        if (!active) return
        setData(response)
      } catch (caught) {
        if (!active) return
        if (caught instanceof ApiError && caught.status === 404) {
          setNotReady(true)
          return
        }

        setError(caught instanceof Error ? caught.message : '오늘의 왕을 불러오지 못했습니다.')
      } finally {
        if (active) {
          setLoading(false)
        }
      }
    }

    void loadTodayKing()

    return () => {
      active = false
    }
  }, [])

  return (
    <section className="today-king-box" aria-labelledby="today-king-title">
      <div className="king-badge">👑 오늘의 급식왕 👑</div>
      <h2 id="today-king-title">오늘의 왕</h2>
      {loading ? <p className="status-message">토너먼트 집계 중입니다...</p> : null}
      {!loading && notReady ? (
        <p className="status-message">오늘의 왕 준비 중! 배틀 심사위원이 아직 점심을 먹는 중입니다.</p>
      ) : null}
      {!loading && error ? <p className="error-message">{error}</p> : null}
      {!loading && !error && !notReady && data ? (
        <>
          <h3 className="king-school">{data.champion.schoolName}</h3>
          <p className="king-menu">{data.champion.menuItems.join(' · ')}</p>
          <p className="king-score">
            건강점수 <b>{data.champion.score.total}점</b> (전국 {data.totalParticipants}개교 중 1위)
          </p>
          <ul className="score-breakdown" aria-label="점수 세부 항목">
            <li>기본점수 {data.champion.score.base}</li>
            <li>제철 {data.champion.score.seasonalIngredient}</li>
            <li>탄단지 {data.champion.score.nutritionBalance}</li>
            <li>반찬 수 {data.champion.score.menuVariety}</li>
            <li>가공식품 {data.champion.score.processedFoodPenalty}</li>
          </ul>
          <p className="king-comment">
            "{data.champion.schoolName} 급식, 오늘은 알고리즘도 두 손 들었습니다."
          </p>
          <p className="bracket-note">▶ {data.date} 토너먼트 결과 반영 완료</p>
        </>
      ) : null}
    </section>
  )
}

export default TodayKing
