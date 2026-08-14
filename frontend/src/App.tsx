import { useMemo, useState } from "react";

import type { SchoolSummary } from "./api/client";
import DateRangePicker, {
  type DateRangeValue,
} from "./components/DateRangePicker";
import Footer from "./components/Footer";
import Header from "./components/Header";
import MealResults from "./components/MealResults";
import SchoolSearch from "./components/SchoolSearch";
import TodayKing from "./components/TodayKing";

function formatDate(date: Date) {
  return date.toISOString().slice(0, 10);
}

function App() {
  const today = useMemo(() => new Date(), []);
  const initialDateRange = useMemo<DateRangeValue>(() => {
    const startDate = new Date(today);
    startDate.setDate(today.getDate() - 6);

    return {
      from: formatDate(startDate),
      to: formatDate(today),
    };
  }, [today]);

  const [selectedSchool, setSelectedSchool] = useState<SchoolSummary | null>(
    null,
  );
  const [dateRange, setDateRange] = useState<DateRangeValue>(initialDateRange);
  const [validationError, setValidationError] = useState<string | null>(null);

  return (
    <div className="app-shell" id="app">
      <Header />
      <main className="content-area">
        <TodayKing />
        <SchoolSearch
          selectedSchool={selectedSchool}
          onSelectSchool={setSelectedSchool}
        />
        <DateRangePicker
          value={dateRange}
          error={validationError}
          onChange={(value) => {
            setDateRange(value);
            setValidationError(null);
          }}
        />
        <MealResults
          selectedSchool={selectedSchool}
          dateRange={dateRange}
          onValidationError={setValidationError}
        />
      </main>
      <Footer />
    </div>
  );
}

export default App;
