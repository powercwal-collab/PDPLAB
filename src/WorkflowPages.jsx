import { useEffect, useMemo, useRef, useState } from 'react';
import {
  ArrowRight, Check, CheckCircle, CircleNotch, ClockCounterClockwise, FileImage, ImageSquare,
  LockKey, MagicWand, ShieldCheck, Sparkle, Trash, TrendUp, WarningCircle, X
} from '@phosphor-icons/react';
import './workflow.css';

const maturityClass = maturity => ({ '弱':'weak', '较弱':'relatively-weak', '中':'medium', '较强':'relatively-strong', '强':'strong' }[maturity] || 'medium');
import { api } from './services/api.js';

const reviewModules = [
  { name:'产品KV/封面故事', max:10, coefficient:.5, score:5, maturity:'中' },
  { name:'沉浸式购物/场景化', max:18, coefficient:.5, score:9, maturity:'中' },
  { name:'卖点与功能证明', max:14, coefficient:.5, score:7, maturity:'中' },
  { name:'产品互动/动态内容', max:8, coefficient:0, score:0, maturity:'弱' },
  { name:'细节查阅', max:12, coefficient:1, score:12, maturity:'强' },
  { name:'尺码/适配与对比选购', max:10, coefficient:.5, score:5, maturity:'中' },
  { name:'基础信息', max:8, coefficient:1, score:8, maturity:'强' },
  { name:'使用说明/服务事项', max:5, coefficient:.5, score:2.5, maturity:'中' },
  { name:'关联推荐/延展购买', max:5, coefficient:.5, score:2.5, maturity:'中' },
  { name:'品牌/产品背书', max:5, coefficient:.5, score:2.5, maturity:'中' },
  { name:'页面结构与节奏', max:5, coefficient:1, score:5, maturity:'强' },
];

function mapOverallRating(totalScore, configuredBands) {
  if (configuredBands?.length) {
    return configuredBands.find(band => totalScore < Number(band.lt))?.rating || 7;
  }
  const bands = [[10,1],[20,1.5],[27.5,2],[35,2.5],[42.5,3],[50,3.5],[57.5,4],[65,4.5],[72.5,5],[80,5.5],[85,6],[90,6.5],[101,7]];
  return bands.find(([limit]) => totalScore < limit)?.[1] || 7;
}

function formatConfirmationMode(mode) {
  if (mode === 'ai_auto') return 'AI 自动评分';
  if (mode === 'codex_verified') return 'Codex Skill 校验';
  return '人工修订';
}

function hasVisualEvidence(evidence) {
  if (!evidence?.image_url || evidence.evidence_type === 'missing_content') return false;
  if (evidence.is_crop) return true;
  return Number.isFinite(Number(evidence?.page_index));
}

function HistoryEvidenceThumbnail({ evidence }) {
  const [position, setPosition] = useState('50% 0%');
  const locateEvidence = event => {
    if (evidence?.is_crop) return setPosition('50% 50%');
    const image = event.currentTarget;
    const bbox = evidence?.bbox || {};
    const hasBbox = Number.isFinite(Number(bbox.x)) && Number.isFinite(Number(bbox.y));
    const scale = Math.min(1, 960 / Math.max(image.naturalWidth, 1), 8400 / Math.max(image.naturalHeight, 1));
    const scaledHeight = image.naturalHeight * scale;
    const sliceTop = Math.max(0, Number(evidence?.page_index || 0)) * 1400;
    const sliceHeight = Math.max(1, Math.min(1400, scaledHeight - sliceTop));
    const centerX = hasBbox ? Math.max(0, Math.min(1, Number(bbox.x) + Number(bbox.width || 0) / 2)) : 0.5;
    const withinSliceY = hasBbox ? Number(bbox.y) + Number(bbox.height || 0) / 2 : 0.5;
    const centerY = Math.max(0, Math.min(1, (sliceTop + withinSliceY * sliceHeight) / Math.max(scaledHeight, 1)));
    setPosition(`${centerX * 100}% ${centerY * 100}%`);
  };
  return <img src={evidence.image_url} alt="" onLoad={locateEvidence} style={{objectPosition:position}}/>;
}

export function AnalysisPage({ job, onComplete, onBack }) {
  const [currentJob, setCurrentJob] = useState(job);
  const [pollError, setPollError] = useState('');
  const [failureOpen, setFailureOpen] = useState(false);
  const stages = [
    ['parsing', '文件解析', '读取页面尺寸、格式和版本信息'],
    ['slicing_ocr', '页面切片与 OCR', '识别页面区块与主要文字'],
    ['module_mapping', '11 模块映射', '匹配内容、视觉证据和消费者问题'],
    ['scoring', '评分与优化推演', '生成初评并自动锁定评分版本'],
  ];
  useEffect(() => {
    setCurrentJob(job);
  }, [job]);
  useEffect(() => {
    if (!currentJob?.id || ['completed','failed'].includes(currentJob.status)) return;
    const timer = window.setTimeout(async () => {
      try { const data = await api.diagnosisJob(currentJob.id); setCurrentJob(data.job); setPollError(''); }
      catch (reason) { setPollError(reason.message); }
    }, 650);
    return () => window.clearTimeout(timer);
  }, [currentJob]);
  useEffect(() => {
    if (currentJob?.status === 'failed') setFailureOpen(true);
  }, [currentJob?.status, currentJob?.error_message]);
  const stageIndex = stages.findIndex(([code]) => code === currentJob?.stage);
  const progress = currentJob?.progress || 0;
  const completed = currentJob?.status === 'completed';
  const failed = currentJob?.status === 'failed';
  const retrying = currentJob?.stage === 'retrying' && !failed && !completed;
  return <section className="diagnosis-progress-screen">
    <header className="progress-header"><div className="progress-brand"><span>PDP</span><b>Lab</b></div><button onClick={onBack}>返回首页</button></header>
    <div className="workflow-page analysis-page">
      <div className="analysis-heading">
        <div><div className="workflow-kicker"><CircleNotch className={!completed && !failed ? 'spin' : ''} /> AI 诊断任务 · #{currentJob?.id || '—'}</div><h2>{failed ? '诊断任务未完成' : completed ? 'AI 评分已完成并锁定' : retrying ? '模型服务短暂波动，正在自动重试' : '正在分析这份 PDP'}</h2><p className="workflow-lead">系统按 11 模块评分规则识别信息质量、视觉素材和购买决策证据，完成后自动生成评分版本。</p></div>
        <div className="progress-value"><strong>{Math.round(progress)}%</strong><span>{failed ? '执行失败' : completed ? '评分已锁定' : retrying ? '自动重试中' : '诊断处理中'}</span></div>
      </div>
      <div className="analysis-progress"><span style={{width:`${progress}%`}} /></div>
      <div className="analysis-stages">{stages.map((stage,index) => { const done = completed || index < stageIndex; const active = !failed && !completed && index === stageIndex; return <div className={done ? 'done' : active ? 'active' : ''} key={stage[0]}><i>{done ? <Check /> : index + 1}</i><span><strong>{stage[1]}</strong><small>{stage[2]}</small></span><em>{done ? '完成' : active ? '处理中' : failed && index === Math.max(stageIndex,0) ? '失败' : '等待'}</em></div>; })}</div>
      <div className="workflow-note"><ShieldCheck /><span><b>AI 评分自动锁定</b><small>评分版本会保留模型、规则版本与证据记录；之后仍可人工修订并创建新版本。</small></span></div>
      {(pollError || currentJob?.error_message) && <div className="review-error"><WarningCircle weight="fill"/>{pollError || currentJob.error_message}</div>}
      <div className="workflow-actions"><span className="progress-hint">离开此页不会中断诊断任务</span><button className="primary" disabled={!completed} onClick={() => onComplete(currentJob)}>查看 AI 评分结果 <ArrowRight /></button></div>
    </div>
    {failureOpen && <DiagnosisFailureModal message={currentJob?.error_message || '模型或 PDP Skill 调用失败，未生成评分版本。'} onBack={onBack} onClose={() => setFailureOpen(false)} />}
  </section>;
}

function DiagnosisFailureModal({ message, onBack, onClose }) {
  return <div className="failure-modal-backdrop" role="presentation"><section className="failure-modal" role="alertdialog" aria-modal="true" aria-labelledby="diagnosis-failure-title"><div className="failure-modal-icon"><WarningCircle weight="fill" /></div><div><small>诊断任务执行失败</small><h2 id="diagnosis-failure-title">未成功生成评分</h2><p>{message}</p><span>请确认 AI 模型凭据、PDP Skill 服务和 Celery Worker 均可用。</span></div><div className="failure-modal-actions"><button className="secondary" onClick={onClose}>留在此页</button><button className="primary" onClick={onBack}>返回上传页</button></div></section></div>;
}

export function ScoreReviewPage({ initialModules, starBands, onConfirm }) {
  const [selected, setSelected] = useState(2);
  const [moduleStates, setModuleStates] = useState(() => (initialModules?.length === 11 ? initialModules : reviewModules).map(module => ({...module, checked:false})));
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const current = moduleStates[selected];
  const checkedCount = moduleStates.filter(module => module.checked).length;
  const totalScore = moduleStates.reduce((sum, module) => sum + module.score, 0);
  const overallRating = mapOverallRating(totalScore, starBands);
  const updateCurrent = (change) => setModuleStates(previous => previous.map((module,index) => index === selected ? {...module,...change} : module));
  const setMaturity = (maturity, coefficient) => updateCurrent({ maturity, coefficient, score: Math.round(current.max * coefficient * 100) / 100 });
  const toggleModuleChecked = index => setModuleStates(previous => previous.map((module,itemIndex) => itemIndex === index ? {...module,checked:!module.checked} : module));
  const submit = async () => {
    if (checkedCount !== moduleStates.length) return;
    setSaving(true); setError('');
    try { await onConfirm({ total_score:totalScore, overall_rating:overallRating, modules:moduleStates }); }
    catch (reason) { setError(reason.message || '评分版本保存失败'); }
    finally { setSaving(false); }
  };
  return <div className="review-layout">
    <section className="panel review-list">
      <div className="workflow-panel-head"><div><small>AI 初评 · 待确认</small><h2>检查 11 个模块</h2></div><span>{checkedCount}/11 已检查</span></div>
      <div className="review-batch"><span>总分 {totalScore} · {overallRating} 星</span><button onClick={() => setModuleStates(previous => previous.map(module => ({...module,checked:true})))}>确认全部 AI 初评</button></div>
      <div className="review-rows">{moduleStates.map((module,index)=><button className={selected===index?'selected':''} key={module.name} onClick={()=>setSelected(index)}><i className={module.checked?'checked':''} onClick={event=>{event.stopPropagation();toggleModuleChecked(index)}}>{module.checked&&<Check />}</i><span>{module.name}</span><em className={maturityClass(module.maturity)}>{module.maturity}</em><b>{module.score}/{module.max}</b></button>)}</div>
    </section>
    <section className="panel review-evidence">
      <div className="review-evidence-head"><span>证据核对</span><h2>{current.name}</h2><div><strong>{current.score}</strong><small>/ {current.max} 分</small><em className={maturityClass(current.maturity)}>{current.maturity}</em></div></div>
      <div className="evidence-preview"><img src={current.evidence?.[0]?.image_url || '/projects/nike-kids-learning-shoe.png'} alt="当前 PDP 页面证据"/><span>{current.evidence?.[0] ? `识别区域 · 第 ${current.evidence[0].page_index + 1} 段` : '识别区域 03 · 卖点表达'}</span></div>
      <div className="review-judgment"><small>AI 判断</small><h3>{current.judgment || '有对应内容，但证明方式不足'}</h3><p>{current.evidence?.[0]?.ocr_text || '产品功能有表达，但缺少结构示意、测试数据或场景验证，因此信息与视觉任一维度未达到“强”。'}</p></div>
      <div className="coefficient-picker"><span>确认成熟度</span>{[['弱',0],['较弱',.25],['中',.5],['较强',.75],['强',1]].map(([maturity,coefficient])=><button className={current.coefficient===coefficient?'active':''} key={maturity} onClick={() => setMaturity(maturity,coefficient)}>{maturity} · {coefficient}</button>)}</div>
      <button className="mark-checked" onClick={()=>toggleModuleChecked(selected)}>{current.checked?<CheckCircle weight="fill"/>:<CheckCircle/>}{current.checked?'已检查此模块':'确认此模块证据'}</button>
      {error && <div className="review-error"><WarningCircle weight="fill"/>{error}</div>}
      <div className="workflow-actions review-confirm"><div><LockKey/><span>{checkedCount === 11 ? `将锁定 ${totalScore} 分、${overallRating} 星的评分版本。` : `还需检查 ${11 - checkedCount} 个模块，全部确认后才能锁定。`}</span></div><button className="primary" disabled={checkedCount !== 11 || saving} onClick={submit}>{saving ? '正在保存…' : '确认并锁定评分'} <ArrowRight /></button></div>
    </section>
  </div>;
}

export function DiagnosisHistoryPage({ projectId, projectName, onDeleted, onSelected }) {
  const [records, setRecords] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [deletingId, setDeletingId] = useState(null);
  const [deleteError, setDeleteError] = useState('');
  const [previewEvidence, setPreviewEvidence] = useState(null);
  const evidenceImageContainerRef = useRef(null);
  useEffect(() => {
    if (!projectId) { setRecords([]); setLoading(false); return; }
    setLoading(true); setError('');
    api.diagnoses(projectId).then(data => { setRecords(data.results); setSelectedId(data.results[0]?.id || null); onSelected?.(data.results[0] || null); }).catch(reason => setError(reason.message)).finally(() => setLoading(false));
  }, [projectId]);
  useEffect(() => {
    if (!deleteTarget) return undefined;
    const closeOnEscape = event => {
      if (event.key === 'Escape' && !deletingId) setDeleteTarget(null);
    };
    document.addEventListener('keydown', closeOnEscape);
    return () => document.removeEventListener('keydown', closeOnEscape);
  }, [deleteTarget, deletingId]);
  useEffect(() => {
    if (!previewEvidence) return undefined;
    const closeOnEscape = event => {
      if (event.key === 'Escape') setPreviewEvidence(null);
    };
    document.addEventListener('keydown', closeOnEscape);
    return () => document.removeEventListener('keydown', closeOnEscape);
  }, [previewEvidence]);
  const selected = records.find(record => record.id === selectedId) || records[0];
  const requestDelete = record => {
    setDeleteError('');
    setDeleteTarget(record);
  };
  const selectRecord = record => {
    setSelectedId(record.id);
    onSelected?.(record);
  };
  const confirmDelete = async () => {
    if (!deleteTarget || deletingId) return;
    setDeletingId(deleteTarget.id);
    setDeleteError('');
    try {
      const result = await api.deleteDiagnosis(deleteTarget.id);
      const remaining = records.filter(record => record.id !== deleteTarget.id);
      const nextSelected = selected?.id === deleteTarget.id ? (remaining[0] || null) : selected;
      setRecords(remaining);
      setSelectedId(nextSelected?.id || null);
      setDeleteTarget(null);
      onDeleted?.(result, nextSelected);
    } catch (reason) {
      setDeleteError(reason.message || '评分记录删除失败');
    } finally {
      setDeletingId(null);
    }
  };
  const positionEvidencePreview = event => {
    const container = evidenceImageContainerRef.current;
    if (!container) return;
    if (previewEvidence?.evidence?.is_crop) {
      container.scrollTop = 0;
      return;
    }
    const image = event.currentTarget;
    const evidence = previewEvidence?.evidence || {};
    const bbox = evidence.bbox || {};
    const hasBbox = Number.isFinite(Number(bbox.x)) && Number.isFinite(Number(bbox.y));
    const scale = Math.min(1, 960 / Math.max(image.naturalWidth, 1), 8400 / Math.max(image.naturalHeight, 1));
    const scaledHeight = image.naturalHeight * scale;
    const sliceTop = Math.max(0, Number(evidence.page_index || 0)) * 1400;
    const sliceHeight = Math.max(1, Math.min(1400, scaledHeight - sliceTop));
    const withinSliceY = hasBbox ? Number(bbox.y) + Number(bbox.height || 0) / 2 : 0.5;
    const focusRatio = Math.max(0, Math.min(1, (sliceTop + withinSliceY * sliceHeight) / Math.max(scaledHeight, 1)));
    container.scrollTop = Math.max(0, focusRatio * image.scrollHeight - container.clientHeight * 0.16);
  };
  return <section className="diagnosis-history-page">
    <header><div><small>评价审计记录</small><h2>评分版本</h2><p>{projectName} 的每次锁定评分都会保留模块明细、操作者与时间。</p></div><ClockCounterClockwise size={30}/></header>
    {loading && <div className="history-empty"><CircleNotch className="spin"/>正在读取评分记录…</div>}
    {!loading && error && <div className="history-empty error"><WarningCircle/>{error}</div>}
    {!loading && !error && !records.length && <div className="history-empty"><ClockCounterClockwise size={38}/><h3>暂无锁定评分</h3><p>完成 11 个模块检查并锁定后，评分版本会显示在这里。</p></div>}
    {!loading && selected && <div className="history-layout">
      <aside className="history-record-list" aria-label="评分版本记录">
        {records.map(record => <div className={record.id === selected.id ? 'history-record active' : 'history-record'} key={record.id}>
          <button className="history-record-select" onClick={() => selectRecord(record)} aria-pressed={record.id === selected.id}><span><b>评分版本 v{record.version}</b><small>{new Date(record.created_at).toLocaleString('zh-CN')}</small></span><em>{record.overall_rating} 星 · {formatConfirmationMode(record.confirmation_mode)}</em></button>
          <div className="history-record-meta"><strong>{record.total_score}<small>/100</small></strong><button className="history-delete-button" aria-label={`删除评分版本 v${record.version}`} title={`删除评分版本 v${record.version}`} onClick={() => requestDelete(record)}><Trash size={15}/></button></div>
        </div>)}
      </aside>
      <div className="history-detail">
        <div className="history-summary"><span><small>锁定总分</small><strong>{selected.total_score}</strong></span><span><small>整体星级</small><strong>{selected.overall_rating} 星</strong></span><span><small>评分方式</small><strong>{formatConfirmationMode(selected.confirmation_mode)}</strong></span><span><small>状态</small><strong>已锁定</strong></span></div>
        <div className="history-module-head"><span>模块</span><span>证据切片</span><span>成熟度</span><span>系数</span><span>得分</span></div>
        <div className="history-module-list">{selected.modules.map(module => {
          const evidenceItems = (module.evidence || []).filter(hasVisualEvidence);
          const evidence = evidenceItems[0];
          return <div className="history-module-row" key={module.name}>
            <span>{module.name}</span>
            {evidence ? <button className="history-evidence-thumb" aria-label={`放大查看${module.name}证据切片`} onClick={() => setPreviewEvidence({ module, evidence, count:evidenceItems.length })}><HistoryEvidenceThumbnail evidence={evidence}/>{evidenceItems.length > 1 && <i>+{evidenceItems.length - 1}</i>}</button> : <div className="history-evidence-empty" title="该版本未保存可定位证据"><ImageSquare size={15}/><span>无切片</span></div>}
            <em className={maturityClass(module.maturity)}>{module.maturity}</em><span>{module.coefficient}</span><b>{module.score} / {module.max}</b>
          </div>;
        })}</div>
      </div>
    </div>}
    {deleteTarget && <div className="delete-confirm-backdrop" role="presentation" onMouseDown={event => { if (event.target === event.currentTarget && !deletingId) setDeleteTarget(null); }}><section className="delete-confirm-modal" role="alertdialog" aria-modal="true" aria-labelledby="delete-history-title" aria-describedby="delete-history-description"><div className="delete-confirm-icon"><Trash weight="fill" /></div><div><small>删除评分记录</small><h2 id="delete-history-title">确认删除评分版本 v{deleteTarget.version}？</h2><p id="delete-history-description">删除后将无法恢复该版本及其锁定分值；项目总览会自动切换到剩余的最新评分。</p>{deleteError && <div className="delete-confirm-error"><WarningCircle weight="fill" />{deleteError}</div>}</div><div className="delete-confirm-actions"><button className="secondary" autoFocus disabled={Boolean(deletingId)} onClick={() => setDeleteTarget(null)}>取消</button><button className="danger" disabled={Boolean(deletingId)} onClick={confirmDelete}>{deletingId ? '正在删除…' : '确认删除'}</button></div></section></div>}
    {previewEvidence && <div className="evidence-lightbox-backdrop" role="presentation" onMouseDown={event => { if (event.target === event.currentTarget) setPreviewEvidence(null); }}><section className="evidence-lightbox" role="dialog" aria-modal="true" aria-labelledby="evidence-lightbox-title"><header><div><small>模块证据切片 · 第 {Number(previewEvidence.evidence.page_index || 0) + 1} 段</small><h2 id="evidence-lightbox-title">{previewEvidence.module.name}</h2></div><button aria-label="关闭证据切片预览" onClick={() => setPreviewEvidence(null)}><X size={19}/></button></header><div className="evidence-lightbox-image" ref={evidenceImageContainerRef}><img src={previewEvidence.evidence.source_image_url || previewEvidence.evidence.image_url} alt={`${previewEvidence.module.name}完整页面证据`} onLoad={positionEvidencePreview}/></div><footer><div><small>识别内容</small><p>{previewEvidence.evidence.ocr_text || previewEvidence.evidence.model_reason || '该模块已保存页面视觉证据。'}</p></div>{previewEvidence.count > 1 && <span>该模块共 {previewEvidence.count} 条证据，本次展示第 1 条</span>}</footer></section></div>}
  </section>;
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
    <div className="generation-brief"><div><small>目标层级</small><b>T1 较强</b></div><div><small>预计总分</small><b>79 / 100</b></div><div><small>预计星级</small><b>5.5 星</b></div><div><small>输出模块</small><b>4 个页面段落</b></div></div>
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
  return <section className="rescore-page"><div className="rescore-hero"><div><span>复评结果 · v2</span><h2>页面进入成熟转化增强阶段</h2><p>四个关键模块由“中”提升到“较强”，页面结构达到 T1 较强标准。</p></div><div className="score-shift"><span><small>优化前</small><b>58</b><em>4.5 星</em></span><ArrowRight/><span className="after"><small>优化后</small><b>79</b><em>5.5 星</em></span></div></div><div className="rescore-grid"><section className="panel"><div className="workflow-panel-head"><div><small>模块变化</small><h2>本轮提升明细</h2></div></div>{changes.map(c=><div className="rescore-row" key={c[0]}><span>{c[0]}</span><em className="medium">{c[1]}</em><ArrowRight/><em className="strong">{c[2]}</em><b>{c[3]}</b></div>)}</section><section className="panel expected-value"><div className="workflow-panel-head"><div><small>上线验证</small><h2>建议关注指标</h2></div></div><div><span>首屏继续浏览率</span><b>验证快速决策信息</b></div><div><span>卖点模块停留</span><b>验证证明素材解释力</b></div><div><span>加购转化率</span><b>验证购买阻力降低</b></div><div><span>尺码咨询与退货</span><b>验证适配建议有效性</b></div></section></div><div className="workflow-actions"><button className="primary" onClick={onFinish}>完成本轮优化 <CheckCircle weight="fill"/></button></div></section>;
}
