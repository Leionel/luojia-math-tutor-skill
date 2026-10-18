// playwright-cli run-code --filename scripts/r65_ui_tasks.cjs (isolated fixture :8161, Web :3161)
async (page) => {
  const origin='http://127.0.0.1:3161',tasks=[],measurements={};let id,session,revision;
  const claim='GS不满足严格行对角占优是否一定发散？';
  async function task(name,fn){const entry={task:name,status:'failed',artifacts:[]};tasks.push(entry);try{await fn(entry);entry.status='completed';}catch(e){entry.failure=String(e);}}
  const plain=()=>page.getByRole('textbox',{name:/说说你的问题|围绕当前引用提问/});
  const source=()=>page.getByRole('link',{name:'回看原始来源',exact:true}).first();
  async function revealSource(){if(!await source().isVisible())await page.getByText(/^正在讨论 ·/).first().click();await source().waitFor();}
  await page.setViewportSize({width:1440,height:1000});
  await task('Chat → 探索 → 原会话',async t=>{
    await page.goto(origin+'/chat?new=1');
    const freeCalls=[];const freeListener=r=>{if(r.url().includes(':8161/api/'))freeCalls.push({method:r.method(),path:new URL(r.url()).pathname});};page.on('request',freeListener);
    try{await plain().fill(claim);await page.getByRole('button',{name:'发送',exact:true}).click();await page.getByText('本轮过程 · 回答已保存',{exact:true}).last().waitFor();}
    finally{page.off('request',freeListener);}
    measurements.free_chat_requests=freeCalls;
    measurements.automatic_title_model_requests=freeCalls.filter(r=>r.path==='/api/tutor/generate_title').length;
    if(measurements.automatic_title_model_requests!==0)throw Error('unnecessary title model request');
    session=new URL(page.url()).searchParams.get('session');if(!session)throw Error('saved Chat session locator missing');
    const entry=page.getByRole('link',{name:'围绕当前问题探索',exact:true});if(!await entry.isVisible())throw Error('entry hidden');
    await page.screenshot({path:'output/playwright/r65-after-chat.png'});t.artifacts.push('output/playwright/r65-after-chat.png');
    await entry.focus();await page.keyboard.press('Enter');await page.getByRole('textbox',{name:'我的数学主张',exact:true}).waitFor();
    if(await page.getByRole('textbox',{name:'我的数学主张',exact:true}).inputValue()!==claim)throw Error('claim handoff lost');
    await page.getByRole('textbox',{name:'探索名称',exact:true}).fill('R65 完整探索');
    const calls=[];const listener=r=>{if(r.url().includes(':8161/api/'))calls.push({method:r.method(),path:new URL(r.url()).pathname});};page.on('request',listener);
    try{
      const created=page.waitForResponse(r=>r.url().endsWith('/api/explorations')&&r.request().method()==='POST');
      await page.getByRole('button',{name:'保存并开始探索',exact:true}).click();id=(await (await created).json()).id;
      await page.getByRole('button',{name:'让助教分析并建议实验',exact:true}).waitFor();
      if(await page.getByRole('textbox',{name:'实验A matrix',exact:true}).isVisible())throw Error('blank parameter wall shown before choosing design');
      await page.screenshot({path:'output/playwright/r65-after-first-step.png'});t.artifacts.push('output/playwright/r65-after-first-step.png');
      const start=Date.now();await page.getByRole('button',{name:'让助教分析并建议实验',exact:true}).click();
      await page.getByRole('button',{name:'采用建议参数并编辑',exact:true}).click();measurements.fixture_advice_to_edit_ms=Date.now()-start;
      await page.getByRole('textbox',{name:'实验A limit',exact:true}).fill('41');await page.getByRole('textbox',{name:'实验B limit',exact:true}).fill('41');
      await page.getByRole('textbox',{name:'运行前我的预测',exact:true}).fill('我预测不占优会发散，先看指定矩阵。');
      const check=page.getByRole('checkbox',{name:'我已核对参数，确认运行参考计算',exact:true});await check.focus();await page.keyboard.press('Space');
      const run=page.waitForResponse(r=>r.url().endsWith('/runs')&&r.request().method()==='POST');await page.getByRole('button',{name:'确认执行受控实验',exact:true}).click();
      const computed=await (await run).json();const runs=computed.history.findLast(h=>h.action==='run').payload.runs;
      if(runs[1].matrix_evidence.spectral_radius_exact!=='1/5')throw Error('actual GS evidence missing');
      const accepted=page.waitForResponse(r=>r.url().endsWith('/relations/decision')&&r.request().method()==='POST');
      await page.getByRole('button',{name:'接受为私人关联',exact:true}).first().click();revision=(await (await accepted).json()).revision;
      measurements.comparable_mutation_requests=calls;measurements.controlled_evidence=runs.map(r=>({status:r.status,last_row:r.rows.at(-1),matrix_evidence:r.matrix_evidence}));
    }finally{page.off('request',listener);}
    await page.getByRole('link',{name:'返回原会话',exact:true}).click();await page.getByText('本轮过程 · 回答已保存',{exact:true}).last().waitFor();
    if(new URL(page.url()).searchParams.get('session')!==session)throw Error('did not return to original session');
    t.steps=['Visible Chat entry with Enter','Persisted original claim and session','Collapsed blank parameters; edited proposal and prediction','Confirmed real runner with Space','Accepted private relation; returned to original session'];
  });
  await task('计算 → 引用会话 → 原探索版本',async t=>{
    if(!id)throw Error('previous exploration missing');await page.goto(origin+'/explore?id='+id);
    await page.getByRole('link',{name:/^(带着这次计算与小珞讨论|围绕这次已保存计算讨论)$/}).first().click();await plain().fill('只依据保存的计算，解释不能推广的结论。');
    await page.getByRole('button',{name:'发送',exact:true}).click();await page.getByText('本轮过程 · 回答已保存',{exact:true}).last().waitFor();
    await page.reload();await page.getByText('本轮过程 · 回答已保存',{exact:true}).last().waitFor();await revealSource();
    const href=await source().getAttribute('href');if(!href.includes('revision=')||!href.includes('run='))throw Error('source locator dropped version/run');
    await source().click();await page.getByRole('heading',{name:'正在查看历史版本 '+revision,exact:true}).waitFor();
    await page.screenshot({path:'output/playwright/r65-after-history.png'});t.artifacts.push('output/playwright/r65-after-history.png');
    t.steps=['Discussed actual saved calculation','Reloaded saved answer','Original source retained revision and computation locator'];
  });
  await task('私人图 → 原探索（无需选择节点）',async t=>{
    if(!id)throw Error('previous exploration missing');
    await page.goto(origin+'/graph?view=personal&exploration='+id);await page.getByRole('link',{name:'回到这次探索与历史',exact:true}).waitFor();
    await page.getByLabel('私人知识节点关系图',{exact:true}).waitFor();await page.screenshot({path:'output/playwright/r65-after-graph.png'});t.artifacts.push('output/playwright/r65-after-graph.png');
    await page.getByRole('link',{name:'回到这次探索与历史',exact:true}).focus();await page.keyboard.press('Enter');
    await page.getByRole('heading',{name:'正在查看历史版本 '+revision,exact:true}).waitFor();t.steps=['No node click required','Keyboard return preserves exploration and version'];
  });
  await task('主张修订 → 学习记录 → 旧版本恢复',async t=>{
    if(!id)throw Error('previous exploration missing');
    await page.goto(origin+'/explore?id='+id);await page.getByRole('textbox',{name:'我的数学主张',exact:true}).fill('严格行对角占优是充分条件，但不是必要条件。');
    await page.getByRole('textbox',{name:'修订理由',exact:true}).fill('保存的二阶反例谱半径为1/5；仅针对这组输入。');
    const save=page.waitForResponse(r=>r.url().endsWith('/claim')&&r.request().method()==='POST');await page.getByRole('button',{name:'保存主张修订',exact:true}).click();revision=(await (await save).json()).revision;
    await page.goto(origin+'/records');const link=page.locator(`a[href*="/explore?id=${id}"]`).first();await link.waitFor();
    if(!(await link.getAttribute('href')).includes('revision='+revision))throw Error('record lost historical locator');await link.click();
    await page.getByRole('heading',{name:'正在查看历史版本 '+revision,exact:true}).waitFor();await page.getByRole('combobox',{name:'选择探索历史版本',exact:true}).selectOption('1');
    const historical=page.getByRole('region',{name:'历史版本 1',exact:true});await historical.getByText('当时的主张：'+claim,{exact:true}).waitFor();
    await page.evaluate(()=>{for(const k of Object.keys(localStorage))if(k.startsWith('luojia_experiment_editor:')||k.startsWith('luojia_exploration:'))localStorage.removeItem(k);});await page.reload();
    await page.getByRole('heading',{name:'正在查看历史版本 1',exact:true}).waitFor();if((await page.getByRole('textbox',{name:'我的数学主张',exact:true}).inputValue())===claim)throw Error('history overwrote current claim');
    await page.goto(origin+'/explore?id='+id+'&revision=99999');await page.getByText('找不到指定历史版本。没有替换为其他版本；请选择已有记录。',{exact:true}).waitFor();
    let sourceCalls=0;const reads=r=>{if(r.url().endsWith('/api/explorations/sources'))sourceCalls++;};page.on('request',reads);
    try{
      const sourceResponse=page.waitForResponse(r=>r.url().endsWith('/api/explorations/sources'));
      const editor=page.getByText(/编辑.*节点.*来源/).first();await editor.click();if((await sourceResponse).status()!==200)throw Error('source catalogue unavailable');
      await editor.click();await editor.click();if(sourceCalls!==1)throw Error('source catalogue fetched repeatedly');measurements.lazy_source_catalogue_reads=sourceCalls;
    }finally{page.off('request',reads);}
    t.steps=['Saved new claim with reason','Records linked exact saved version','Selected original claim; cleared local drafts and restored','Latest editable claim stayed separate from historical claim'];
  });
  await task('模型响应丢失 → 读取已保存建议（不重复模型）',async t=>{
    if(!id)throw Error('previous exploration missing');
    await page.goto(origin+'/explore?id='+id);let posts=0;
    const listener=r=>{if(r.method()==='POST'&&r.url().endsWith('/advice'))posts++;};page.on('request',listener);
    await page.route('**/api/explorations/*/advice',async route=>{await route.fetch();await route.abort('failed');},{times:1});
    try{
      await page.getByRole('button',{name:'让助教分析并建议实验',exact:true}).click();
      await page.getByRole('button',{name:'重新读取已保存建议（不调用模型）',exact:true}).waitFor();
      await page.getByRole('button',{name:'重新读取已保存建议（不调用模型）',exact:true}).click();await page.getByText('已读取服务端保存的建议，本次没有请求模型。',{exact:true}).waitFor();
      if(posts!==1)throw Error('unexpected repeated model request');measurements.dropped_response_model_posts=posts;
      await page.screenshot({path:'output/playwright/r65-after-recovery.png'});t.artifacts.push('output/playwright/r65-after-recovery.png');
    }finally{page.off('request',listener);}
    t.steps=['Injected response loss after actual fixture persisted advice','Explicit recovery used GET only','Exactly one advice POST; no automatic model retry'];
  });
  await task('私有资料 → 选段对话 → 已保存引用恢复',async t=>{
    await page.goto(origin+'/materials');await page.getByRole('button',{name:/^(选段研讨|选择用于对话)$/}).first().click();
    await page.route('**/api/tutor/context',async route=>{await new Promise(resolve=>setTimeout(resolve,1200));await route.continue();},{times:1});
    const restoring=page.waitForRequest(r=>r.url().endsWith('/api/tutor/context'));
    await page.getByRole('button',{name:/^带此章节进入对话(研思)?$/}).click();await restoring;
    measurements.material_input_locked_during_restore=!await plain().isEditable();
    if(!measurements.material_input_locked_during_restore)throw Error('input can be lost during source restore');
    await plain().fill('仅依据这份合成资料，说明哪些条件仍需核对。');await page.getByRole('button',{name:'发送',exact:true}).click();await page.getByText('本轮过程 · 回答已保存',{exact:true}).last().waitFor();
    await page.reload();await page.getByText('本轮过程 · 回答已保存',{exact:true}).last().waitFor();await page.getByText('回看这条回答实际引用的原文',{exact:true}).last().click();
    await page.getByRole('blockquote').last().waitFor();await page.screenshot({path:'output/playwright/r65-after-material.png'});t.artifacts.push('output/playwright/r65-after-material.png');
    t.steps=['Synthetic owned material, no external parser','Full Chat preserves exact citation after reload'];
  });
  await task('390px 与键盘：手工回退、长参数、表格',async t=>{
    if(!id)throw Error('previous exploration missing');
    await page.setViewportSize({width:390,height:844});await page.goto(origin+'/explore?id='+id+'&revision=1');await page.getByRole('heading',{name:'正在查看历史版本 1',exact:true}).waitFor();
    await page.getByRole('button',{name:'手工设计实验（无需模型）',exact:true}).focus();await page.keyboard.press('Enter');
    await page.getByRole('textbox',{name:'实验A matrix',exact:true}).waitFor();await page.getByRole('textbox',{name:'实验A matrix',exact:true}).fill('12345678901234567890 '.repeat(20));
    const width=await page.evaluate(()=>document.documentElement.scrollWidth);if(width>390)throw Error('mobile page overflow '+width);measurements.mobile={viewport:390,scrollWidth:width};
    await page.screenshot({path:'output/playwright/r65-after-mobile.png'});t.artifacts.push('output/playwright/r65-after-mobile.png');
    await page.getByRole('button',{name:'采用 GS 默认示例',exact:true}).click();await page.getByRole('textbox',{name:'运行前我的预测',exact:true}).fill('手工示例只用于比较指定参数。');
    const box=page.getByRole('checkbox',{name:'我已核对参数，确认运行参考计算',exact:true});await box.focus();await page.keyboard.press('Space');
    if(!await page.getByRole('button',{name:'确认执行受控实验',exact:true}).isEnabled())throw Error('keyboard cannot enable run');
    const execution=page.waitForResponse(r=>r.url().endsWith('/runs')&&r.request().method()==='POST');
    await page.getByRole('button',{name:'确认执行受控实验',exact:true}).click();if((await execution).status()!==200)throw Error('manual runner did not complete');
    if(await page.evaluate(()=>document.documentElement.scrollWidth)>390)throw Error('saved table breaks mobile layout');
    await page.goto(origin+'/materials');await page.locator('a[href*="/reading?document="]').first().click();
    await page.getByRole('textbox',{name:'原文选择框',exact:true}).waitFor();await page.locator('.katex-display').first().waitFor();
    const layout=await page.evaluate(()=>Array.from(document.querySelectorAll('main,[class~="overflow-y-auto"]')).filter(e=>e.clientWidth>0).map(e=>({tag:e.tagName,width:e.clientWidth,scroll:e.scrollWidth})));
    if(layout.some(e=>e.scroll>e.width+2))throw Error('long formula widens a main scroll area: '+JSON.stringify(layout));measurements.long_formula_layout=layout;
    const formulaWidth=await page.evaluate(()=>document.documentElement.scrollWidth);if(formulaWidth>390)throw Error('long formula breaks mobile layout '+formulaWidth);measurements.long_formula_page_width=formulaWidth;
    await page.locator('.math-block').first().scrollIntoViewIfNeeded();
    await page.screenshot({path:'output/playwright/r65-after-mobile-formula.png'});t.artifacts.push('output/playwright/r65-after-mobile-formula.png');
    t.steps=['390px old-version view','Enter opens manual editor, Space confirms parameters','Long draft stays contained','No-model default example executes actual runner; saved table contained'];
  });
  const result={version:'r65-browser-v1',scope:'offline_functional_automation_not_human_or_model_quality',human_participants:0,provider_requests:0,tasks,measurements,exploration_id:id,origin_session:session};
  await page.evaluate(r=>localStorage.setItem('r65-after',JSON.stringify(r)),result);return result;
}
