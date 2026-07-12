import { useEffect, useMemo, useState } from 'react';
import {
  ArrowRight, Check, CheckCircle, CircleNotch, FileImage, ImageSquare,
  LockKey, MagicWand, ShieldCheck, Sparkle, TrendUp, WarningCircle
} from '@phosphor-icons/react';
import './workflow.css';

const reviewModules = [
  ['产品KV/封面故事', 10, 0.5, 5, '中'],
  ['沉浸式购物/场景化', 18, 0.5, 9, '中'],
  ['卖点与功能证明', 14, 0.5, 7, '中'],
  ['产品互动/动态内容', 8, 0, 0, '弱'],
  ['细节查阅', 12, 1, 12, '强'],
  ['尺码/适配与对比选购', 10, 0.5, 5, '中'],
  ['基础信息', 8, 1, 8, '强'],
  ['使用说明/服务事项', 5, 0.5, 2.5, '中'],
  ['关联推荐/延展购买', 5, 0.5, 2.5, '中'],
  ['品牌/产品背书', 5, 0.5, 2.5, '中'],
  ['页面结构与节奏', 5, 1, 5, '强'],
];

export function AnalysisPage({ onReview, onBack }) {
  const [step, setStep] = useState(0);
  const stages = [
    ['文件解析', '读取页面尺寸、格式和版本信息'],
    ['页面切片与 OCR', '识别 12 个页面区块与主要文字'],
    ['11 模块映射', '匹配内容、视觉证据和消费者问题'],
    ['评分与优化推演', '生成初评、优先级和预计提升区间'],
  ];
  useEffect(() => {
    if (step >= stages.length) return;
    const timer = window.setTimeout(() => setStep(s => s + 1), 650);
    return () => window.clearTimeout(timer);
  }, [step, stages.length]);
  const progress = Math.min(100, step / stages.length * 100);
  return <section className="diagnosis-progress-screen">
    <header className="progress-header"><div className="progress-brand"><span>PDP</span><b>Lab</b></div><button onClick={onBack}>返回首页</button></header>
    <div className="workflow-page analysis-page">
      <div className="analysis-heading">
        <div><div className="workflow-kicker"><CircleNotch className={step < stages.length ? 'spin' : ''} /> AI 诊断任务 · v1</div><h2>{step < stages.length ? '正在分析这份 PDP' : '初步诊断已完成'}</h2><p className="workflow-lead">系统正在按 11 模块评分规则识别信息质量、视觉素材和购买决策证据。</p></div>
        <div className="progress-value"><strong>{Math.round(progress)}%</strong><span>{step < stages.length ? '诊断处理中' : '等待人工确认'}</span></div>
      </div>
      <div className="analysis-progress"><span style={{width:`${progress}%`}} /></div>
      <div className="analysis-stages">{stages.map((stage,index) => <div className={index < step ? 'done' : index === step ? 'active' : ''} key={stage[0]}><i>{index < step ? <Check /> : index + 1}</i><span><strong>{stage[0]}</strong><small>{stage[1]}</small></span><em>{index < step ? '完成' : index === step ? '处理中' : '等待'}</em></div>)}</div>
      <div className="workflow-note"><ShieldCheck /><span><b>评分不会自动锁定</b><small>诊断完成后需要人工检查证据与模块成熟度，再生成正式评分版本。</small></span></div>
      <div className="workflow-actions"><span className="progress-hint">离开此页不会中断诊断任务</span><button className="primary" disabled={step < stages.length} onClick={onReview}>检查 AI 初评 <ArrowRight /></button></div>
    </div>
  </section>;
}

export function ScoreReviewPage({ onConfirm }) {
  const [selected, setSelected] = useState(2);
  const [checked, setChecked] = useState(new Set([0,1]));
  const current = reviewModules[selected];
  const toggleChecked = index => setChecked(prev => { const next=new Set(prev); next.has(index)?next.delete(index):next.add(index); return next; });
  return <div className="review-layout">
    <section className="panel review-list">
      <div className="workflow-panel-head"><div><small>AI 初评 · 待确认</small><h2>检查 11 个模块</h2></div><span>{checked.size}/11 已检查</span></div>
      <div className="review-rows">{reviewModules.map((m,index)=><button className={selected===index?'selected':''} key={m[0]} onClick={()=>setSelected(index)}><i className={checked.has(index)?'checked':''} onClick={e=>{e.stopPropagation();toggleChecked(index)}}>{checked.has(index)&&<Check />}</i><span>{m[0]}</span><em className={m[4]==='强'?'strong':m[4]==='弱'?'weak':'medium'}>{m[4]}</em><b>{m[3]}/{m[1]}</b></button>)}</div>
    </section>
    <section className="panel review-evidence">
      <div className="review-evidence-head"><span>证据核对</span><h2>{current[0]}</h2><div><strong>{current[3]}</strong><small>/ {current[1]} 分</small><em className={current[4]==='强'?'strong':current[4]==='弱'?'weak':'medium'}>{current[4]}</em></div></div>
      <div className="evidence-preview"><img src="/projects/nike-kids-learning-shoe.png" alt="当前 PDP 页面证据"/><span>识别区域 03 · 卖点表达</span></div>
      <div className="review-judgment"><small>AI 判断</small><h3>有对应内容，但证明方式不足</h3><p>产品功能有表达，但缺少结构示意、测试数据或场景验证，因此信息与视觉任一维度未达到“强”。</p></div>
      <div className="coefficient-picker"><span>确认成熟度</span>{[['弱',0],['中',.5],['强',1]].map(x=><button className={current[2]===x[1]?'active':''} key={x[0]}>{x[0]} · {x[1]}</button>)}</div>
      <button className="mark-checked" onClick={()=>toggleChecked(selected)}>{checked.has(selected)?<CheckCircle weight="fill"/>:<CheckCircle/>}{checked.has(selected)?'已检查此模块':'确认此模块证据'}</button>
      <div className="workflow-actions review-confirm"><div><LockKey/><span>确认后生成评分版本 v1，可在审计记录中追溯。</span></div><button className="primary" onClick={onConfirm}>确认并锁定评分 <ArrowRight /></button></div>
    </section>
  </div>;
}

const matchedAssets = [
  {id:'a1',name:'中底剖面与缓震结构',type:'产品结构图',status:'可直接使用',image:'/final/02-proof.png'},
  {id:'a2',name:'儿童户外运动场景',type:'场景素材',status:'需编辑',image:'/final/03-scene.png'},
  {id:'a3',name:'尺码测量与脚型建议',type:'信息模板',status:'可直接使用',image:'/final/04-fit.png'},
  {id:'a4',name:'主视觉商品封面',type:'KV 模板',status:'需生成',image:'/final/01-hero.png'},
];

export function AssetMatchPage({ onGenerate }) {
  const [selected,setSelected]=useState(new Set(['a1','a2','a3']));
  const toggle=id=>setSelected(prev=>{const n=new Set(prev);n.has(id)?n.delete(id):n.add(id);return n});
  return <section className="asset-match-page">
    <div className="match-summary"><div><span>优化任务 P0 + P1</span><h2>品牌资产匹配结果</h2><p>根据卖点证明、场景化和尺码适配三个缺口，共找到 4 项候选资产。</p></div><div className="match-stats"><strong>3</strong><span>已选择</span><strong>1</strong><span>需生成</span></div></div>
    <div className="asset-requirements"><span>本次页面需要</span><b>结构证明</b><b>真实场景</b><b>尺码指导</b><b>主视觉升级</b></div>
    <div className="matched-grid">{matchedAssets.map(asset=><button className={selected.has(asset.id)?'selected':''} key={asset.id} onClick={()=>toggle(asset.id)}><div className="matched-image"><img src={asset.image} alt=""/><i>{selected.has(asset.id)&&<Check/>}</i></div><span>{asset.type}</span><strong>{asset.name}</strong><small className={asset.status==='需生成'?'generate':asset.status==='需编辑'?'edit':''}>{asset.status}</small></button>)}</div>
    <div className="match-gap"><WarningCircle weight="fill"/><div><b>仍缺少一项真实测试数据</b><span>可先使用品牌已审核的材料说明生成草稿，正式上线前补充测试结果。</span></div><button>创建补充任务</button></div>
    <div className="workflow-actions"><div className="asset-policy"><ShieldCheck/><span>仅使用当前品牌授权资产，生成结果默认进入待审核状态。</span></div><button className="primary" disabled={!selected.size} onClick={()=>onGenerate([...selected])}>使用 {selected.size} 项资产生成 <MagicWand /></button></div>
  </section>;
}

export function GenerationPage({ assetIds, onComplete }) {
  const [progress,setProgress]=useState(0);
  useEffect(()=>{if(progress>=100)return;const t=window.setTimeout(()=>setProgress(p=>Math.min(100,p+20)),500);return()=>window.clearTimeout(t)},[progress]);
  const stage=progress<25?'整理页面结构':progress<50?'生成卖点证明':progress<75?'组合场景与细节':progress<100?'执行品牌一致性检查':'生成完成';
  return <section className="workflow-page generation-page">
    <div className="generation-icon"><Sparkle weight="fill"/></div><span className="workflow-kicker">AI 页面生成任务 · 草稿 v2</span><h2>{stage}</h2><p className="workflow-lead">基于已锁定评分、P0/P1 优化任务与 {assetIds.length} 项品牌资产生成新版 PDP。</p>
    <div className="generation-progress"><span style={{width:`${progress}%`}}/><b>{progress}%</b></div>
    <div className="generation-brief"><div><small>目标层级</small><b>T1 强</b></div><div><small>预计总分</small><b>79 / 100</b></div><div><small>预计星级</small><b>5.5 星</b></div><div><small>输出模块</small><b>4 个页面段落</b></div></div>
    <div className="generation-checks"><span className={progress>=40?'done':''}><CheckCircle/>商品结构真实性</span><span className={progress>=60?'done':''}><CheckCircle/>品牌视觉一致性</span><span className={progress>=80?'done':''}><CheckCircle/>功能宣称检查</span><span className={progress>=100?'done':''}><CheckCircle/>页面结构与节奏</span></div>
    <div className="workflow-actions"><button className="primary" disabled={progress<100} onClick={onComplete}>查看最终优化页面 <ArrowRight /></button></div>
  </section>;
}

export function FinalPage({ onRescore, onBackTasks }) {
  return <section className="final-page">
    <div className="final-head"><div><span>优化页面草稿 v2</span><h2>最终优化页面</h2><p>已应用卖点证明、真实场景、尺码指导和主视觉升级。</p></div><div><button className="secondary" onClick={onBackTasks}>返回优化任务</button><button className="primary" onClick={onRescore}>发起复评 <TrendUp /></button></div></div>
    <div className="before-after">
      <div className="version-column before"><div><span>优化前 · v1</span><b>58 分 · 4.5 星</b></div><div className="long-page original"><img src="/projects/nike-kids-learning-shoe.png" alt="优化前 PDP"/></div></div>
      <div className="version-column after"><div><span>优化后 · v2</span><b>预计 79 分 · 5.5 星</b></div><div className="long-page optimized">{['01-hero','02-proof','03-scene','04-fit'].map(name=><img key={name} src={`/final/${name}.png`} alt="优化后 PDP 段落"/>)}</div></div>
      <aside className="applied-changes"><span>本轮已应用</span><div><i>+7</i><b>卖点与功能证明</b><small>结构图、测试逻辑和用户利益</small></div><div><i>+9</i><b>沉浸式场景</b><small>场景、动作和利益点绑定</small></div><div><i>+5</i><b>尺码与适配</b><small>脚型、测量和选择建议</small></div><div className="review-status"><ShieldCheck weight="fill"/><span><b>待人工审核</b><small>商品真实性与宣称数据需最终确认</small></span></div></aside>
    </div>
  </section>;
}

export function RescorePage({ onFinish }) {
  const changes=[['沉浸式购物/场景化','中','强','9 → 18'],['卖点与功能证明','中','强','7 → 14'],['尺码/适配与对比选购','中','强','5 → 10'],['产品KV/封面故事','中','强','5 → 10']];
  return <section className="rescore-page"><div className="rescore-hero"><div><span>复评结果 · v2</span><h2>页面进入成熟转化增强阶段</h2><p>四个关键模块由“中”提升到“强”，页面结构达到 T1 强标准。</p></div><div className="score-shift"><span><small>优化前</small><b>58</b><em>4.5 星</em></span><ArrowRight/><span className="after"><small>优化后</small><b>79</b><em>5.5 星</em></span></div></div><div className="rescore-grid"><section className="panel"><div className="workflow-panel-head"><div><small>模块变化</small><h2>本轮提升明细</h2></div></div>{changes.map(c=><div className="rescore-row" key={c[0]}><span>{c[0]}</span><em className="medium">{c[1]}</em><ArrowRight/><em className="strong">{c[2]}</em><b>{c[3]}</b></div>)}</section><section className="panel expected-value"><div className="workflow-panel-head"><div><small>上线验证</small><h2>建议关注指标</h2></div></div><div><span>首屏继续浏览率</span><b>验证快速决策信息</b></div><div><span>卖点模块停留</span><b>验证证明素材解释力</b></div><div><span>加购转化率</span><b>验证购买阻力降低</b></div><div><span>尺码咨询与退货</span><b>验证适配建议有效性</b></div></section></div><div className="workflow-actions"><button className="primary" onClick={onFinish}>完成本轮优化 <CheckCircle weight="fill"/></button></div></section>;
}
