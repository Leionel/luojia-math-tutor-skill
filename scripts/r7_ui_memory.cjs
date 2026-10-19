// Playwright CLI; existing R65 offline fixture on :8000, production Web :3161.
async (page) => {
  const origin='http://127.0.0.1:3161', rows=[];
  await page.goto(origin+'/chat?new=1');
  await page.evaluate(()=>localStorage.setItem('luojia_demo_access','true'));
  const input=()=>page.getByRole('textbox',{name:/说说你的问题|围绕当前引用提问/});
  const settle=()=>page.waitForFunction(()=>!document.getAnimations().some(a=>a.playState==='running'&&a.effect?.getComputedTiming().iterations!==Infinity));
  async function send(question){
    await page.goto(origin+'/chat?new=1');await input().fill(question);
    await page.getByRole('button',{name:'发送',exact:true}).click();
    await page.getByText('本轮过程 · 回答已保存',{exact:true}).last().waitFor();
  }
  await page.setViewportSize({width:1440,height:1000});
  await send('牛顿法换个出发点会怎样？');
  const why=()=>page.getByText('为何联想到这个旧判断／实验',{exact:true});
  await why().waitFor();await why().click();
  await page.getByText('原判断：Newton任意初值都收敛',{exact:true}).waitFor();
  await page.getByText('后来修订：Newton并非任意初值都收敛',{exact:true}).waitFor();
  await settle();await page.screenshot({path:'output/playwright/r7-p1-history-final.png',fullPage:true});
  const session=new URL(page.url()).searchParams.get('session');
  await page.reload();await why().waitFor();await why().click();
  const source=page.getByRole('link',{name:/打开原始探索（本轮引用版本/});
  const href=await source.getAttribute('href');
  if(!href.includes('r7-browser-history')||!href.includes('revision=4'))throw Error('original version locator lost');
  await source.focus();await page.keyboard.press('Enter');
  await page.getByRole('textbox',{name:'我的数学主张',exact:true}).waitFor();
  if(await page.getByRole('textbox',{name:'我的数学主张',exact:true}).inputValue()!=='Newton并非任意初值都收敛')throw Error('wrong original claim version');
  await settle();await page.screenshot({path:'output/playwright/r7-p1-source-final.png',fullPage:true});
  rows.push({task:'paraphrase recall, saved explanation, reload and keyboard source return',status:'completed',session,href});
  await page.setViewportSize({width:390,height:844});
  await send('Newton 导数为零时为什么不能更新？');
  if(await why().count())throw Error('same-method unrelated history leaked');
  await page.reload();await page.getByText('本轮过程 · 回答已保存',{exact:true}).last().waitFor();
  if(await why().count())throw Error('unrelated history persisted after reload');
  const width=await page.evaluate(()=>({client:document.documentElement.clientWidth,scroll:document.documentElement.scrollWidth}));
  if(width.scroll>width.client)throw Error('mobile page overflow '+JSON.stringify(width));
  await settle();await page.screenshot({path:'output/playwright/r7-p2-mobile-final.png',fullPage:true});
  rows.push({task:'same-method unrelated history excluded, mobile and refresh',status:'completed',width});
  return {version:'r7-memory-browser-v1',tasks:rows,provider_requests:0,human_participants:0,
    scope:'automated functionality with fixed model reply; no mathematical teaching-quality rating'};
}
