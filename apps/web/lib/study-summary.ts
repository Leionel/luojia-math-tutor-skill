import type {LearningRecommendation} from "./learning-api";
export type StudySummary={version:"study-summary-v1";local_date:string;read_at:string;plan_exists:boolean;stale:boolean;help_locked:boolean;tasks:{id:string;title:string;state:string;stale:boolean;session_available:boolean;kind:string}[];omitted_tasks:number;recommendation:LearningRecommendation;read_only:true;independent_success:false};
export function studyTaskHref(task:StudySummary["tasks"][number]){return /^[A-Za-z0-9_-]{1,80}$/.test(task.id)&&!task.stale&&task.session_available&&task.state!=="missing"?`/study?task=${encodeURIComponent(task.id)}`:null;}
export function recommendationHref(value:LearningRecommendation):string{
 const href=value.href;
 return href==="/study"||href==="/assessment"?href:/^\/study\?task=[A-Za-z0-9_-]{1,80}$/.test(href)||/^\/reading\?unit=[A-Za-z0-9_-]{1,80}$/.test(href)?href:"/study";
}
