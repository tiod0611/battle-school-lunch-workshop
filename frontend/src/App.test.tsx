import { http, HttpResponse } from 'msw'
import { setupServer } from 'msw/node'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import App from './App'

const apiBaseUrl = 'http://localhost:8000'

const schoolResponse = {
  items: [
    {
      schoolCode: '7010569',
      officeCode: 'B10',
      officeName: '서울특별시교육청',
      schoolName: '서울OO고등학교',
      schoolKind: '고등학교',
      region: '서울',
      foundationType: '공립',
    },
  ],
  page: 1,
  limit: 20,
  totalCount: 1,
}

const todayKingResponse = {
  date: '2026-08-14',
  totalParticipants: 128,
  champion: {
    schoolCode: '7010569',
    schoolName: '서울OO고등학교',
    officeName: '서울특별시교육청',
    menuItems: ['현미밥', '된장찌개', '제육볶음', '봄동나물무침', '배추김치'],
    score: {
      base: 20,
      seasonalIngredient: 22,
      nutritionBalance: 24,
      menuVariety: 21,
      processedFoodPenalty: -2,
      total: 85,
    },
  },
  bracket: [],
}

const mealResponse = {
  schoolCode: '7010569',
  officeCode: 'B10',
  schoolName: '서울OO고등학교',
  isEmpty: false,
  meals: [
    {
      date: '2026-08-14',
      dayOfWeek: '금',
      menuItems: ['흑미밥', '미역국', '돈까스'],
      calorie: '820 Kcal',
      nutritionInfo: '탄수화물 90g',
    },
  ],
}

const server = setupServer(
  http.get(`${apiBaseUrl}/api/tournament/today`, () => HttpResponse.json(todayKingResponse)),
  http.get(`${apiBaseUrl}/api/schools/search`, () => HttpResponse.json(schoolResponse)),
  http.get(`${apiBaseUrl}/api/meals`, () => HttpResponse.json(mealResponse)),
)

beforeAll(() => server.listen())
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

describe('급식배틀 프론트엔드', () => {
  it('학교 검색 후 결과를 선택할 수 있다', async () => {
    const user = userEvent.setup()
    render(<App />)

    await screen.findByText('서울OO고등학교')

    await user.type(screen.getByLabelText('학교명'), '서울고')
    await user.click(screen.getByRole('button', { name: '검 색' }))

    const schoolButton = await screen.findByRole('button', { name: /서울OO고등학교/ })
    await user.click(schoolButton)

    expect(screen.getByText(/선택 학교:/)).toBeInTheDocument()
  })

  it('잘못된 날짜 범위면 오류를 보여주고 API 호출을 막는다', async () => {
    const mealsSpy = vi.fn(() => HttpResponse.json(mealResponse))
    server.use(http.get(`${apiBaseUrl}/api/meals`, () => mealsSpy()))

    const user = userEvent.setup()
    render(<App />)

    await user.type(screen.getByLabelText('학교명'), '서울고')
    await user.click(screen.getByRole('button', { name: '검 색' }))
    await user.click(await screen.findByRole('button', { name: /서울OO고등학교/ }))

    await user.clear(screen.getByLabelText('시작일'))
    await user.type(screen.getByLabelText('시작일'), '2026-08-31')
    await user.clear(screen.getByLabelText('종료일'))
    await user.type(screen.getByLabelText('종료일'), '2026-08-01')
    await user.click(screen.getByRole('button', { name: '급식 조회' }))

    expect(await screen.findByText('종료일은 시작일보다 빠를 수 없습니다.')).toBeInTheDocument()
    expect(mealsSpy).not.toHaveBeenCalled()
  })

  it('급식 결과 정상/빈결과/API 오류를 각각 표시한다', async () => {
    const user = userEvent.setup()
    render(<App />)

    await user.type(screen.getByLabelText('학교명'), '서울고')
    await user.click(screen.getByRole('button', { name: '검 색' }))
    await user.click(await screen.findByRole('button', { name: /서울OO고등학교/ }))

    await user.clear(screen.getByLabelText('시작일'))
    await user.type(screen.getByLabelText('시작일'), '2026-08-01')
    await user.clear(screen.getByLabelText('종료일'))
    await user.type(screen.getByLabelText('종료일'), '2026-08-14')
    await user.click(screen.getByRole('button', { name: '급식 조회' }))

    expect(await screen.findByRole('table', { name: '급식 조회 결과' })).toBeInTheDocument()
    expect(screen.getByText('흑미밥, 미역국, 돈까스')).toBeInTheDocument()

    server.use(
      http.get(`${apiBaseUrl}/api/meals`, () =>
        HttpResponse.json({ ...mealResponse, meals: [], isEmpty: true }),
      ),
    )
    await user.click(screen.getByRole('button', { name: '급식 조회' }))
    expect(await screen.findByText('해당 기간에는 등록된 중식 급식 정보가 없습니다.')).toBeInTheDocument()

    server.use(
      http.get(
        `${apiBaseUrl}/api/meals`,
        () => HttpResponse.json({ detail: '일시적인 급식 조회 오류입니다.' }, { status: 502 }),
      ),
    )
    await user.click(screen.getByRole('button', { name: '급식 조회' }))
    expect(await screen.findByText('일시적인 급식 조회 오류입니다.')).toBeInTheDocument()
  })

  it('오늘의 왕 정상 표시와 404 준비중 상태를 처리한다', async () => {
    const { unmount } = render(<App />)
    expect(await screen.findByText('서울OO고등학교')).toBeInTheDocument()
    expect(screen.getByText(/건강점수/)).toBeInTheDocument()
    unmount()

    server.use(
      http.get(
        `${apiBaseUrl}/api/tournament/today`,
        () => HttpResponse.json({ detail: '오늘의 왕 준비 중', code: 'TOURNAMENT_NOT_READY' }, { status: 404 }),
      ),
    )

    render(<App />)
    expect(
      await screen.findByText('오늘의 왕 준비 중! 배틀 심사위원이 아직 점심을 먹는 중입니다.'),
    ).toBeInTheDocument()
  })
})
