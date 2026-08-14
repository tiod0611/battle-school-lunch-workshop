function Header() {
  return (
    <>
      <div className="util-bar">
        즐겨찾기 추가 | 글자크기 <a href="#app">가</a> <a href="#app">가</a>{" "}
        <a href="#app">가</a> | 현재 접속자: 1,024명
      </div>
      <header className="main-header">
        <h1>🍚 급 식 배 틀 🍚</h1>
        <p className="subtitle">전국 학교 급식 정보 조회 시스템</p>
      </header>
      <div className="notice-marquee" role="status" aria-label="공지사항">
        <div className="notice-track">
          🔔 공지: 매일 정오, 전국 고등학교 128개교가 급식으로 목숨을 건 배틀을
          벌칩니다! 오늘의 왕은 누구?! 🔔
        </div>
      </div>
    </>
  );
}

export default Header;
