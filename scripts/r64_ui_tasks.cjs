// Run with playwright-cli run-code --filename scripts/r64_ui_tasks.cjs.
// Requires the isolated r61_ui_fixture API :8161 and production Web :3161.
async (page) => {
  const origin='http://127.0.0.1:3161';
  const tasks=[]; const ids={};
  const cases=[
    {id:'gs',task:'chat_to_gs_and_restore',claim:'GS不满足严格行对角占优是否一定发散？',prediction:'第二组不占优，我预测发散。',revision:'严格行对角占优是GS收敛充分条件，不能把不占优直接判为发散。',reason:'指定二阶反例的误差矩阵谱半径为1/5；轨迹只描述本次计算。'},
    {id:'newton',task:'newton_to_chat_and_return',claim:'Newton法对x^3-2*x+2从任意初值都收敛。',prediction:'初值0和-2应该都收敛。',revision:'该函数从0开始出现0与1循环，不能推广任意初值收敛。',reason:'保存轨迹0→1→0，可用Newton公式代数核对；-2残差达标不证明吸引域。'},
    {id:'integration',task:'integration_to_chat_and_return',claim:'对x^4在[0,1]用Simpson，误差估计小就证明严格误差界。',prediction:'步长减小可能改善近似；估计不是严格界。',revision:'步长比较支持局部数值观察；误差估计不能直接升格为严格界。',reason:'近似值改善，严格界仍需光滑性、导数界及舍入分析。'},
  ];
  for(const c of cases){
    const task={task_id:c.task,status:'failed',steps:[],artifact_refs:[],evidence_source:'offline_browser_fixture',model_quality:null};tasks.push(task);
    try{
      if(c.id!=='gs'){
        await page.goto(origin+'/chat');
        await page.getByRole('textbox',{name:/说说你的问题|围绕当前引用提问/}).fill(c.claim);
        await page.getByText('按需打开工具',{exact:true}).click();
        await page.getByRole('link',{name:'围绕当前问题探索',exact:true}).click();
      }
      if(await page.getByRole('textbox',{name:'我的数学主张',exact:true}).inputValue()!==c.claim)throw Error('Chat draft handoff mismatch');
      task.steps.push('Chat draft transferred through visible exploration link');
      await page.getByRole('textbox',{name:'探索名称',exact:true}).fill('R64 '+c.id+' 自动化任务');
      await page.getByRole('button',{name:'保存并开始探索',exact:true}).click();
      await page.getByRole('button',{name:'让助教分析并建议实验',exact:true}).click();
      await page.getByRole('button',{name:'采用建议参数并编辑',exact:true}).click();
      await page.getByRole('textbox',{name:'实验A limit',exact:true}).fill(c.id==='gs'?'41':c.id==='newton'?'13':'3');
      await page.getByRole('textbox',{name:'实验B limit',exact:true}).fill(c.id==='gs'?'41':c.id==='newton'?'13':'3');
      await page.getByRole('textbox',{name:'运行前我的预测',exact:true}).fill(c.prediction);
      await page.getByRole('checkbox',{name:'我已核对参数，确认运行参考计算',exact:true}).check();
      const execution=page.waitForResponse(r=>r.url().includes('/api/explorations/')&&r.url().endsWith('/runs')&&r.request().method()==='POST');
      await page.getByRole('button',{name:'确认执行受控实验',exact:true}).click();
      const executed=await (await execution).json();ids[c.id]=executed.id;
      task.steps.push('Edited limits, recorded prediction, explicitly confirmed real controlled runner');
      if(c.id==='gs'){
        await page.getByRole('button',{name:'接受为私人关联',exact:true}).first().click();
        await page.getByText(/已接受 · 私人确认，未经审核/).first().waitFor();
        task.steps.push('Accepted pending candidate as private relation');
      }
      await page.getByRole('textbox',{name:'我的数学主张',exact:true}).fill(c.revision);
      await page.getByRole('textbox',{name:'修订理由',exact:true}).fill(c.reason);
      const revision=page.waitForResponse(r=>r.url().endsWith('/claim')&&r.request().method()==='POST');
      await page.getByRole('button',{name:'保存主张修订',exact:true}).click();
      task.saved_record=await (await revision).json();
      await page.evaluate(()=>{for(const k of Object.keys(localStorage))if(k.startsWith('luojia_experiment_editor:')||k.startsWith('luojia_exploration:'))localStorage.removeItem(k);});
      await page.reload();
      await page.getByRole('heading',{name:'已保存的实验与证据',exact:true}).waitFor();
      if(await page.getByRole('textbox',{name:'我的数学主张',exact:true}).inputValue()!==c.revision)throw Error('claim did not restore');
      if(await page.getByRole('textbox',{name:'运行前我的预测',exact:true}).inputValue()!==c.prediction)throw Error('prediction did not restore');
      task.steps.push('Cleared local exploration drafts; prediction, revision and runs restored after refresh');
      await page.getByRole('heading',{name:'已保存的实验与证据',exact:true}).scrollIntoViewIfNeeded();
      const image='output/playwright/r64-'+c.id+'.png';await page.screenshot({path:image});task.artifact_refs.push(image);
      await page.getByRole('link',{name:'围绕这次已保存计算讨论',exact:true}).first().click();
      await page.getByRole('textbox',{name:'围绕当前引用提问，也可以先移除引用再自由讨论。',exact:true}).fill('仅依据保存的计算，解释现象与不能推出的结论。');
      await page.getByRole('button',{name:'发送',exact:true}).click();
      await page.getByText('本轮过程 · 回答已保存',{exact:true}).last().waitFor();
      await page.reload();
      await page.getByText('本轮过程 · 回答已保存',{exact:true}).last().waitFor();
      await page.getByRole('link',{name:'回看原始来源',exact:true}).first().click();
      await page.getByRole('heading',{name:'已保存的实验与证据',exact:true}).waitFor();
      task.steps.push('Returned to Chat with saved calculation reference, sent fixture discussion, restored saved answer, reopened original exploration');
      task.status='completed';
    }catch(error){task.failure=String(error);}
  }
  await page.evaluate(value=>localStorage.setItem('r64-automation-observations',JSON.stringify(value)),{tasks,ids});
  return {version:'r64-browser-partial-v1',tasks,ids};
}
