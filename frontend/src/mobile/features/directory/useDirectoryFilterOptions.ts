import { reactive, ref } from "vue"
import { listGroups, listUserOptions } from "./api"
import type { DirectoryGroup, DirectoryUserOption } from "./types"

/** 列表筛选所需的公共分组及人员选项；独立失败可分别展示。 */
export function useDirectoryFilterOptions() {
  const groups=reactive<DirectoryGroup[]>([]),users=reactive<DirectoryUserOption[]>([]),error=ref("")
  async function load() {
    error.value=""
    const results=await Promise.allSettled([listGroups(),listUserOptions()])
    const [groupResult,userResult]=results
    if(groupResult.status==='fulfilled')groups.splice(0,groups.length,...groupResult.value.items)
    if(userResult.status==='fulfilled')users.splice(0,users.length,...userResult.value.items)
    error.value=results.flatMap(result=>result.status==='rejected'?[result.reason instanceof Error?result.reason.message:'筛选选项加载失败。']:[]).join('；')
  }
  return {groups,users,error,load}
}
