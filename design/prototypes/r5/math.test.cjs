const test=require('node:test');
const assert=require('node:assert/strict');
const M=require('./math.js');
test('Newton cycle is computed, not a synthetic plot',()=>{
  const r=M.newton({function:'cycle',x0:1});
  assert.deepEqual(r.rows.map(x=>x.x),[1,0,1]);assert.equal(r.status,'cycle');
  assert.ok(r.rows.every(x=>x.derivative!==0));
});
test('Changing only the initial value can approach the negative root',()=>{
  const r=M.newton({function:'cycle',x0:-2,limit:10});
  assert.equal(r.status,'residual_stop');assert.ok(Math.abs(r.rows.at(-1).x+1.769292354)<1e-7);
});
test('Derivative zero stops without claiming convergence',()=>{
  assert.equal(M.newton({function:'sqrt2',x0:0}).status,'derivative_zero');
});
test('GS uses the newly updated first component and reports actual residual',()=>{
  const r=M.gs({matrix:'4 1;2 3',rhs:'1 2',initial:'0 0'});
  assert.equal(r.rows[1].x,.25);assert.equal(r.rows[1].y,.5);assert.equal(r.rows[1].residual,.5);
  assert.ok(r.rows.at(-1).residual<r.rows[1].residual);
});
test('Quadrature retains node weights and matches an independent polynomial-free reference',()=>{
  const r=M.integrate({left:0,right:1,intervals:8,method:'simpson'});
  assert.deepEqual(r.rows.slice(0,5).map(x=>x.weight),[1,4,2,4,2]);
  assert.ok(Math.abs(r.approximation-(Math.E-1))<3e-6);
});
test('Invalid parameter states are rejected before computing',()=>{
  for(const action of [()=>M.newton({x0:'',limit:8}),()=>M.gs({matrix:'0 1;2 3',rhs:'1 2',initial:'0 0'}),()=>M.integrate({left:0,right:1,intervals:3})])assert.throws(action);
});
