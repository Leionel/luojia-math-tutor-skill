// Continue after r64_ui_tasks.cjs in the same isolated browser session.
async (page) => {
  const prior=await page.evaluate(()=>JSON.parse(localStorage.getItem('r64-automation-observations')));
  const tasks=prior.tasks;const origin='http://127.0.0.1:3161';
  const graph={task_id:'personal_graph_restore',status:'failed',steps:[],artifact_refs:[],model_quality:null};tasks.push(graph);
  try{
    await page.goto(origin+'/graph?view=personal');
    await page.getByRole('combobox',{name:'选择数学探索',exact:true}).selectOption(prior.ids.gs);
    await page.getByLabel('私人知识节点关系图',{exact:true}).waitFor();
    await page.getByText('初值与条件',{exact:true}).first().waitFor();
    await page.evaluate(()=>{for(const k of Object.keys(localStorage))if(k.includes('exploration')||k.includes('experiment_editor'))localStorage.removeItem(k);});
    // Select is navigation state; verify persisted graph after a full navigation.
    await page.goto(origin+'/graph?view=personal');
    await page.getByRole('combobox',{name:'选择数学探索',exact:true}).selectOption(prior.ids.gs);
    await page.getByLabel('私人知识节点关系图',{exact:true}).waitFor();
    await page.getByText('初值与条件',{exact:true}).first().waitFor();
    await page.screenshot({path:'output/playwright/r64-graph.png'});graph.artifact_refs.push('output/playwright/r64-graph.png');
    graph.steps.push('Selected accepted GS private graph; cleared local exploration drafts; navigated again and restored persisted nodes and relation');
    graph.status='completed';
  }catch(error){graph.failure=String(error);}
  const reading={task_id:'material_reference_restore',status:'failed',steps:[],artifact_refs:[],model_quality:null};tasks.push(reading);
  try{
    await page.goto(origin+'/reading');
    await page.getByRole('button',{name:/^讨论字符 /}).click();
    await page.getByRole('link',{name:'在完整聊天页讨论 ↗',exact:true}).click();
    await page.getByRole('textbox',{name:'围绕当前引用提问，也可以先移除引用再自由讨论。',exact:true}).fill('请只依据当前Newton原文，说明局部收敛需要的条件。');
    await page.getByRole('button',{name:'发送',exact:true}).click();
    await page.getByText('本轮过程 · 回答已保存',{exact:true}).last().waitFor();
    const savedUrl=page.url();
    await page.evaluate(()=>{for(const k of Object.keys(localStorage))if(k.startsWith('reading-selection:'))localStorage.removeItem(k);});
    await page.goto(savedUrl);
    await page.getByText('本轮过程 · 回答已保存',{exact:true}).last().waitFor();
    await page.getByText('回看这条回答实际引用的原文',{exact:true}).last().click();
    await page.getByRole('blockquote').last().waitFor();
    await page.screenshot({path:'output/playwright/r64-reading.png'});reading.artifact_refs.push('output/playwright/r64-reading.png');
    await page.getByRole('link',{name:'回看原始来源',exact:true}).first().click();
    await page.getByRole('textbox',{name:'原文选择框',exact:true}).waitFor();
    reading.steps.push('Selected original Newton reading; opened full Chat; sent reference-bound question; restored saved message after removing local reading selection; opened persisted quote and original source');
    reading.status='completed';
  }catch(error){reading.failure=String(error);}
  return {version:'r64-browser-v1',participant_type:'agent_automation',human_participants:0,tasks,ids:prior.ids};
}
