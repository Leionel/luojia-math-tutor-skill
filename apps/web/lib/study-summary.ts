import type {LearningOverview,LearningRecommendation} from "./learning-api";
export type StudySummary={version:"study-summary-v1";local_date:string;read_at:string;plan_exists:boolean;stale:boolean;help_locked:boolean;tasks:{id:string;title:string;state:string;stale:boolean;session_available:boolean;kind:string}[];omitted_tasks:number;recommendation:LearningRecommendation;read_only:true;independent_success:false};
export function studyTaskHref(task:StudySummary["tasks"][number]){return /^[A-Za-z0-9_-]{1,80}$/.test(task.id)&&!task.stale&&task.session_available&&task.state!=="missing"?`/study?task=${encodeURIComponent(task.id)}`:null;}
export function recommendationHref(value:LearningRecommendation):string{
 const href=value.href;
 return href==="/study"||href==="/assessment"?href:/^\/study\?task=[A-Za-z0-9_-]{1,80}$/.test(href)||/^\/reading\?unit=[A-Za-z0-9_-]{1,80}$/.test(href)?href:"/study";
}
export function homeNextStep(overview:Pick<LearningOverview,"recommendation"|"active_assessment"|"next_task">|null){
 const recommendation=overview?.recommendation;
 if(!recommendation)return {href:"/study",title:"给数值分析留一段时间",reason:"安排 15 或 30 分钟。阅读、练习与独立检验会分别记录。",label:"安排今日学习"};
 const labels:Record<string,string>={assessment_in_progress:"继续章节自检",confirm_feedback:"确认过程反馈",revise_process:"修订求根过程",due_review:"安排到期复习",stale_source:"核对课程来源",resume_task:"继续这项任务"};
 const progress=overview?.active_assessment;
 return {href:recommendationHref(recommendation),title:recommendation.title,
  reason:recommendation.kind==="assessment_in_progress"&&progress?`已保存 ${progress.answered} / ${progress.total} 题。${recommendation.reason}`:recommendation.reason,
  label:labels[recommendation.kind]??"查看今日学习"};
}
