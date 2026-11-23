export interface DictionaryItem {
  id: string
  dict_type: string
  dict_code: string
  dict_name: string
  dict_value: string
  description: string
  status: string
  sort_order: number
}

/** 客户配置行，复用 system_dictionary 存储（dict_type='customer'）。 */
export interface Customer {
  id: string
  dict_type: "customer"
  dict_code: string
  dict_name: string
  dict_value: string
  description: string
  status: "active" | "inactive"
  sort_order: number
}

/** 新增/编辑客户时提交的载荷；编辑时通常省略 dict_code。 */
export interface CustomerMutationPayload {
  dict_code: string
  dict_name: string
  sort_order?: number
  status?: "active" | "inactive"
  description?: string
}
