const DEFAULT_API_BASE_URL = "http://localhost:8000";

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.trim() || DEFAULT_API_BASE_URL;

export interface SchoolSummary {
  schoolCode: string;
  officeCode: string;
  officeName: string;
  schoolName: string;
  schoolKind: string;
  region?: string;
  foundationType?: string;
}

export interface SchoolSearchResponse {
  items: SchoolSummary[];
  page: number;
  limit: number;
  totalCount: number;
}

export interface MealItem {
  date: string;
  dayOfWeek: string;
  menuItems: string[];
  calorie?: string;
  nutritionInfo?: string;
}

export interface MealSearchResponse {
  schoolCode: string;
  officeCode: string;
  schoolName: string;
  meals: MealItem[];
  isEmpty: boolean;
}

export interface ScoreBreakdown {
  base: number;
  seasonalIngredient: number;
  nutritionBalance: number;
  menuVariety: number;
  processedFoodPenalty: number;
  total: number;
}

export interface TournamentSchool {
  schoolCode: string;
  schoolName: string;
  officeName: string;
  menuItems: string[];
  score: ScoreBreakdown;
}

export interface TournamentMatch {
  matchId: string;
  schoolA: TournamentSchool;
  schoolB: TournamentSchool | null;
  winnerSchoolCode: string;
  isBye: boolean;
}

export interface TournamentRound {
  roundNumber: number;
  roundName: string;
  matches: TournamentMatch[];
}

export interface TodayKingResponse {
  date: string;
  totalParticipants: number;
  champion: TournamentSchool;
  bracket: TournamentRound[];
}

export interface ValidationErrorResponse {
  detail: string;
}

export interface ErrorResponse {
  detail: string;
  code?: string;
}

export class ApiError extends Error {
  status: number;
  code?: string;

  constructor(status: number, message: string, code?: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }
}

function buildUrl(
  path: string,
  params?: Record<string, string | number | undefined>,
) {
  const url = new URL(path, API_BASE_URL);

  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== "") {
        url.searchParams.set(key, String(value));
      }
    });
  }

  return url.toString();
}

async function requestJson<T>(
  path: string,
  params?: Record<string, string | number | undefined>,
) {
  const response = await fetch(buildUrl(path, params));
  const contentType = response.headers.get("content-type") ?? "";
  const body = contentType.includes("application/json")
    ? await response.json()
    : null;

  if (!response.ok) {
    const detail =
      body && typeof body.detail === "string"
        ? body.detail
        : "요청 처리 중 오류가 발생했습니다.";
    const code = body && typeof body.code === "string" ? body.code : undefined;
    throw new ApiError(response.status, detail, code);
  }

  return body as T;
}

export function searchSchools(keyword: string, page = 1, limit = 20) {
  return requestJson<SchoolSearchResponse>("/api/schools/search", {
    keyword,
    page,
    limit,
  });
}

export function getMeals(
  schoolCode: string,
  officeCode: string,
  from: string,
  to: string,
) {
  return requestJson<MealSearchResponse>("/api/meals", {
    schoolCode,
    officeCode,
    from,
    to,
  });
}

export function getTodayKing() {
  return requestJson<TodayKingResponse>("/api/tournament/today");
}
