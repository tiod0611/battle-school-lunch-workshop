export interface DateRangeValue {
  from: string
  to: string
}

interface DateRangePickerProps {
  value: DateRangeValue
  error: string | null
  onChange: (value: DateRangeValue) => void
}

function DateRangePicker({ value, error, onChange }: DateRangePickerProps) {
  return (
    <section className="search-box">
      <h3>▶ 2단계: 조회 기간 선택</h3>
      <div className="date-range-row">
        <label htmlFor="from-date">시작일</label>
        <input
          id="from-date"
          type="date"
          value={value.from}
          onChange={(event) => onChange({ ...value, from: event.target.value })}
        />
        <span className="date-separator">~</span>
        <label htmlFor="to-date">종료일</label>
        <input
          id="to-date"
          type="date"
          value={value.to}
          onChange={(event) => onChange({ ...value, to: event.target.value })}
        />
      </div>
      <p className="helper-text">최대 31일까지만 조회할 수 있습니다.</p>
      {error ? <p className="error-message">{error}</p> : null}
    </section>
  )
}

export default DateRangePicker
