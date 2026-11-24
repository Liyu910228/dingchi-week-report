import type { SubmissionPart, SubmissionDetail } from "@/features/submissions/types";
export interface MonthRow {
    employee_id: string;
    employee_name: string;
    month_key: string;
    role_name: string;
    week_count: number;
    completed_count: number;
    updated_at: string;
}
export interface MonthPage {
    items: MonthRow[];
    total: number;
    total_pages: number;
}
export type MonthWeek = Pick<SubmissionDetail, "plan" | "parts"> & {
    sources: {
        id: string;
        role_name: string;
    }[];
};
export interface MonthDetail {
    month_key: string;
    employee_id: string;
    monthly_parts: SubmissionPart[];
    weeks: MonthWeek[];
}
