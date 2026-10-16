/** Upload state describes this request only; it is not a background job. */
export const DOCUMENT_ACCEPT=".pdf,.doc,.docx,.pptx";
export function documentUploadError(file:{name:string;size:number}):string|null {
  if(!/\.(pdf|docx?|pptx)$/i.test(file.name))return "请选择 PDF、Word 或 PPTX 文档。";
  if(file.size===0)return "文件为空，请重新选择。";
  if(file.size>200*1024*1024)return "文件超过 200MB，请拆分后上传。";
  return null;
}
export function materialStatus(status:string|undefined) {return status==="ready"?"原文已保存":status==="source_missing"?"缺少解析原文，需重新导入":"解析状态待核对";}
