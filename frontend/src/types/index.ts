// TypeScript types matching the backend Pydantic models exactly

export interface StepTokens {
  input: number;
  output: number;
}

export interface Step {
  index: number;
  name: string;
  tool: string;
  status: string;
  started_at: string;
  duration_ms: number | null;
  input: string;
  output: string | null;
  tokens: StepTokens;
}

export interface RunError {
  type: string;
  message: string;
  step_index: number;
}

export interface RunSummary {
  id: string;
  agent: string;
  model: string;
  status: string;
  started_at: string;
  ended_at: string | null;
  duration_ms: number | null;
  input_tokens: number;
  output_tokens: number;
  cost_usd: number | null;
  prompt: string;
  error: RunError | null;
  tenant_id: string;
}

export interface RunDetail extends RunSummary {
  steps: Step[];
}

export interface RunsResponse {
  total: number;
  page: number;
  page_size: number;
  items: RunSummary[];
}

export interface OverallStats {
  total_runs: number;
  success_rate: number;
  median_duration_ms: number | null;
  p95_duration_ms: number | null;
}

export interface AgentStats {
  agent: string;
  total_runs: number;
  success_rate: number;
  total_cost_usd: number | null;
  cost_usd_is_partial: boolean;
}

export interface DailyCount {
  date: string;
  count: number;
}

export interface StatsResponse {
  overall: OverallStats;
  per_agent: AgentStats[];
  daily_counts: DailyCount[];
}

// Query params for /api/runs
export interface RunsParams {
  page?: number;
  page_size?: number;
  status?: string[];
  agent?: string[];
  tool?: string[];
  started_after?: string;
  started_before?: string;
  q?: string;
  sort_by?: string;
  sort_dir?: string;
}
