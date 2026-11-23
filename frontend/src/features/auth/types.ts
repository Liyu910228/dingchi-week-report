export interface Role {
  customer_ids?: string[]
  id: string
  role_code: string
  role_name: string
  scope: "self" | "team" | "all" | string
  description: string
  report_template_code: string
  role_group_code?: string
  status: string
}

export interface UserAccount {
  role_customer_ids?: Record<string, string[]>
  id: string
  username: string
  employee_no: string
  display_name: string
  email: string
  manager_id: string | null
  group_id: string | null
  group_name?: string
  avatar_color: string
  status: string
  role_codes?: string[]
  role_names?: string[]
}

export interface Session {
  access_token: string
  token_type: "Bearer"
  expires_in: number
  user: UserAccount
  roles: Role[]
  active_role: Role
}
