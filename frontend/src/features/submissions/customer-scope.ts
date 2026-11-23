import type {ComputedRef,InjectionKey,Ref} from "vue"
export interface CustomerScope {enabled:ComputedRef<boolean>;name:ComputedRef<string>;tabs:ComputedRef<{id:string;name:string}[]>;active:Ref<string>}
export const customerScopeKey:InjectionKey<CustomerScope>=Symbol("report-customer-scope")
