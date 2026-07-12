import { useMemo, useState } from 'react';
import {
  SquaresFour, ClipboardText, ChartBar, ImageSquare, Sparkle, Gear,
  CaretDown, CaretUp, ArrowRight, CheckCircle, WarningCircle, XCircle,
  UploadSimple, MagnifyingGlass, Bell, DotsThree, TrendUp, FileImage, CaretRight
  , House, Plus, FolderOpen
} from '@phosphor-icons/react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import './styles.css';
import './home-overrides.css';
import { AnalysisPage, ScoreReviewPage, AssetMatchPage, GenerationPage, FinalPage, RescorePage } from './WorkflowPages.jsx';

const modules = [
  { name: '产品KV/封面故事', short: '产品KV', score: 5, max: 10, maturity: '中' },
  { name: '沉浸式购物/场景化', short: '场景化', score: 9, max: 18, maturity: '中' },
  { name: '卖点与功能证明', short: '卖点证明', score: 7, max: 14, maturity: '中' },
  { name: '产品互动/动态内容', short: '动态内容', score: 0, max: 8, maturity: '弱' },
  { name: '细节查阅', short: '细节查阅', score: 12, max: 12, maturity: '强' },
  { name: '尺码/适配与对比选购', short: '尺码适配', score: 5, max: 10, maturity: '中' },
  { name: '基础信息', short: '基础信息', score: 8, max: 8, maturity: '强' },
  { name: '使用说明/服务事项', short: '服务事项', score: 2.5, max: 5, maturity: '中' },
  { name: '关联推荐/延展购买', short: '关联推荐', score: 2.5, max: 5, maturity: '中' },
  { name: '品牌/产品背书', short: '品牌背书', score: 2.5, max: 5, maturity: '中' },
  { name: '页面结构与节奏', short: '结构节奏', score: 5, max: 5, maturity: '强' },
];

const tasks = [
  { id: 'P0-01', priority: 'P0', title: '补齐核心卖点证明', module: '卖点与功能证明', lift: '+7', owner: '内容 × 设计', status: '待开始', detail: '将“缓震、稳定、抓地”从口号改为鞋体结构图、材料测试与用户利益三段式证据。', assets: ['中底剖面图', '材料测试数据', '鞋侧面高清图'] },
  { id: 'P0-02', priority: 'P0', title: '重构前两屏决策信息', module: '页面结构与节奏', lift: '+3', owner: '运营 × 设计', status: '进行中', detail: '前置年龄段、运动等级、适用场景和四个核心安心点。', assets: ['商品主图', '年龄段信息', '场景定义'] },
  { id: 'P1-01', priority: 'P1', title: '场景与利益点绑定', module: '沉浸式购物/场景化', lift: '+9', owner: '摄影 × 设计', status: '待开始', detail: '为内场训练、外场竞赛与学校日常建立场景—动作—产品利益对应关系。', assets: ['运动场景图', '儿童上脚图', '动作抓拍'] },
  { id: 'P1-02', priority: 'P1', title: '补充尺码适配建议', module: '尺码/适配与对比选购', lift: '+5', owner: '商品 × 内容', status: '待开始', detail: '增加宽脚、高脚背和临界码建议，并说明测量方式。', assets: ['尺码表', '测量示意', '用户反馈'] },
];

const nav = [
  { group: '工作台', items: [['首页', House], ['项目总览', SquaresFour], ['评分诊断', ClipboardText], ['优化路线', ChartBar]] },
  { group: '资源中心', items: [['品牌资产', ImageSquare], ['AI 创作', Sparkle]] },
  { group: '系统', items: [['设置', Gear]] },
];

const gapData = [
  { name: '场景化', value: 9, color: '#5E7DF5' },
  { name: '卖点证明', value: 7, color: '#FFAD49' },
  { name: '尺码适配', value: 5, color: '#6CCE98' },
];

function StatusIcon({ maturity }) {
  if (maturity === '强') return <CheckCircle weight="fill" />;
  if (maturity === '弱') return <XCircle weight="fill" />;
  return <WarningCircle weight="fill" />;
}

export function App() {
  const [active, setActive] = useState('首页');
  const [currentProject, setCurrentProject] = useState('Nike Kids｜毛毛虫幼童学步鞋');
  const [projectMenuOpen, setProjectMenuOpen] = useState(false);
  const [generationAssets, setGenerationAssets] = useState(['a1','a2','a3']);
  const [expanded, setExpanded] = useState('P0-01');
  const [query, setQuery] = useState('');
  const [filter, setFilter] = useState('全部');
  const [toast, setToast] = useState('');

  const visibleTasks = useMemo(() => tasks.filter(t =>
    (filter === '全部' || t.priority === filter) &&
    (t.title.includes(query) || t.module.includes(query))
  ), [filter, query]);

  const triggerToast = (message) => {
    setToast(message);
    window.setTimeout(() => setToast(''), 2400);
  };

  const isStandalone = active === '首页' || active === '导入 PDP' || active === '诊断进度';

  return (
    <div className="page-bg">
      <div className={isStandalone ? 'app-shell home-mode' : 'app-shell'}>
        <aside className="sidebar">
          <div className="brand"><span>PDP</span><b>Lab</b></div>
          <div className="side-nav">
            {nav.map(section => (
              <div className="nav-section" key={section.group}>
                <p>{section.group}</p>
                {section.items.map(([label, Icon]) => (
                  <button key={label} className={active === label ? 'nav-item active' : 'nav-item'} onClick={() => setActive(label)}>
                    <Icon size={19} weight={active === label ? 'fill' : 'regular'} />
                    <span>{label}</span>
                  </button>
                ))}
              </div>
            ))}
          </div>
          <div className="user-card">
            <div className="avatar">LX</div>
            <div><strong>品牌策略组</strong><small>管理员</small></div>
            <DotsThree size={21} />
          </div>
        </aside>

        <main className={isStandalone ? 'main home-main' : 'main'}>
          {!isStandalone && <header className="topbar">
            <div>
              <div className="breadcrumb">项目 / {currentProject}</div>
              <h1>{active}</h1>
            </div>
            <div className="top-actions">
              <button className="back-home" onClick={() => setActive('首页')}><House size={18} /> 返回首页</button>
              <div className="project-switcher">
                <button className="switch-project" onClick={() => setProjectMenuOpen(!projectMenuOpen)}><FolderOpen size={18} /><span>切换项目</span><CaretDown size={13} /></button>
                {projectMenuOpen && <div className="project-menu">
                  {['Nike Kids｜毛毛虫幼童学步鞋','Nike Kids｜儿童足球球衣','Nike Running｜城市轻跑鞋'].map(name => <button className={name === currentProject ? 'selected' : ''} key={name} onClick={() => { setCurrentProject(name); setActive('项目总览'); setProjectMenuOpen(false); triggerToast(`已切换至 ${name}`); }}><span>{name}</span>{name === currentProject && <CheckCircle weight="fill" />}</button>)}
                  <button className="menu-new" onClick={() => { setActive('导入 PDP'); setProjectMenuOpen(false); }}><Plus /> 新建诊断项目</button>
                </div>}
              </div>
              <button className="icon-button" aria-label="通知"><Bell size={20} /></button>
              <button className="secondary" onClick={() => setActive('导入 PDP')}><UploadSimple size={18} /> 导入新版本</button>
              <button className="primary" onClick={() => {setActive('优化路线'); triggerToast('已进入 P0 优化路线');}}>查看 P0 优化路线 <ArrowRight size={18} /></button>
            </div>
          </header>}

          {active === '首页' && <HomePage onOpenProject={(name) => { setCurrentProject(name); setActive('项目总览'); }} onImport={() => setActive('导入 PDP')} />}
          {active === '项目总览' && <Dashboard onRoute={() => setActive('优化路线')} />}
          {active === '评分诊断' && <Diagnosis />}
          {active === '优化路线' && (
            <TaskRoute query={query} setQuery={setQuery} filter={filter} setFilter={setFilter} visibleTasks={visibleTasks} expanded={expanded} setExpanded={setExpanded} onGenerate={() => { setActive('品牌资产匹配'); triggerToast('已创建品牌资产匹配任务'); }} />
          )}
          {active === '导入 PDP' && <UploadPage onCancel={() => setActive('首页')} onFinish={() => { setActive('诊断进度'); triggerToast('PDP 已上传，诊断任务已开始'); }} />}
          {active === '诊断进度' && <AnalysisPage onBack={() => setActive('首页')} onReview={() => setActive('评分确认')} />}
          {active === '评分确认' && <ScoreReviewPage onConfirm={() => { setActive('项目总览'); triggerToast('评分版本 v1 已锁定'); }} />}
          {active === '品牌资产匹配' && <AssetMatchPage onGenerate={(ids) => { setGenerationAssets(ids); setActive('AI 生成'); }} />}
          {active === '品牌资产' && <AssetMatchPage onGenerate={(ids) => { setGenerationAssets(ids); setActive('AI 生成'); }} />}
          {active === 'AI 生成' && <GenerationPage assetIds={generationAssets} onComplete={() => setActive('最终优化页面')} />}
          {active === 'AI 创作' && <GenerationPage assetIds={generationAssets} onComplete={() => setActive('最终优化页面')} />}
          {active === '最终优化页面' && <FinalPage onBackTasks={() => setActive('优化路线')} onRescore={() => setActive('复评结果')} />}
          {active === '复评结果' && <RescorePage onFinish={() => { setActive('项目总览'); triggerToast('本轮优化已完成并归档'); }} />}
          {active === '设置' && <FuturePage title={active} onBack={() => setActive('项目总览')} />}
        </main>
      </div>
      {toast && <div className="toast"><CheckCircle weight="fill" />{toast}</div>}
    </div>
  );
}

function Dashboard({ onRoute }) {
  return <div className="dashboard-grid">
    <section className="panel score-panel">
      <div className="panel-head"><div><small>核心结论</small><h2>整体诊断</h2></div><span className="date-pill">评估于 2026.07.10</span></div>
      <div className="score-body">
        <div className="score-number"><strong>58</strong><span>/ 100</span></div>
        <div className="score-copy">
          <div className="score-copy-head"><div><small>整体星级</small><strong>4.5 星</strong></div><span>完整说明增强页</span></div>
          <p>页面信息基本完整，但场景、证明与尺码决策仍存在明显阻力。</p>
          <div className="tier-row"><span>当前 T1-minus</span><ArrowRight /><b>目标 T1 强</b></div>
        </div>
      </div>
      <div className="star-track"><div className="track-line"><span style={{width:'58%'}}></span><i style={{left:'58%'}}>58</i></div><div className="track-labels"><span>3 星<br/><small>基础说明</small></span><span>4 星<br/><small>完整说明</small></span><span className="current">4.5 星<br/><small>当前</small></span><span>5 星<br/><small>成熟转化</small></span><span>6 星<br/><small>专业决策</small></span></div></div>
      <div className="why-row"><WarningCircle weight="fill" /><p><b>为什么还不是 5 星：</b>高权重模块仍停留在“有信息、弱证明”，未形成稳定的购买说服链路。</p></div>
    </section>

    <section className="panel gap-panel">
      <div className="panel-head"><div><small>优先级依据</small><h2>前三大得分缺口</h2></div><button className="text-button" onClick={onRoute}>查看全部 <ArrowRight /></button></div>
      <div className="gap-chart"><ResponsiveContainer width="100%" height="100%"><BarChart data={gapData} layout="vertical" margin={{left: 6,right:20,top:5,bottom:5}}><XAxis type="number" hide domain={[0,10]}/><YAxis dataKey="name" type="category" axisLine={false} tickLine={false} width={74} tick={{fill:'#5f6570',fontSize:13}}/><Tooltip cursor={{fill:'#f5f8fc'}} content={<GapTooltip />}/><Bar dataKey="value" radius={[0,5,5,0]} barSize={22}>{gapData.map(d=><Cell key={d.name} fill={d.color}/>)}</Bar></BarChart></ResponsiveContainer></div>
      <div className="gap-list">{gapData.map((g,i)=><div key={g.name}><b>0{i+1}</b><span>{g.name}<small>{['缺少真实运动场景与利益绑定','卖点仅停留在口号与参数','缺少脚型与临界码建议'][i]}</small></span><strong>可提升 +{g.value}</strong></div>)}</div>
    </section>

    <section className="panel maturity-panel">
      <div className="panel-head"><div><small>11 模块评分</small><h2>模块成熟度分布</h2></div><div className="legend"><span className="strong">强 3</span><span className="medium">中 7</span><span className="weak">弱 1</span></div></div>
      <div className="module-table"><div className="table-head"><span>模块</span><span>成熟度</span><span>得分</span></div>{modules.slice(0,6).map(m=><div className="module-row" key={m.name}><span>{m.name}</span><span className={`maturity ${m.maturity==='强'?'strong':m.maturity==='弱'?'weak':'medium'}`}><StatusIcon maturity={m.maturity}/>{m.maturity}</span><span><b>{m.score}</b> / {m.max}</span></div>)}</div>
    </section>

    <section className="panel action-panel">
      <div className="panel-head"><div><small>下一步行动</small><h2>P0 优化任务</h2></div><span className="count-pill">2 项</span></div>
      <div className="impact-banner"><TrendUp size={25} weight="fill"/><div><span>完成 P0 后预计</span><strong>58 → 68 分</strong></div><em>进入 5 星成熟转化页</em></div>
      <div className="compact-tasks">{tasks.slice(0,2).map(t=><div key={t.id}><span className="priority p0">P0</span><p><strong>{t.title}</strong><small>{t.module} · {t.owner}</small></p><b>{t.lift} 分</b><ArrowRight /></div>)}</div>
      <button className="full-button" onClick={onRoute}>查看完整优化路线 <ArrowRight /></button>
    </section>
  </div>;
}

function GapTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  return <div className="chart-tip"><b>{payload[0].payload.name}</b><span>最高可提升 {payload[0].value} 分</span><small>点击进入证据详情</small></div>;
}

function HomePage({ onOpenProject, onImport }) {
  const projects = [
    { name: 'Nike Kids｜毛毛虫幼童学步鞋', date: '更新于 2026.07.10', score: '4.5 星', image: '/projects/nike-kids-learning-shoe.png' },
    { name: 'Nike Kids｜儿童足球球衣', date: '更新于 2026.07.08', score: '4 星', image: '/projects/brazil-kids-football-jersey.png' },
    { name: 'Nike Running｜城市轻跑鞋', date: '更新于 2026.06.30', score: '待复评', image: '' },
  ];
  return <div className="home-page">
    <section className="home-hero">
      <div className="home-wordmark"><span>PDP</span><b>Lab</b></div>
      <h1>让每个详情页，都有清晰的优化方向</h1>
      <p>选择已有项目继续诊断，或上传新的 PDP 开始评分。</p>
      <button className="home-upload" onClick={onImport}>
        <div><UploadSimple size={24}/><span><b>上传 PDP 内容</b><small>支持长图、截图、PDF 或网页导出文件</small></span></div>
        <span className="upload-action">选择文件 <ArrowRight /></span>
      </button>
      <div className="home-tags"><span>11 模块评分</span><span>弱 / 中 / 强成熟度</span><span>P0 / P1 / P2 优化路线</span><span>品牌资产匹配</span></div>
    </section>
    <section className="recent-projects">
      <div className="recent-head"><div><small>继续工作</small><h2>最近项目</h2></div><button>查看全部 <ArrowRight /></button></div>
      <div className="project-grid">
        <button className="new-project" onClick={onImport}><Plus size={30}/><span>新建诊断项目</span><small>选择项目并上传内容</small></button>
        {projects.map(project=><button className="project-card" key={project.name} onClick={() => onOpenProject(project.name)}>
          <div className="project-cover">{project.image ? <img src={project.image} alt=""/> : <FolderOpen size={38}/>}<span>{project.score}</span></div>
          <strong>{project.name}</strong><small>{project.date}</small>
        </button>)}
      </div>
    </section>
  </div>;
}

function UploadPage({ onCancel, onFinish }) {
  const [project, setProject] = useState('');
  const [fileName, setFileName] = useState('');
  return <section className="upload-page">
    <div className="upload-intro"><span>开始一次诊断</span><h2>选择项目并上传 PDP 内容</h2><p>支持长图、截图、PDF 或网页导出文件。</p></div>
    <div className="upload-steps">
      <div className="upload-step">
        <div className="step-index">01</div>
        <div className="step-main"><small>选择项目</small><h3>这份 PDP 属于哪个项目？</h3>
          <label className="project-select"><select value={project} onChange={e=>setProject(e.target.value)}><option value="">请选择已有项目</option><option>Nike Kids｜毛毛虫幼童学步鞋</option><option>Nike Kids｜儿童篮球鞋系列</option><option>创建新项目</option></select><CaretDown /></label>
        </div>
        {project && <CheckCircle className="step-done" weight="fill" />}
      </div>
      <CaretRight className="step-arrow" />
      <div className={`upload-step ${!project ? 'disabled' : ''}`}>
        <div className="step-index">02</div>
        <div className="step-main"><small>上传内容</small><h3>添加待诊断的 PDP</h3>
          <button className={`drop-zone ${fileName ? 'has-file' : ''}`} disabled={!project} onClick={()=>setFileName('Nike_Kids_PDP_v1.png')}>
            {fileName ? <><CheckCircle size={28} weight="fill"/><span><b>{fileName}</b><small>已准备完成 · 点击重新选择</small></span></> : <><FileImage size={30}/><span><b>点击选择或拖入文件</b><small>PNG、JPG、PDF，最大 30MB</small></span></>}
          </button>
        </div>
      </div>
    </div>
    <div className="upload-footer"><button className="secondary" onClick={onCancel}>取消</button><button className="primary" disabled={!project || !fileName} onClick={onFinish}>开始识别 <ArrowRight /></button></div>
  </section>;
}

function Diagnosis() {
  const [selected, setSelected] = useState(modules[2]);
  return <div className="diagnosis-layout"><section className="panel module-browser"><div className="panel-head"><div><small>评分证据</small><h2>11 模块诊断</h2></div><span className="count-pill">总分 58</span></div><div className="diagnosis-list">{modules.map(m=><button key={m.name} className={selected.name===m.name?'selected':''} onClick={()=>setSelected(m)}><span>{m.name}</span><i className={m.maturity==='强'?'strong':m.maturity==='弱'?'weak':'medium'}>{m.maturity}</i><b>{m.score}/{m.max}</b><ArrowRight /></button>)}</div></section><section className="panel evidence-panel"><div className="evidence-top"><span className="priority p0">重点模块</span><h2>{selected.name}</h2><div className="evidence-score"><strong>{selected.score}</strong><span>/ {selected.max} 分</span><i className={selected.maturity==='强'?'strong':selected.maturity==='弱'?'weak':'medium'}>{selected.maturity}</i></div></div><div className="evidence-block"><small>信息判断</small><h3>有对应内容，但购买问题回答不够具体</h3><p>页面出现功能描述，但没有建立“产品结构—证明方式—用户利益”的完整关系。</p></div><div className="evidence-block"><small>视觉判断</small><h3>素材清晰，但解释力与吸引力不足</h3><p>现有图片以商品展示为主，没有将缓震、稳定和抓地转译为易理解的视觉证据。</p></div><div className="evidence-block warning"><small>提升到“强”需要</small><h3>补齐结构图、测试证据和真实场景</h3><p>预计模块可从 {selected.score} 分提升至 {selected.max} 分。</p></div></section></div>;
}

function TaskRoute({query,setQuery,filter,setFilter,visibleTasks,expanded,setExpanded,onGenerate}) {
  return <div className="route-page"><section className="panel route-hero"><div><span className="eyebrow">从诊断到执行</span><h2>优先完成 2 个 P0，预计进入 5 星</h2><p>系统已按“剩余得分空间 × 商业影响 × 改造可行性”生成优化顺序。</p></div><div className="route-score"><span>当前</span><strong>58</strong><ArrowRight/><span>预计</span><strong>68</strong></div></section><section className="panel task-ledger"><div className="ledger-toolbar"><div className="search"><MagnifyingGlass/><input value={query} onChange={e=>setQuery(e.target.value)} placeholder="搜索任务或模块"/></div><div className="filters">{['全部','P0','P1','P2'].map(f=><button className={filter===f?'active':''} onClick={()=>setFilter(f)} key={f}>{f}</button>)}</div></div><div className="task-head"><span>优先级 / 任务</span><span>对应模块</span><span>预计提升</span><span>负责人</span><span>状态</span><span></span></div>{visibleTasks.map(task=><div className="task-wrap" key={task.id}><button className="task-row" onClick={()=>setExpanded(expanded===task.id?'':task.id)}><span><i className={`priority ${task.priority.toLowerCase()}`}>{task.priority}</i><b>{task.title}</b></span><span>{task.module}</span><strong>{task.lift}</strong><span>{task.owner}</span><span className="task-status">{task.status}</span>{expanded===task.id?<CaretUp/>:<CaretDown/>}</button>{expanded===task.id&&<div className="task-detail"><div><small>执行说明</small><p>{task.detail}</p></div><div><small>所需资产</small><div className="asset-tags">{task.assets.map(a=><span key={a}>{a}</span>)}</div></div><button className="primary" onClick={onGenerate}>匹配品牌资产 <ArrowRight/></button></div>}</div>)}</section></div>;
}

function FuturePage({title,onBack}) { return <section className="panel future-page"><Sparkle size={34} weight="fill"/><span>第二期能力预览</span><h2>{title}将接入诊断任务闭环</h2><p>从评分缺口自动识别所需品牌资产，并生成符合商品真实性、品牌规范和 T1/T0 标准的优化素材。</p><button className="secondary" onClick={onBack}>返回项目总览</button></section>; }
