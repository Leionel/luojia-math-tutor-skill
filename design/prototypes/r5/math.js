/* Bounded browser computations for a labelled prototype; no model or server. */
(function(root){
  'use strict';
  const finite = (v, name, bound=1e6) => { const n=Number(v); if(String(v).trim()===''||!Number.isFinite(n)||Math.abs(n)>bound)throw Error(name+'需要是范围内的有限数'); return n; };
  const integer=(v,name,min,max)=>{const n=finite(v,name);if(!Number.isInteger(n)||n<min||n>max)throw Error(name+'需要是 '+min+'–'+max+' 的整数');return n;};
  function newton(p){
    const x0=finite(p.x0,'初值'), limit=integer(p.limit??8,'步数',2,30),tol=finite(p.tolerance??1e-7,'阈值',1);
    if(tol<=0)throw Error('阈值必须大于 0');
    const f=p.function==='sqrt2'?x=>x*x-2:x=>x*x*x-2*x+2;
    const df=p.function==='sqrt2'?x=>2*x:x=>3*x*x-2;
    const rows=[];let x=x0,status='budget';
    for(let k=0;k<=limit;k++){
      const fx=f(x),d=df(x); if(!Number.isFinite(fx)||Math.abs(x)>1e12){status='non_finite';break;}
      rows.push({k,x,fx,derivative:d,residual:Math.abs(fx),delta:k?Math.abs(x-rows[k-1].x):null});
      if(Math.abs(fx)<=tol){status='residual_stop';break;}
      if(Math.abs(d)<1e-12){status='derivative_zero';break;}
      if(k>=2&&Math.abs(x-rows[k-2].x)<=1e-12&&Math.abs(x-rows[k-1].x)>tol){status='cycle';break;}
      x-=fx/d;
    }
    return {domain:'newton',parameters:{function:p.function==='sqrt2'?'sqrt2':'cycle',x0,limit,tolerance:tol},rows,status,
      expression:p.function==='sqrt2'?'f(x) = x² − 2':'f(x) = x³ − 2x + 2',scope:'有限浮点轨迹；停止状态不证明任意初值收敛'};
  }
  function numbers(text,count,label){ const parts=String(text).trim().split(/[\s,;；，]+/);if(parts.length!==count)throw Error(label+'需要 '+count+' 个数');return parts.map(x=>finite(x,label)); }
  function gs(p){
    const a=numbers(p.matrix,4,'矩阵'),b=numbers(p.rhs,2,'右端项'),initial=numbers(p.initial,2,'初值');
    if(a[0]===0||a[3]===0)throw Error('当前顺序的对角元素不能为 0；请修改矩阵');
    const limit=integer(p.limit??8,'步数',2,30),tol=finite(p.tolerance??1e-7,'阈值',1);if(tol<=0)throw Error('阈值必须大于 0');
    let [x,y]=initial;const rows=[];let status='budget';
    for(let k=0;k<=limit;k++){
      const r=Math.max(Math.abs(a[0]*x+a[1]*y-b[0]),Math.abs(a[2]*x+a[3]*y-b[1]));
      if(!Number.isFinite(r)||Math.max(Math.abs(x),Math.abs(y))>1e12){status='non_finite';break;}
      rows.push({k,x,y,residual:r,delta:k?Math.max(Math.abs(x-rows[k-1].x),Math.abs(y-rows[k-1].y)):null});
      if(r<=tol){status='residual_stop';break;}
      x=(b[0]-a[1]*y)/a[0];y=(b[1]-a[2]*x)/a[3];
    }
    return {domain:'gs',parameters:{matrix:a,rhs:b,initial,limit,tolerance:tol},rows,status,expression:'Gauss–Seidel · Ax = b',scope:'按新分量顺序迭代；有限轨迹不能证明一般收敛'};
  }
  function integrate(p){
    const left=finite(p.left,'左端点',10),right=finite(p.right,'右端点',10),n=integer(p.intervals??8,'子区间数',2,64);
    if(right<=left)throw Error('右端点应大于左端点');
    const method=p.method==='trapezoid'?'trapezoid':'simpson';if(method==='simpson'&&n%2)throw Error('Simpson 的子区间数必须为偶数');
    const h=(right-left)/n,rows=[];let sum=0;
    for(let k=0;k<=n;k++){const x=left+k*h,fx=Math.exp(x),weight=k===0||k===n?1:method==='simpson'?(k%2?4:2):2;sum+=weight*fx;rows.push({k,x,fx,weight,residual:null,partial:sum*h/(method==='simpson'?3:2),delta:null});}
    return {domain:'integration',parameters:{left,right,intervals:n,method},rows,status:'quadrature',approximation:rows.at(-1).partial,reference:Math.exp(right)-Math.exp(left),expression:'∫ exp(x) dx',scope:'浏览器浮点求积；解析积分的浮点参考差不是一般严格误差界'};
  }
  function hash(value){let h=2166136261;for(const c of JSON.stringify(value)){h^=c.charCodeAt(0);h=Math.imul(h,16777619);}return (h>>>0).toString(16).padStart(8,'0');}
  const api={newton,gs,integrate,hash,finite};root.R5Math=api;if(typeof module!=='undefined')module.exports=api;
})(globalThis);
