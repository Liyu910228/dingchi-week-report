export interface LeaderDepartment {
  name: string
  rate: number
  taskCount: number
}

export interface LeaderResult {
  id: string
  name: string
  owner: string
  category: string
  file: string
}

export interface LeaderPlan {
  id: string
  name: string
  note: string
  date: string
  owner: string
}

export interface LeaderRelation {
  id: string
  name: string
  count: number
}
