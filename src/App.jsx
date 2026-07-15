import { useEffect, useMemo, useRef, useState } from 'react';
import {
  SquaresFour, ClipboardText, ChartBar, ImageSquare, Sparkle, Gear,
  CaretDown, CaretUp, ArrowRight, CheckCircle, WarningCircle, XCircle,
  UploadSimple, MagnifyingGlass, DotsThree, TrendUp, FileImage, CaretRight
  , House, Plus, FolderOpen, UserCircle, Bell, SignOut, Question,
  Keyboard, Translate, ShieldCheck, PencilSimple, DeviceMobile, X,
  CircleNotch, ClockCounterClockwise
} from '@phosphor-icons/react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import './styles.css';
import './dashboard-overrides.css';
import './home-overrides.css';
import './responsive.css';
import './user-profile.css';
import { AnalysisPage, ScoreReviewPage, AssetMatchPage, DiagnosisHistoryPage, GenerationPage, FinalPage, RescorePage } from './WorkflowPages.jsx';
import { api } from './services/api.js';

const projectArtwork = {
  'Nike Kids｜毛毛虫幼童学步鞋': { score: '4.5 星', image: '/projects/nike-kids-learning-shoe.png', date: '更新于 2026.07.10' },
  'Nike Kids｜儿童足球球衣': { score: '4 星', image: '/projects/brazil-kids-football-jersey.png', date: '更新于 2026.07.08' },
  'Nike Running｜城市轻跑鞋': { score: '待复评', image: '', date: '更新于 2026.06.30' },
};

const modules = [
  { code:'product_kv', name: '产品KV/封面故事', short: '产品KV', score: 5, max: 10, maturity: '中' },
  { code:'scenario', name: '沉浸式购物/场景化', short: '场景化', score: 9, max: 18, maturity: '中' },
  { code:'selling_point_proof', name: '卖点与功能证明', short: '卖点证明', score: 7, max: 14, maturity: '中' },
  { code:'interactive_content', name: '产品互动/动态内容', short: '动态内容', score: 0, max: 8, maturity: '弱' },
  { code:'detail_review', name: '细节查阅', short: '细节查阅', score: 12, max: 12, maturity: '强' },
  { code:'fit_comparison', name: '尺码/适配与对比选购', short: '尺码适配', score: 5, max: 10, maturity: '中' },
  { code:'basic_information', name: '基础信息', short: '基础信息', score: 8, max: 8, maturity: '强' },
  { code:'service', name: '使用说明/服务事项', short: '服务事项', score: 2.5, max: 5, maturity: '中' },
  { code:'recommendation', name: '关联推荐/延展购买', short: '关联推荐', score: 2.5, max: 5, maturity: '中' },
  { code:'endorsement', name: '品牌/产品背书', short: '品牌背书', score: 2.5, max: 5, maturity: '中' },
  { code:'page_rhythm', name: '页面结构与节奏', short: '结构节奏', score: 5, max: 5, maturity: '强' },
];

const nav = [
  { group: '工作台', items: [['首页', House], ['项目总览', SquaresFour], ['评分诊断', ClipboardText], ['评分记录', ClockCounterClockwise], ['优化路线', ChartBar]] },
  { group: '资源中心', items: [['品牌资产', ImageSquare], ['AI 创作', Sparkle]] },
  { group: '系统', items: [['设置', Gear]] },
];

const gapColors = ['#5E7DF5', '#FFAD49', '#6CCE98'];
const maturityOrder = { '弱': 0, '中': 1, '强': 2 };
const taskBlueprints = {
  product_kv: { title:'重构首屏产品主张', owner:'内容 × 设计', assets:['商品主图','系列定位','核心卖点'] },
  scenario: { title:'强化真实使用场景', owner:'摄影 × 设计', assets:['真实场景图','动作抓拍','用户利益说明'] },
  selling_point_proof: { title:'补齐核心卖点证明', owner:'内容 × 设计', assets:['结构示意','测试数据','材料证明'] },
  interactive_content: { title:'补齐动态讲解内容', owner:'内容 × 交互', assets:['功能视频','3D/AR 素材','试穿动效'] },
  detail_review: { title:'完善产品细节查阅', owner:'摄影 × 设计', assets:['多角度图','结构特写','材质细节'] },
  fit_comparison: { title:'补充尺码适配建议', owner:'商品 × 内容', assets:['尺码表','测量示意','脚型建议'] },
  basic_information: { title:'补齐基础商品信息', owner:'商品 × 内容', assets:['商品参数','材质成分','规格信息'] },
  service: { title:'补充服务与售后说明', owner:'客服 × 内容', assets:['护理说明','退换规则','售后政策'] },
  recommendation: { title:'优化关联推荐逻辑', owner:'运营 × 商品', assets:['系列商品','场景搭配','推荐规则'] },
  endorsement: { title:'补强品牌与产品背书', owner:'品牌 × 内容', assets:['认证奖项','科技来源','用户口碑'] },
  page_rhythm: { title:'重构页面结构与节奏', owner:'运营 × 设计', assets:['页面线框','模块顺序','首屏信息'] },
};

function formatScore(value) {
  const numeric = Number(value || 0);
  return Number.isInteger(numeric) ? String(numeric) : numeric.toFixed(1).replace(/\.0$/, '');
}

function userInitials(user) {
  const source = (user?.nickname || user?.username || '用户').trim();
  if (!source) return '用户';
  const words = source.split(/\s+/).filter(Boolean);
  if (words.length > 1) return words.slice(0, 2).map(word => Array.from(word)[0]).join('').toUpperCase();
  return Array.from(source).slice(0, 2).join('').toUpperCase();
}

function userRoleLabel(user) {
  if (user?.is_superuser) return '超级管理员';
  if (user?.is_staff) return '管理员';
  return '用户';
}

function UserAvatar({ user, className = '', imageUrl = '', as = 'div' }) {
  const Element = as;
  const avatarUrl = imageUrl || user?.avatar_url || '';
  return <Element className={`avatar${className ? ` ${className}` : ''}${avatarUrl ? ' has-image' : ''}`}>
    {avatarUrl ? <img src={avatarUrl} alt={`${user?.nickname || user?.username || '用户'}头像`} /> : userInitials(user)}
  </Element>;
}

function AnimatedScore({ value, duration = 760 }) {
  const numericValue = Number(value || 0);
  const [displayValue, setDisplayValue] = useState(0);

  useEffect(() => {
    const reduceMotion = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
    if (reduceMotion) {
      setDisplayValue(numericValue);
      return undefined;
    }

    let frameId;
    const startedAt = performance.now();
    const tick = (now) => {
      const progress = Math.min(1, (now - startedAt) / duration);
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplayValue(Math.round(numericValue * eased * 10) / 10);
      if (progress < 1) frameId = requestAnimationFrame(tick);
    };
    frameId = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frameId);
  }, [numericValue, duration]);

  return <strong aria-label={`评分 ${formatScore(numericValue)}`}>{formatScore(displayValue)}</strong>;
}

function useDismissiblePopover(open, setOpen, scopeRef) {
  useEffect(() => {
    if (!open) return undefined;
    const closeOnOutside = (event) => {
      if (scopeRef.current && !scopeRef.current.contains(event.target)) setOpen(false);
    };
    const closeOnEscape = (event) => {
      if (event.key === 'Escape') setOpen(false);
    };
    document.addEventListener('pointerdown', closeOnOutside);
    document.addEventListener('keydown', closeOnEscape);
    return () => {
      document.removeEventListener('pointerdown', closeOnOutside);
      document.removeEventListener('keydown', closeOnEscape);
    };
  }, [open, setOpen, scopeRef]);
}

function buildGapItems(moduleList = []) {
  return moduleList.map((module, index) => {
    const max = Number(module.max ?? module.weight ?? 0);
    const score = Number(module.score ?? 0);
    const value = Math.max(0, Math.round((max - score) * 10) / 10);
    const fallback = modules.find(item => item.code === module.code || item.name === module.name) || {};
    const evidenceReason = module.evidence?.[0]?.model_reason;
    const reason = module.judgment || evidenceReason || `${module.name}尚未达到“强”标准`;
    return {
      code: module.code || fallback.code || module.name,
      name: fallback.short || module.short || module.name,
      fullName: module.name,
      maturity: module.maturity,
      max,
      score,
      value,
      reason,
      strongStandard: module.strong_standard || fallback.strong_standard || '',
      originalIndex: index,
    };
  }).filter(item => item.value > 0).sort((a, b) =>
    b.value - a.value ||
    (maturityOrder[a.maturity] ?? 9) - (maturityOrder[b.maturity] ?? 9) ||
    a.originalIndex - b.originalIndex
  ).map((item, index) => ({ ...item, color: gapColors[index % gapColors.length] }));
}

function buildTasksFromGaps(gapItems = []) {
  const counters = { P0: 0, P1: 0, P2: 0 };
  return gapItems.map((gap, index) => {
    const priority = index < 2 ? 'P0' : index < 4 ? 'P1' : 'P2';
    counters[priority] += 1;
    const blueprint = taskBlueprints[gap.code] || { title:`补强${gap.fullName}`, owner:'内容 × 设计', assets:['模块素材','证明信息','版式方案'] };
    const target = gap.strongStandard ? `目标标准：${gap.strongStandard}` : '目标标准：补齐信息与视觉证据并达到“强”成熟度';
    return {
      id: `${priority}-${String(counters[priority]).padStart(2, '0')}`,
      priority,
      title: blueprint.title,
      module: gap.fullName,
      lift: `+${formatScore(gap.value)}`,
      liftValue: gap.value,
      owner: blueprint.owner,
      status: '待开始',
      detail: `${gap.reason}。${target}。`,
      assets: blueprint.assets,
    };
  });
}

function StatusIcon({ maturity }) {
  if (maturity === '强') return <CheckCircle weight="fill" />;
  if (maturity === '弱') return <XCircle weight="fill" />;
  return <WarningCircle weight="fill" />;
}

export function App() {
  const [authenticated, setAuthenticated] = useState(null);
  const [currentUser, setCurrentUser] = useState(null);
  const [projects, setProjects] = useState([]);
  const [active, setActive] = useState('首页');
  const [currentProject, setCurrentProject] = useState('Nike Kids｜毛毛虫幼童学步鞋');
  const [projectMenuOpen, setProjectMenuOpen] = useState(false);
  const projectSwitcherRef = useRef(null);
  const accountMenuScopeRef = useRef(null);
  const [generationAssets, setGenerationAssets] = useState(['a1','a2','a3']);
  const [expanded, setExpanded] = useState('P0-01');
  const [query, setQuery] = useState('');
  const [filter, setFilter] = useState('全部');
  const [toast, setToast] = useState('');
  const [accountMenuOpen, setAccountMenuOpen] = useState(false);
  const [accountTab, setAccountTab] = useState('个人主页');
  const [accountModalOpen, setAccountModalOpen] = useState(false);
  const [latestDiagnosis, setLatestDiagnosis] = useState(null);
  const [diagnosisJob, setDiagnosisJob] = useState(null);
  const [diagnosisConfig, setDiagnosisConfig] = useState(null);
  const [uploadProjectId, setUploadProjectId] = useState(null);
  const unavailableEntries = new Set(['品牌资产', 'AI 创作']);

  useEffect(() => {
    api.me().then(data => { setAuthenticated(true); setCurrentUser(data.user); }).catch(() => setAuthenticated(false));
  }, []);

  useEffect(() => {
    if (!authenticated) return;
    api.projects().then(data => setProjects(data.results)).catch(() => setProjects([]));
    api.diagnosisConfig().then(setDiagnosisConfig).catch(() => setDiagnosisConfig(null));
  }, [authenticated]);

  useEffect(() => {
    if (!authenticated || !['项目总览', '评分诊断', '评分确认', '设置'].includes(active)) return;
    api.diagnosisConfig().then(setDiagnosisConfig).catch(() => setDiagnosisConfig(null));
  }, [authenticated, active]);

  useEffect(() => {
    if (!authenticated || active !== '首页') return;
    api.projects().then(data => setProjects(data.results)).catch(() => {});
  }, [authenticated, active]);

  useDismissiblePopover(projectMenuOpen, setProjectMenuOpen, projectSwitcherRef);
  useDismissiblePopover(accountMenuOpen, setAccountMenuOpen, accountMenuScopeRef);

  const activeRuleModules = useMemo(() => {
    const ruleModules = diagnosisConfig?.scoring_rules?.modules;
    if (!ruleModules?.length) return modules;
    return ruleModules.map(definition => {
      const fallback = modules.find(module => module.code === definition.code) || {};
      const coefficient = fallback.max ? fallback.score / fallback.max : 0;
      return {
        ...fallback,
        code: definition.code,
        name: definition.name,
        short: fallback.short || definition.name,
        max: definition.weight,
        score: Math.round(definition.weight * coefficient * 10) / 10,
        strong_standard: definition.strong_standard,
      };
    });
  }, [diagnosisConfig]);
  const activeStarBands = diagnosisConfig?.scoring_rules?.star_bands;
  const projectModules = useMemo(
    () => latestDiagnosis?.modules?.length ? latestDiagnosis.modules : activeRuleModules,
    [latestDiagnosis, activeRuleModules]
  );
  const projectGapItems = useMemo(() => buildGapItems(projectModules), [projectModules]);
  const projectTasks = useMemo(() => buildTasksFromGaps(projectGapItems), [projectGapItems]);

  const visibleTasks = useMemo(() => projectTasks.filter(t =>
    (filter === '全部' || t.priority === filter) &&
    (t.title.includes(query) || t.module.includes(query))
  ), [projectTasks, filter, query]);
  const currentProjectData = projects.find(project => project.name === currentProject);

  useEffect(() => {
    if (!currentProjectData?.id) { setLatestDiagnosis(null); return; }
    api.diagnoses(currentProjectData.id).then(data => setLatestDiagnosis(data.results[0] || null)).catch(() => setLatestDiagnosis(null));
  }, [currentProjectData?.id]);

  const triggerToast = (message) => {
    setToast(message);
    window.setTimeout(() => setToast(''), 2400);
  };

  const handleAccountNavigate = (target) => {
    if (target === '退出登录') {
      api.logout().catch(() => {});
      setAuthenticated(false);
      setAccountMenuOpen(false);
      return;
    }
    if (target === '管理后台') window.open('/admin/', '_blank', 'noopener,noreferrer');
    else { setAccountTab(target); setAccountModalOpen(true); }
    setAccountMenuOpen(false);
  };

  const isStandalone = active === '首页' || active === '全部项目' || active === '导入 PDP' || active === '诊断进度';

  if (authenticated === null) return <div className="app-loading"><CircleNotch className="spin"/> 正在恢复登录状态…</div>;
  if (!authenticated) return <AuthPage onAuthenticated={(user) => { setCurrentUser(user); setAuthenticated(true); setActive('首页'); }} />;

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
                  <button key={label} disabled={unavailableEntries.has(label)} className={`${active === label ? 'nav-item active' : 'nav-item'}${unavailableEntries.has(label) ? ' unavailable' : ''}`} onClick={() => setActive(label)}>
                    <Icon size={19} weight={active === label ? 'fill' : 'regular'} />
                    <span>{label}</span>{unavailableEntries.has(label) && <small>暂未开放</small>}
                  </button>
                ))}
              </div>
            ))}
          </div>
          <div className="account-menu-anchor" ref={!isStandalone ? accountMenuScopeRef : undefined}>
            <button className="user-card" aria-haspopup="menu" onClick={() => setAccountMenuOpen(open => !open)} aria-expanded={accountMenuOpen}>
              <UserAvatar user={currentUser} />
              <div><strong>{currentUser?.nickname || currentUser?.username || '用户'}</strong><small>{userRoleLabel(currentUser)}</small></div>
              <DotsThree size={21} />
            </button>
            {accountMenuOpen && !isStandalone && <AccountMenu user={currentUser} onNavigate={handleAccountNavigate} />}
          </div>
        </aside>

        {active === '首页' && <div className="home-account-entry" ref={accountMenuScopeRef}>
          <button className="home-account-button" aria-label="用户管理" aria-haspopup="menu" aria-expanded={accountMenuOpen} onClick={() => setAccountMenuOpen(open => !open)}>
            <UserAvatar user={currentUser} className="home-avatar" as="span"/><i aria-hidden="true" />
          </button>
          {accountMenuOpen && <AccountMenu user={currentUser} onNavigate={handleAccountNavigate} />}
        </div>}

        <main className={isStandalone ? 'main home-main' : 'main'}>
          {!isStandalone && <header className="topbar">
            <div>
              <div className="breadcrumb">{active === '账户管理' ? '账号 / 管理中心' : `项目 / ${currentProject}`}</div>
              <h1>{active}</h1>
            </div>
            <div className="top-actions">
              {active === '账户管理' ? <button className="secondary" onClick={() => setActive('项目总览')}><X size={18}/> 关闭</button> : <>
              <button className="back-home" onClick={() => setActive('首页')}><House size={18} /> 返回首页</button>
              <div className="project-switcher" ref={projectSwitcherRef}>
                <button className="switch-project" aria-haspopup="menu" aria-expanded={projectMenuOpen} onClick={() => setProjectMenuOpen(open => !open)}><FolderOpen size={18} /><span>切换项目</span><CaretDown size={13} /></button>
                {projectMenuOpen && <div className="project-menu" role="menu" aria-label="切换项目">
                  <ProjectMenuPanel projects={projects} selectedName={currentProject} onSelect={(project) => { setCurrentProject(project.name); setActive('项目总览'); setProjectMenuOpen(false); triggerToast(`已切换至 ${project.name}`); }} onCreate={() => { setUploadProjectId(null); setActive('导入 PDP'); setProjectMenuOpen(false); }} />
                </div>}
              </div>
              <button className="secondary" onClick={() => { setUploadProjectId(currentProjectData?.id || null); setActive('导入 PDP'); }}><UploadSimple size={18} /> 导入新版本</button>
              <button className="primary" onClick={() => {setActive('优化路线'); triggerToast('已进入 P0 优化路线');}}>查看 P0 优化路线 <ArrowRight size={18} /></button>
              </>}
            </div>
          </header>}

          {active === '首页' && <HomePage projects={projects} onViewAll={() => setActive('全部项目')} onOpenProject={(name) => { setCurrentProject(name); setActive('项目总览'); }} onImport={() => { setUploadProjectId(null); setActive('导入 PDP'); }} />}
          {active === '全部项目' && <AllProjectsPage projects={projects} onBack={() => setActive('首页')} onOpenProject={(name) => { setCurrentProject(name); setActive('项目总览'); }} onCreate={() => { setUploadProjectId(null); setActive('导入 PDP'); }} />}
          {active === '项目总览' && <Dashboard diagnosis={latestDiagnosis} ruleModules={activeRuleModules} starBands={activeStarBands} gapItems={projectGapItems} taskItems={projectTasks} onRoute={() => setActive('优化路线')} />}
          {active === '评分诊断' && <Diagnosis diagnosis={latestDiagnosis} ruleModules={activeRuleModules} onReview={() => setActive('评分确认')} />}
          {active === '评分记录' && <DiagnosisHistoryPage projectId={currentProjectData?.id} projectName={currentProject} onSelected={setLatestDiagnosis} onDeleted={(result, nextSelected) => { setLatestDiagnosis(nextSelected || null); api.projects().then(data => setProjects(data.results)).catch(() => {}); triggerToast(`评分版本 v${result.deleted_version} 已删除`); }} />}
          {active === '优化路线' && (
            <TaskRoute query={query} setQuery={setQuery} filter={filter} setFilter={setFilter} visibleTasks={visibleTasks} tasks={projectTasks} currentScore={latestDiagnosis?.total_score ?? projectModules.reduce((sum,module) => sum + Number(module.score || 0), 0)} starBands={activeStarBands} expanded={expanded} setExpanded={setExpanded} />
          )}
          {active === '导入 PDP' && <UploadPage projects={projects} initialProjectId={uploadProjectId} diagnosisConfig={diagnosisConfig} onProjectCreated={(project) => setProjects(prev => [project, ...prev])} onCancel={() => { setActive(uploadProjectId ? '项目总览' : '首页'); setUploadProjectId(null); }} onFinish={(project, job) => { if (project?.name) setCurrentProject(project.name); setUploadProjectId(null); setDiagnosisJob(job); setActive('诊断进度'); triggerToast('PDP 已上传，AI 诊断任务已创建'); }} />}
          {active === '诊断进度' && <AnalysisPage job={diagnosisJob} onBack={() => setActive('首页')} onComplete={(job) => { setLatestDiagnosis(job.diagnosis || null); setActive('评分记录'); triggerToast(`AI 评分版本 v${job.diagnosis?.version || 1} 已自动锁定`); }} />}
          {active === '评分确认' && <ScoreReviewPage initialModules={latestDiagnosis?.modules || activeRuleModules} starBands={activeStarBands} onConfirm={async (payload) => { if (!currentProjectData?.id) throw new Error('当前项目尚未同步，请返回首页重新选择项目'); const data = await api.saveDiagnosis({ ...payload, project_id:currentProjectData.id }); setLatestDiagnosis(data.diagnosis); setActive('评分记录'); triggerToast(`评分版本 v${data.diagnosis.version} 已锁定`); }} />}
          {active === '品牌资产匹配' && <AssetMatchPage onGenerate={(ids) => { setGenerationAssets(ids); setActive('AI 生成'); }} />}
          {active === '品牌资产' && <AssetMatchPage onGenerate={(ids) => { setGenerationAssets(ids); setActive('AI 生成'); }} />}
          {active === 'AI 生成' && <GenerationPage assetIds={generationAssets} onComplete={() => setActive('最终优化页面')} />}
          {active === 'AI 创作' && <GenerationPage assetIds={generationAssets} onComplete={() => setActive('最终优化页面')} />}
          {active === '最终优化页面' && <FinalPage onBackTasks={() => setActive('优化路线')} onRescore={() => setActive('复评结果')} />}
          {active === '复评结果' && <RescorePage onFinish={() => { setActive('项目总览'); triggerToast('本轮优化已完成并归档'); }} />}
          {active === '设置' && <SettingsPage diagnosisConfig={diagnosisConfig} currentUser={currentUser} onSaved={(message) => triggerToast(message)} />}
          {active === '账户管理' && <AccountManagement currentUser={currentUser} activeTab={accountTab} setActiveTab={setAccountTab} onUserUpdated={setCurrentUser} onSaved={(message='账户信息已保存') => triggerToast(message)} />}
        </main>
      </div>
      {accountModalOpen && <div className="account-modal-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) setAccountModalOpen(false); }}>
        <section className="account-modal" role="dialog" aria-modal="true" aria-labelledby="account-modal-title">
          <header className="account-modal-header"><div><small>账号与偏好设置</small><h2 id="account-modal-title">账户管理</h2></div><button aria-label="关闭账户管理" onClick={() => setAccountModalOpen(false)}><X size={20}/></button></header>
          <AccountManagement currentUser={currentUser} activeTab={accountTab} setActiveTab={setAccountTab} onUserUpdated={setCurrentUser} onSaved={(message='账户信息已保存') => triggerToast(message)} />
        </section>
      </div>}
      {toast && <div className="toast"><CheckCircle weight="fill" />{toast}</div>}
    </div>
  );
}

function AccountMenu({ user, onNavigate }) {
  return <div className="account-popover" role="menu" aria-label="用户管理菜单">
    <div className="account-popover-head"><UserAvatar user={user} className="large"/><div><strong>{user?.nickname || user?.username || '用户'}</strong><small>{user?.email || '未设置邮箱'}</small></div></div>
    <div className="account-menu-group">
      <button role="menuitem" onClick={() => onNavigate('个人主页')}><UserCircle/><span>个人主页</span></button>
      <button role="menuitem" onClick={() => onNavigate('通知')}><Bell/><span>通知</span><CaretRight/></button>
      {user?.is_superuser && <button role="menuitem" onClick={() => onNavigate('管理后台')}><ShieldCheck/><span>管理后台</span><CaretRight/></button>}
    </div>
    <div className="account-menu-group auxiliary">
      <button role="menuitem" onClick={() => onNavigate('使用教程')}><Question/><span>使用教程</span></button>
      <button role="menuitem" onClick={() => onNavigate('快捷键')}><Keyboard/><span>快捷键</span></button>
      <button role="menuitem" onClick={() => onNavigate('简体中文')}><Translate/><span>简体中文</span><CaretRight/></button>
    </div>
    <button role="menuitem" className="sign-out" onClick={() => onNavigate('退出登录')}><SignOut/><span>退出登录</span></button>
  </div>;
}

function AuthPage({ onAuthenticated }) {
  const [mode, setMode] = useState('登录');
  const [form, setForm] = useState({ username: 'powercwal', nickname: '', email: '', password: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const update = (key) => (event) => setForm({ ...form, [key]: event.target.value });
  const submit = async (event) => {
    event.preventDefault(); setError(''); setLoading(true);
    try {
      const data = mode === '登录' ? await api.login(form) : await api.register(form);
      onAuthenticated(data.user);
    } catch (reason) { setError(reason.message); }
    finally { setLoading(false); }
  };
  return <main className="auth-page">
    <section className="auth-brand-panel">
      <div className="auth-brand"><span>PDP</span><b>Lab</b></div>
      <div><small>品牌详情页诊断与优化工作台</small><h1>让每个详情页，<br/>都有清晰的优化方向</h1><p>通过 11 模块评分、人工证据确认和版本记录，把诊断结果转化为可执行的优化任务。</p></div>
      <div className="auth-proof"><span>11</span><p><b>模块诊断</b><small>证据、成熟度与优先级</small></p><span>P0</span><p><b>优化路线</b><small>聚焦最重要的增长动作</small></p></div>
    </section>
    <section className="auth-form-panel">
      <form className="auth-card" onSubmit={submit}>
        <div className="auth-mobile-brand"><span>PDP</span><b>Lab</b></div>
        <small>欢迎使用 PDP Lab</small><h2>{mode === '登录' ? '登录你的工作台' : '创建一个新账号'}</h2><p>{mode === '登录' ? '继续管理项目、诊断任务和品牌资产。' : '注册后即可创建第一个 PDP 诊断项目。'}</p>
        <div className="auth-tabs"><button type="button" className={mode === '登录' ? 'active' : ''} onClick={() => { setMode('登录'); setError(''); }}>登录</button><button type="button" className={mode === '注册' ? 'active' : ''} onClick={() => { setMode('注册'); setError(''); }}>注册</button></div>
        <label><span>账号</span><input value={form.username} onChange={update('username')} placeholder={mode === '登录' ? '请输入用户名或邮箱' : '请输入用户名'} required/></label>
        {mode === '注册' && <><label><span>昵称</span><input value={form.nickname} onChange={update('nickname')} placeholder="团队成员如何称呼你" required/></label><label><span>电子邮箱</span><input type="email" value={form.email} onChange={update('email')} placeholder="name@company.com" required/></label></>}
        <label><span>密码</span><input type="password" value={form.password} onChange={update('password')} placeholder="至少 8 位字符" minLength={8} required/></label>
        {error && <div className="auth-error"><WarningCircle weight="fill"/>{error}</div>}
        <button className="auth-submit" disabled={loading}>{loading ? '处理中…' : mode === '登录' ? '登录 PDP Lab' : '创建账号'}<ArrowRight/></button>
        {mode === '登录' && <div className="auth-hint">本地管理员账号：powercwal</div>}
      </form>
    </section>
  </main>;
}

function AccountManagement({ currentUser, activeTab, setActiveTab, onUserUpdated, onSaved }) {
  const [nickname, setNickname] = useState(currentUser?.nickname || currentUser?.username || '');
  const [email, setEmail] = useState(currentUser?.email || '');
  const [avatarPreview, setAvatarPreview] = useState('');
  const [uploadingAvatar, setUploadingAvatar] = useState(false);
  const [productUpdates, setProductUpdates] = useState(true);
  const [taskUpdates, setTaskUpdates] = useState(true);
  const [weeklyReport, setWeeklyReport] = useState(false);
  const [saving, setSaving] = useState(false);
  const tabs = [['个人主页', UserCircle], ['通知', Bell], ['安全与登录', ShieldCheck]];
  useEffect(() => {
    api.preferences().then(data => { setTaskUpdates(data.task_updates); setProductUpdates(data.product_updates); setWeeklyReport(data.weekly_report); }).catch(() => {});
  }, []);
  useEffect(() => {
    setNickname(currentUser?.nickname || currentUser?.username || '');
    setEmail(currentUser?.email || '');
  }, [currentUser?.username, currentUser?.nickname, currentUser?.email]);
  useEffect(() => () => {
    if (avatarPreview?.startsWith('blob:')) URL.revokeObjectURL(avatarPreview);
  }, [avatarPreview]);
  const changeAvatar = async (event) => {
    const file = event.target.files?.[0];
    event.target.value = '';
    if (!file) return;
    if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) { onSaved('头像仅支持 JPG、PNG 或 WebP'); return; }
    if (file.size > 5 * 1024 * 1024) { onSaved('头像文件不能超过 5MB'); return; }
    const previewUrl = URL.createObjectURL(file);
    setAvatarPreview(previewUrl);
    setUploadingAvatar(true);
    try {
      const user = await api.uploadAvatar(file);
      onUserUpdated?.(user);
      setAvatarPreview('');
      onSaved('头像已更新');
    } catch (reason) {
      setAvatarPreview('');
      onSaved(reason.message);
    } finally {
      setUploadingAvatar(false);
    }
  };
  const saveProfile = async () => {
    setSaving(true);
    try { const user = await api.updateProfile({ nickname, email }); onUserUpdated?.(user); onSaved('账户信息已保存'); }
    catch (reason) { onSaved(reason.message); }
    finally { setSaving(false); }
  };
  const savePreferences = async () => {
    setSaving(true);
    try { await api.updatePreferences({ task_updates: taskUpdates, product_updates: productUpdates, weekly_report: weeklyReport }); onSaved('通知偏好已保存'); }
    catch (reason) { onSaved(reason.message); }
    finally { setSaving(false); }
  };
  return <section className="account-management">
    <aside className="account-tabs"><h2>账户管理</h2>{tabs.map(([label, Icon]) => <button key={label} className={activeTab === label ? 'active' : ''} onClick={() => setActiveTab(label)}><Icon size={20}/>{label}</button>)}</aside>
    <div className="account-content">
      {activeTab === '个人主页' && <>
        <div className="account-section-title"><div><h2>账户信息</h2><p>维护个人资料与团队身份信息。</p></div></div>
        <div className="profile-summary"><UserAvatar user={currentUser} imageUrl={avatarPreview} className="profile"/><div><strong>{nickname}</strong><span>{email}</span><small>{userRoleLabel(currentUser)}</small></div><input id="avatar-file" type="file" accept="image/jpeg,image/png,image/webp" hidden disabled={uploadingAvatar} onChange={changeAvatar}/><label htmlFor="avatar-file" className={`secondary avatar-upload${uploadingAvatar ? ' disabled' : ''}`}>{uploadingAvatar ? '上传中…' : '更换头像'}</label></div>
        <div className="account-form">
          <label><span>昵称</span><div><input value={nickname} onChange={e => setNickname(e.target.value)}/><PencilSimple/></div></label>
          <label><span>电子邮箱</span><div><input type="email" value={email} onChange={e => setEmail(e.target.value)}/><PencilSimple/></div></label>
          <label><span>账号角色</span><div className="readonly-value">{userRoleLabel(currentUser)}</div></label>
        </div>
        <div className="device-section"><div><h3>设备管理</h3><p>查看当前登录设备，异常设备可在 Django 管理后台中停用账号。</p></div><div className="device-row"><DeviceMobile size={22}/><div><strong>桌面端 · macOS · 本地开发环境</strong><small>当前设备 · 最近活动：刚刚</small></div><span>在线</span></div></div>
        <div className="account-actions"><button className="primary" disabled={saving} onClick={saveProfile}>{saving?'保存中…':'保存修改'}</button></div>
      </>}
      {activeTab === '通知' && <>
        <div className="account-section-title"><div><h2>通知设置</h2><p>选择希望接收的诊断任务和系统消息。</p></div></div>
        <div className="notification-inbox"><h3>最近通知</h3><div><CheckCircle weight="fill"/><span><b>评分版本 v1 已生成</b><small>Nike Kids｜毛毛虫幼童学步鞋 · 刚刚</small></span><em>未读</em></div><div><ClipboardText weight="fill"/><span><b>初步诊断等待确认</b><small>请检查 11 个模块的证据与成熟度 · 12 分钟前</small></span></div></div>
        <h3 className="preference-title">通知偏好</h3>
        <NotificationRow title="诊断任务进度" description="上传解析、评分完成和复评结果提醒" checked={taskUpdates} onChange={setTaskUpdates}/>
        <NotificationRow title="产品功能更新" description="PDP Lab 新功能与能力升级通知" checked={productUpdates} onChange={setProductUpdates}/>
        <NotificationRow title="每周项目报告" description="汇总项目评分变化、待办任务和资产使用情况" checked={weeklyReport} onChange={setWeeklyReport}/>
        <div className="account-actions"><button className="primary" disabled={saving} onClick={savePreferences}>{saving?'保存中…':'保存通知偏好'}</button></div>
      </>}
      {activeTab === '安全与登录' && <>
        <div className="account-section-title"><div><h2>安全与登录</h2><p>账号权限与密码由 Django 管理后台统一维护。</p></div></div>
        {currentUser?.is_superuser
          ? <div className="security-card"><ShieldCheck size={30} weight="fill"/><div><strong>{userRoleLabel(currentUser)}账号</strong><p>当前账号已获授权使用运营管理后台。</p></div><a href="/admin/" target="_blank" rel="noreferrer">打开管理后台 <ArrowRight/></a></div>
          : <div className="security-card"><ShieldCheck size={30}/><div><strong>普通用户账号</strong><p>当前账号可使用 PDP Lab 工作台，但无权登录运营管理后台。</p></div><span className="readonly-value">后台不可用</span></div>}
      </>}
      {activeTab === '使用教程' && <InfoPanel icon={Question} title="使用教程" description="按产品流程快速完成一次 PDP 诊断。" items={[['1','新建项目并上传 PDP'],['2','等待诊断并确认 11 个模块'],['3','锁定评分并查看历史版本'],['4','根据 P0/P1 路线执行优化'],['5','资产匹配与 AI 生成暂未开放']]}/>} 
      {activeTab === '快捷键' && <InfoPanel icon={Keyboard} title="快捷键" description="在工作台中更快地完成常用操作。" items={[["⌘ K","打开项目切换"],["⌘ U","导入新版本"],["⌘ /","打开快捷键"],["Esc","关闭弹窗"]]}/>} 
      {activeTab === '简体中文' && <InfoPanel icon={Translate} title="语言设置" description="选择界面显示语言。" items={[["简体中文","当前语言"],["English","即将支持"],["日本語","即将支持"]]}/>} 
    </div>
  </section>;
}

function InfoPanel({ icon: Icon, title, description, items }) {
  return <div className="info-panel"><div className="account-section-title"><div><h2>{title}</h2><p>{description}</p></div><Icon size={28}/></div><div className="info-list">{items.map(item=><div key={item[0]}><strong>{item[0]}</strong><span>{item[1]}</span></div>)}</div></div>;
}

function NotificationRow({ title, description, checked, onChange }) {
  return <div className="notification-row"><div><strong>{title}</strong><p>{description}</p></div><button aria-label={`${title}${checked?'已开启':'已关闭'}`} className={checked ? 'toggle active' : 'toggle'} onClick={() => onChange(!checked)} aria-pressed={checked}><span/></button></div>;
}

function Dashboard({ diagnosis, ruleModules, starBands, gapItems, taskItems, onRoute }) {
  const dashboardModules = diagnosis?.modules?.length ? diagnosis.modules : (ruleModules?.length ? ruleModules : modules);
  const modulePageSize = 6;
  const modulePageCount = Math.max(1, Math.ceil(dashboardModules.length / modulePageSize));
  const [modulePage, setModulePage] = useState(0);
  const moduleSignature = dashboardModules.map(module => `${module.code || module.name}:${module.score}:${module.max}`).join('|');
  useEffect(() => setModulePage(0), [moduleSignature]);
  const safeModulePage = Math.min(modulePage, modulePageCount - 1);
  const visibleModules = dashboardModules.slice(safeModulePage * modulePageSize, (safeModulePage + 1) * modulePageSize);
  const dashboardScore = diagnosis?.total_score ?? dashboardModules.reduce((sum,module) => sum + module.score, 0);
  const dashboardRating = diagnosis?.overall_rating ?? 4.5;
  const ratingPosition = Math.max(0, Math.min(100, ((Number(dashboardRating) - 3) / 4) * 100));
  const currentBand = starBands?.find(band => Number(dashboardScore) < Number(band.lt));
  const nextWholeRating = Math.min(7, Math.floor(Number(dashboardRating)) + 1);
  const dashboardGapItems = gapItems?.length ? gapItems : buildGapItems(dashboardModules);
  const gapData = dashboardGapItems.slice(0, 3);
  const gapMaximum = Math.max(1, ...gapData.map(item => item.value));
  const dashboardTasks = taskItems?.length ? taskItems : buildTasksFromGaps(dashboardGapItems);
  const p0Tasks = dashboardTasks.filter(task => task.priority === 'P0').slice(0, 2);
  const projectedScore = Math.min(100, Math.round((Number(dashboardScore) + p0Tasks.reduce((sum, task) => sum + task.liftValue, 0)) * 10) / 10);
  const projectedBand = starBands?.find(band => projectedScore < Number(band.lt));
  const assessmentDate = diagnosis?.created_at
    ? new Date(diagnosis.created_at).toLocaleDateString('zh-CN').replaceAll('/', '.')
    : '2026.07.10';
  const wholeStarFallback = ['基础说明页','完整说明页','成熟转化页','专业决策页','标杆增长页'];
  const wholeStarBands = [3,4,5,6,7].map((star,index) => ({
    star,
    pageType: starBands?.find(band => Number(band.rating) === star)?.page_type || wholeStarFallback[index],
  }));
  const maturityCounts = dashboardModules.reduce((counts,module) => ({...counts,[module.maturity]:(counts[module.maturity] || 0) + 1}), {});
  const scoreAnimationKey = `${diagnosis?.id || diagnosis?.version_id || moduleSignature}-${dashboardScore}-${dashboardRating}-${assessmentDate}`;
  return <div className="dashboard-grid">
    <section className="panel score-panel" key={scoreAnimationKey}>
      <div className="panel-head"><div><small>核心结论</small><h2>整体诊断</h2></div><span className="date-pill">评估于 {assessmentDate}</span></div>
      <div className="score-body">
        <div className="score-number"><AnimatedScore value={dashboardScore}/><span>/ 100</span></div>
        <div className="score-copy">
          <div className="score-copy-head"><div><small>整体星级</small><strong>{dashboardRating} 星</strong></div><span>{currentBand?.page_type || '完整说明增强页'}</span></div>
          <p>{currentBand?.business_meaning || '页面信息基本完整，但场景、证明与尺码决策仍存在明显阻力。'}</p>
        </div>
      </div>
      <div className="star-track" aria-label={`当前整体星级 ${dashboardRating} 星`}>
        <div className="track-line" style={{'--rating-position': `${ratingPosition}%`}}>
          <span style={{width:`${ratingPosition}%`}}></span>
          <i className={Number(dashboardRating) >= 7 ? 'track-marker edge-right' : 'track-marker'}><b>当前 {dashboardRating} 星</b></i>
        </div>
        <div className="track-labels">{wholeStarBands.map(item => <span key={item.star}><b>{item.star} 星</b><small>{item.pageType}</small></span>)}</div>
      </div>
      <div className="why-row"><WarningCircle weight="fill" /><p><b>为什么还不是 {nextWholeRating} 星：</b>{dashboardGapItems.length ? `仍有 ${dashboardGapItems.length} 个模块未达到“强”，优先补齐 ${dashboardGapItems.slice(0,2).map(module => module.fullName).join('、')}。` : '全部模块已达到“强”，可通过真实转化数据继续验证标杆增长表现。'}</p></div>
    </section>

    <section className="panel gap-panel">
      <div className="panel-head"><div><small>优先级依据</small><h2>{gapData.length >= 3 ? '前三大得分缺口' : gapData.length ? `主要得分缺口 · ${gapData.length} 项` : '暂无得分缺口'}</h2></div><button className="text-button" onClick={onRoute}>查看全部 <ArrowRight /></button></div>
      {gapData.length ? <>
        <div className="gap-chart"><ResponsiveContainer width="100%" height="100%"><BarChart data={gapData} layout="vertical" margin={{left: 6,right:20,top:5,bottom:5}}><XAxis type="number" hide domain={[0,gapMaximum]}/><YAxis dataKey="name" type="category" axisLine={false} tickLine={false} width={74} tick={{fill:'#5f6570',fontSize:13}}/><Tooltip cursor={{fill:'#f5f8fc'}} content={<GapTooltip />}/><Bar dataKey="value" radius={[0,5,5,0]} barSize={22}>{gapData.map(d=><Cell key={d.code} fill={d.color}/>)}</Bar></BarChart></ResponsiveContainer></div>
        <div className="gap-list">{gapData.map((g,i)=><div key={g.code}><b>0{i+1}</b><span>{g.name}<small title={g.reason}>{g.reason}</small></span><strong>可提升 +{formatScore(g.value)}</strong></div>)}</div>
      </> : <div className="gap-empty"><CheckCircle weight="fill"/><strong>11 个模块均已达到“强”</strong><span>当前没有可计算的模块得分缺口。</span></div>}
    </section>

    <section className="panel maturity-panel">
      <div className="panel-head"><div><small>11 模块评分</small><h2>模块成熟度分布</h2></div><div className="legend"><span className="strong">强 {maturityCounts['强'] || 0}</span><span className="medium">中 {maturityCounts['中'] || 0}</span><span className="weak">弱 {maturityCounts['弱'] || 0}</span></div></div>
      <div className="module-carousel" aria-label="模块成熟度分页" aria-roledescription="轮播">
        <div className="module-table module-page" key={safeModulePage}><div className="table-head"><span>模块</span><span>成熟度</span><span>得分</span></div>{visibleModules.map(m=><div className="module-row" key={m.name}><span>{m.name}</span><span className={`maturity ${m.maturity==='强'?'strong':m.maturity==='弱'?'weak':'medium'}`}><StatusIcon maturity={m.maturity}/>{m.maturity}</span><span><b>{m.score}</b> / {m.max}</span></div>)}</div>
        {modulePageCount > 1 && <div className="module-pagination" role="group" aria-label="模块列表分页">{Array.from({ length: modulePageCount }, (_, index) => <button key={index} type="button" className={index === safeModulePage ? 'active' : ''} aria-label={`查看第 ${index + 1} 页模块`} aria-current={index === safeModulePage ? 'page' : undefined} onClick={() => setModulePage(index)} />)}</div>}
      </div>
    </section>

    <section className="panel action-panel">
      <div className="panel-head"><div><small>下一步行动</small><h2>P0 优化任务</h2></div><span className="count-pill">{p0Tasks.length} 项</span></div>
      <div className="impact-banner"><TrendUp size={25} weight="fill"/><div><span>完成 P0 后预计</span><strong>{formatScore(dashboardScore)} → {formatScore(projectedScore)} 分</strong></div><em>预计进入 {projectedBand?.rating || dashboardRating} 星 · {projectedBand?.page_type || currentBand?.page_type || '当前阶段'}</em></div>
      <div className="compact-tasks">{p0Tasks.length ? p0Tasks.map(t=><div key={t.id}><span className="priority p0">P0</span><p><strong>{t.title}</strong><small>{t.module} · {t.owner}</small></p><b>{t.lift} 分</b><ArrowRight /></div>) : <div className="compact-empty"><CheckCircle weight="fill"/>暂无 P0 得分补强任务</div>}</div>
      <button className="full-button" onClick={onRoute}>查看完整优化路线 <ArrowRight /></button>
    </section>
  </div>;
}

function GapTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  return <div className="chart-tip"><b>{payload[0].payload.name}</b><span>最高可提升 {formatScore(payload[0].value)} 分</span><small>{payload[0].payload.reason}</small></div>;
}

function normalizeProject(project) {
  const artwork = projectArtwork[project.name] || {};
  const updatedDate = project.updated_at ? `更新于 ${new Date(project.updated_at).toLocaleDateString('zh-CN').replaceAll('/', '.')}` : '';
  const isPersistedProject = Boolean(project.id);
  return {
    ...project,
    date: updatedDate || artwork.date || '刚刚创建',
    score: project.score_label || (!isPersistedProject ? artwork.score : '') || '待诊断',
    image: project.cover_url || (!isPersistedProject ? artwork.image : '') || '',
  };
}

function HomePage({ projects, onViewAll, onOpenProject, onImport }) {
  const visibleProjects = projects.slice(0, 3).map(normalizeProject);
  return <div className="home-page">
    <section className="home-hero">
      <div className="home-wordmark"><span>PDP</span><b>Lab</b></div>
      <h1>让每个详情页，都有清晰的优化方向</h1>
      <p>选择已有项目继续诊断，或上传新的 PDP 开始评分。</p>
      <button className="home-upload" onClick={onImport}>
        <div><UploadSimple size={24}/><span><b>上传 PDP 内容</b><small>支持长图、截图、PDF 或网页导出文件</small></span></div>
        <span className="upload-action">选择文件 <ArrowRight /></span>
      </button>
      <div className="home-tags"><span>11 模块评分</span><span>弱 / 中 / 强成熟度</span><span>评分版本可追溯</span><span className="unavailable">品牌资产匹配 · 暂未开放</span></div>
    </section>
    <section className="recent-projects">
      <div className="recent-head"><div><small>继续工作</small><h2>最近项目</h2></div><button onClick={onViewAll}>查看全部 <ArrowRight /></button></div>
      <div className="project-grid">
        <button className="new-project" onClick={onImport}><Plus size={30}/><span>新建诊断项目</span><small>选择项目并上传内容</small></button>
        {visibleProjects.map(project=><button className="project-card" key={project.id || project.name} onClick={() => onOpenProject(project.name)}>
          <div className="project-cover">{project.image ? <img src={project.image} alt=""/> : <FolderOpen size={38}/>}<span>{project.score}</span></div>
          <strong>{project.name}</strong><small>{project.date}</small>
        </button>)}
      </div>
    </section>
  </div>;
}

function AllProjectsPage({ projects, onBack, onOpenProject, onCreate }) {
  const [keyword, setKeyword] = useState('');
  const filtered = projects.map(normalizeProject).filter(project => project.name.toLowerCase().includes(keyword.toLowerCase()) || project.brand?.toLowerCase().includes(keyword.toLowerCase()));
  return <section className="all-projects-page">
    <header><button onClick={onBack}><House/> 返回首页</button><div><small>项目中心</small><h1>全部项目</h1><p>搜索并继续已有诊断，或创建一个新项目。</p></div><button className="primary" onClick={onCreate}><Plus/> 新建项目</button></header>
    <div className="all-projects-toolbar"><label><MagnifyingGlass/><input value={keyword} onChange={event => setKeyword(event.target.value)} placeholder="搜索项目或品牌"/></label><span>共 {filtered.length} 个项目</span></div>
    {filtered.length ? <div className="all-projects-grid">{filtered.map(project => <button key={project.id || project.name} onClick={() => onOpenProject(project.name)}><div className="project-cover">{project.image ? <img src={project.image} alt=""/> : <FolderOpen size={42}/>}<span>{project.score}</span></div><strong>{project.name}</strong><small>{project.brand || '未设置品牌'} · {project.category || '未设置品类'}</small><em>{project.date}</em></button>)}</div> : <div className="empty-projects"><FolderOpen size={44}/><h2>没有匹配的项目</h2><p>调整搜索条件，或创建一个新的诊断项目。</p><button className="primary" onClick={onCreate}>新建项目</button></div>}
  </section>;
}

function UploadPage({ projects, initialProjectId, diagnosisConfig, onProjectCreated, onCancel, onFinish }) {
  const [projectId, setProjectId] = useState(initialProjectId ? String(initialProjectId) : '');
  const [projectPickerOpen, setProjectPickerOpen] = useState(false);
  const [pendingProjectChange, setPendingProjectChange] = useState(null);
  const [newProject, setNewProject] = useState({ name: '', brand: '', category: '' });
  const [file, setFile] = useState(null);
  const [error, setError] = useState('');
  const [uploading, setUploading] = useState(false);
  const [failure, setFailure] = useState(null);
  const projectPickerRef = useRef(null);
  const selectedProject = projects.find(project => String(project.id) === String(projectId));
  const hasProjectContext = Boolean(initialProjectId);
  const projectPreselected = Boolean(selectedProject && String(initialProjectId) === String(projectId));
  useDismissiblePopover(projectPickerOpen, setProjectPickerOpen, projectPickerRef);
  const applyProjectSelection = project => {
    setProjectId(String(project.id));
    setError('');
    setProjectPickerOpen(false);
  };
  const requestProjectSelection = project => {
    if (String(project.id) === String(projectId)) {
      setProjectPickerOpen(false);
      return;
    }
    if (initialProjectId) {
      setPendingProjectChange({ type:'select', project });
      setProjectPickerOpen(false);
      return;
    }
    applyProjectSelection(project);
  };
  const requestProjectCreation = () => {
    if (initialProjectId) {
      setPendingProjectChange({ type:'create' });
      setProjectPickerOpen(false);
      return;
    }
    setProjectId('__new__');
    setError('');
    setProjectPickerOpen(false);
  };
  const confirmProjectChange = () => {
    if (pendingProjectChange?.type === 'select') applyProjectSelection(pendingProjectChange.project);
    if (pendingProjectChange?.type === 'create') {
      setProjectId('__new__');
      setError('');
    }
    setPendingProjectChange(null);
  };
  const validateFile = candidate => {
    if (!candidate) return;
    const allowed = ['image/png', 'image/jpeg', 'application/pdf'];
    if (!allowed.includes(candidate.type)) return setError('仅支持 PNG、JPG 或 PDF 文件');
    if (candidate.size > 30 * 1024 * 1024) return setError('文件不能超过 30MB');
    setError(''); setFile(candidate);
  };
  const createProject = async () => {
    setError('');
    try {
      const data = await api.createProject(newProject);
      onProjectCreated(data.project);
      setProjectId(String(data.project.id));
    } catch (reason) {
      const message = reason.message || '项目创建失败';
      setError(message);
      setFailure({
        title:'项目创建失败',
        message,
        hint:'请确认登录状态后刷新页面重试；项目创建不依赖 AI 模型或 PDP Skill。',
      });
    }
  };
  const submitUpload = async () => {
    if (!projectId || !file) return;
    if (diagnosisConfig?.active_adapter === 'mock') {
      const message = '当前模型适配器为 Mock，不会读取或理解本次上传内容。系统已停止创建评分，避免产生错误或不实际的信息。';
      setError(message);
      setFailure({ title:'Mock 模式不可生成正式评分', message, hint:'请先在管理后台配置并验证真实模型 API；Mock 仅保留给开发回归测试。' });
      return;
    }
    setUploading(true); setError('');
    try {
      const sourceData = await api.uploadSource(projectId, file);
      const jobData = await api.createDiagnosisJob(sourceData.source.id, { visual_tier:'T1', business_goal:'提升购买决策效率' });
      onFinish(projects.find(project => String(project.id) === String(projectId)), jobData.job);
    }
    catch (reason) {
      const message = reason.message || '诊断任务未能启动';
      setError(message);
      setFailure({ title:'诊断任务未成功', message });
    }
    finally { setUploading(false); }
  };
  return <section className="upload-page">
    <div className="upload-intro"><span>{hasProjectContext ? '导入项目新版本' : '开始一次诊断'}</span><h2>{hasProjectContext ? (selectedProject ? `为「${selectedProject.name}」上传新版本` : '创建新项目并上传 PDP 内容') : '选择项目并上传 PDP 内容'}</h2><p>{projectPreselected ? '系统已优先识别当前项目；如归属有误，可在下方切换。' : '支持长图、截图、PDF 或网页导出文件。'}</p></div>
    <div className="upload-steps">
      <div className="upload-step">
        <div className="step-main"><div className="step-label"><span className="step-index">01</span><small>{projectPreselected ? '优先识别项目' : hasProjectContext ? '已选择项目' : '选择项目'}</small></div><h3>{projectPreselected ? '已为你选择最可能归属的项目，可点击切换' : hasProjectContext ? '新版本将归入你选择的项目' : '这份 PDP 属于哪个项目？'}</h3>
          <div className="upload-project-picker" ref={projectPickerRef}>
            <button type="button" className={`project-select${projectPreselected ? ' suggested-project' : ''}`} aria-haspopup="menu" aria-expanded={projectPickerOpen} onClick={() => setProjectPickerOpen(open => !open)}><span>{projectId === '__new__' ? '创建新项目' : selectedProject?.name || '请选择已有项目'}</span>{projectPickerOpen ? <CaretUp /> : <CaretDown />}</button>
            {projectPickerOpen && <div className="project-menu upload-project-menu" role="menu" aria-label="选择项目"><ProjectMenuPanel projects={projects} selectedId={projectId} onSelect={requestProjectSelection} onCreate={requestProjectCreation} /></div>}
          </div>
          {projectId === '__new__' && <div className="new-project-form"><input value={newProject.name} onChange={e=>setNewProject({...newProject,name:e.target.value})} placeholder="项目名称"/><input value={newProject.brand} onChange={e=>setNewProject({...newProject,brand:e.target.value})} placeholder="品牌"/><input value={newProject.category} onChange={e=>setNewProject({...newProject,category:e.target.value})} placeholder="品类"/><button className="secondary" disabled={!newProject.name.trim()} onClick={createProject}>创建并选择</button></div>}
        </div>
        {projectId && projectId !== '__new__' && <CheckCircle className="step-done" weight="fill" />}
      </div>
      <CaretRight className="step-arrow" />
      <div className={`upload-step ${!projectId || projectId === '__new__' ? 'disabled' : ''}`}>
        <div className="step-main"><div className="step-label"><span className="step-index">02</span><small>上传内容</small></div><h3>添加待诊断的 PDP</h3>
          <input id="pdp-upload-input" type="file" hidden accept=".png,.jpg,.jpeg,.pdf" disabled={!projectId || projectId === '__new__'} onChange={event => validateFile(event.target.files?.[0])}/>
          <label htmlFor="pdp-upload-input" className={`drop-zone ${file ? 'has-file' : ''}`} onDragOver={event=>event.preventDefault()} onDrop={event=>{event.preventDefault();validateFile(event.dataTransfer.files?.[0])}}>
            {file ? <><CheckCircle size={28} weight="fill"/><span><b>{file.name}</b><small>{(file.size/1024/1024).toFixed(2)}MB · 点击重新选择</small></span></> : <><FileImage size={30}/><span><b>点击选择或拖入文件</b><small>PNG、JPG、PDF，最大 30MB</small></span></>}
          </label>
        </div>
      </div>
    </div>
    {error && <div className="upload-error"><WarningCircle weight="fill"/>{error}</div>}
    <div className="upload-footer"><button className="secondary" onClick={onCancel}>取消</button><button className="primary" disabled={!projectId || projectId === '__new__' || !file || uploading} onClick={submitUpload}>{uploading ? '上传中…' : '开始识别'} <ArrowRight /></button></div>
    {pendingProjectChange && <div className="delete-confirm-backdrop" role="presentation" onMouseDown={event => { if (event.target === event.currentTarget) setPendingProjectChange(null); }}><section className="delete-confirm-modal project-change-confirm" role="alertdialog" aria-modal="true" aria-labelledby="project-change-title" aria-describedby="project-change-description"><div className="delete-confirm-icon"><WarningCircle weight="fill" /></div><div><small>确认项目归属</small><h2 id="project-change-title">新版本将归入另一个项目</h2><p id="project-change-description">{pendingProjectChange.type === 'select' ? `确认后，本次上传将从「${selectedProject?.name}」切换到「${pendingProjectChange.project.name}」。` : `确认后将创建新项目，本次上传不会归入「${selectedProject?.name}」。`}</p></div><div className="delete-confirm-actions"><button className="secondary" autoFocus onClick={() => setPendingProjectChange(null)}>取消</button><button className="primary" onClick={confirmProjectChange}>确认更改</button></div></section></div>}
    {failure && <FailureModal title={failure.title} message={failure.message} hint={failure.hint} onClose={() => setFailure(null)} />}
  </section>;
}

function ProjectMenuPanel({ projects, selectedId, selectedName, onSelect, onCreate }) {
  return <>
    <div className="project-menu-list">
      {projects.length ? projects.map(project => {
        const selected = selectedId !== undefined && selectedId !== ''
          ? String(project.id) === String(selectedId)
          : project.name === selectedName;
        return <button type="button" role="menuitem" className={selected ? 'selected' : ''} key={project.id || project.name} title={project.name} onClick={() => onSelect(project)}><span>{project.name}</span>{selected && <CheckCircle weight="fill" />}</button>;
      }) : <div className="project-menu-empty">暂无可选择项目</div>}
    </div>
    <button type="button" className="menu-new" onClick={onCreate}><Plus /> 新建诊断项目</button>
  </>;
}

function FailureModal({ title, message, hint, onClose }) {
  return <div className="failure-modal-backdrop" role="presentation" onMouseDown={event => { if (event.target === event.currentTarget) onClose(); }}><section className="failure-modal" role="alertdialog" aria-modal="true" aria-labelledby="failure-modal-title"><div className="failure-modal-icon"><WarningCircle weight="fill" /></div><div><small>本次操作未完成</small><h2 id="failure-modal-title">{title}</h2><p>{message}</p><span>{hint || '请检查 AI 模型 API Key、PDP Skill 接入地址与 Worker 状态后重试。'}</span></div><button className="primary" onClick={onClose}>我知道了</button></section></div>;
}

function Diagnosis({ diagnosis, ruleModules, onReview }) {
  const rawDiagnosisModules = diagnosis?.modules?.length ? diagnosis.modules : (ruleModules?.length ? ruleModules : modules);
  const diagnosisModules = rawDiagnosisModules.map(module => {
    const definition = ruleModules?.find(item => item.code === module.code || item.name === module.name) || {};
    return { ...definition, ...module, max: module.max ?? module.weight ?? definition.max ?? definition.weight ?? 0 };
  });
  const [selectedName, setSelectedName] = useState(diagnosisModules[2].name);
  const selected = diagnosisModules.find(module => module.name === selectedName) || diagnosisModules[0];
  const totalScore = diagnosis?.total_score ?? diagnosisModules.reduce((sum,module) => sum + module.score, 0);
  const primaryEvidence = selected.evidence?.[0];
  const evidenceCount = selected.evidence?.length || 0;
  const maturityLogic = selected.maturity === '强'
    ? '页面信息与视觉素材均能支持该模块的购买决策。'
    : selected.maturity === '弱'
      ? '页面未形成可识别的对应模块，消费者无法获得这类决策信息。'
      : '页面已有对应内容，但信息或视觉素材至少一项仍未达到强标准。';
  const judgmentTitle = selected.judgment || `${selected.name}当前成熟度为“${selected.maturity}”`;
  const evidenceTitle = primaryEvidence?.model_reason || (evidenceCount ? '已定位对应页面证据' : '当前版本未保存可定位证据');
  const evidenceCopy = primaryEvidence?.ocr_text?.trim() || (evidenceCount ? '该证据未识别到可展示文字，请在复核页面结合原图区域查看。' : '请重新运行 AI 诊断或进入人工复核，为该模块补充页面证据。');
  const isStrong = selected.maturity === '强';
  const improvementTitle = isStrong ? `保持${selected.name}的强项表现` : selected.maturity === '弱' ? `先建立完整的${selected.name}模块` : `强化${selected.name}的信息与视觉证据`;
  const improvementCopy = `${selected.strong_standard || '围绕消费者购买问题补齐信息、证据与视觉表达。'}${isStrong ? ' 建议结合上线后的真实转化数据持续验证。' : ` 预计模块可从 ${selected.score} 分提升至 ${selected.max} 分。`}`;
  return <div className="diagnosis-layout"><section className="panel module-browser"><div className="panel-head"><div><small>评分证据</small><h2>11 模块诊断</h2></div><span className="count-pill">总分 {totalScore}</span></div><div className="diagnosis-list">{diagnosisModules.map(m=><button key={m.name} className={selected.name===m.name?'selected':''} onClick={()=>setSelectedName(m.name)}><span>{m.name}</span><i className={m.maturity==='强'?'strong':m.maturity==='弱'?'weak':'medium'}>{m.maturity}</i><b>{m.score}/{m.max}</b><ArrowRight /></button>)}</div></section><section className="panel evidence-panel"><div className="evidence-top"><div><span className="priority p0">重点模块</span><h2>{selected.name}</h2></div><button className="primary" onClick={onReview}>复核并创建新评分版本 <ArrowRight/></button><div className="evidence-score"><strong>{selected.score}</strong><span>/ {selected.max} 分</span><i className={selected.maturity==='强'?'strong':selected.maturity==='弱'?'weak':'medium'}>{selected.maturity}</i></div></div><div className="evidence-block"><small>模块判断</small><h3>{judgmentTitle}</h3><p>{maturityLogic}</p></div><div className="evidence-block"><small>页面证据 · {evidenceCount} 条</small><h3>{evidenceTitle}</h3><p>{evidenceCopy}</p></div><div className={isStrong ? 'evidence-block success' : 'evidence-block warning'}><small>{isStrong ? '保持“强”需要' : '提升到“强”需要'}</small><h3>{improvementTitle}</h3><p>{improvementCopy}</p></div></section></div>;
}

function TaskRoute({query,setQuery,filter,setFilter,visibleTasks,tasks,currentScore,starBands,expanded,setExpanded}) {
  const p0Tasks = tasks.filter(task => task.priority === 'P0');
  const projectedScore = Math.min(100, Math.round((Number(currentScore) + p0Tasks.reduce((sum,task) => sum + task.liftValue, 0)) * 10) / 10);
  const projectedBand = starBands?.find(band => projectedScore < Number(band.lt));
  return <div className="route-page"><section className="panel route-hero"><div><span className="eyebrow">从诊断到执行</span><h2>{p0Tasks.length ? `优先完成 ${p0Tasks.length} 个 P0，预计进入 ${projectedBand?.rating || '下一'} 星` : '当前没有 P0 得分补强任务'}</h2><p>系统已按模块剩余得分空间、成熟度与评分规则生成优化顺序。</p></div><div className="route-score"><span>当前</span><strong>{formatScore(currentScore)}</strong><ArrowRight/><span>预计</span><strong>{formatScore(projectedScore)}</strong></div></section><section className="panel task-ledger"><div className="ledger-toolbar"><div className="search"><MagnifyingGlass/><input value={query} onChange={e=>setQuery(e.target.value)} placeholder="搜索任务或模块"/></div><div className="filters">{['全部','P0','P1','P2'].map(f=><button className={filter===f?'active':''} onClick={()=>setFilter(f)} key={f}>{f}</button>)}</div></div><div className="task-head"><span>优先级 / 任务</span><span>对应模块</span><span>预计提升</span><span>负责人</span><span>状态</span><span></span></div>{visibleTasks.length ? visibleTasks.map(task=><div className="task-wrap" key={task.id}><button className="task-row" onClick={()=>setExpanded(expanded===task.id?'':task.id)}><span><i className={`priority ${task.priority.toLowerCase()}`}>{task.priority}</i><b>{task.title}</b></span><span>{task.module}</span><strong>{task.lift}</strong><span>{task.owner}</span><span className="task-status">{task.status}</span>{expanded===task.id?<CaretUp/>:<CaretDown/>}</button>{expanded===task.id&&<div className="task-detail"><div><small>执行说明</small><p>{task.detail}</p></div><div><small>所需资产</small><div className="asset-tags">{task.assets.map(a=><span key={a}>{a}</span>)}</div></div><button className="primary unavailable-action" disabled>品牌资产匹配 · 暂未开放</button></div>}</div>) : <div className="task-empty">当前筛选条件下没有优化任务。</div>}</section></div>;
}

function SettingsPage({ onSaved, diagnosisConfig, currentUser }) {
  const [tab, setTab] = useState('诊断规则');
  const [settings, setSettings] = useState({ target:'T1 强', autoMatch:false, requireReview:true, weeklyDigest:false });
  const tabs=['诊断规则','品牌资产','集成服务','团队权限'];
  const ruleRevision = diagnosisConfig?.source_revision?.replace('sha256:', '').slice(0, 8);
  const ruleModules = diagnosisConfig?.scoring_rules?.modules || [];
  return <section className="settings-page">
    <aside><h2>系统设置</h2>{tabs.map(item=><button key={item} className={tab===item?'active':''} onClick={()=>setTab(item)}>{item}<CaretRight/></button>)}</aside>
    <div className="settings-content">
      {tab==='诊断规则'&&<><div className="settings-head"><div><h2>诊断规则</h2><p>前端评分展示与后端当前启用的 PDP Skill 规则保持一致。</p></div><strong className="config-status ready">已同步</strong></div><div className="rule-source-card"><div><small>规则来源</small><b>{diagnosisConfig?.source_skill || 'pdp-detail-page-methodology'}</b><span>{diagnosisConfig?.source_mode === 'remote_http' ? '远程 Skill' : '内置版本化规则'} · {diagnosisConfig?.scoring_standard_version || 'pdp-v1'}{ruleRevision ? ` · ${ruleRevision}` : ''}</span></div><em>{ruleModules.length || 11} 模块 · 100 分</em></div><div className="rule-module-list">{ruleModules.map(module=><div key={module.code}><span>{module.name}</span><b>{module.weight} 分</b><small>{module.strong_standard}</small></div>)}</div><SettingSelect label="默认目标层级" value={settings.target} onChange={value=>setSettings({...settings,target:value})} options={['T1 强','T1-minus','T0 专业决策']}/><div className="setting-row"><div><b>AI 评分确认方式</b><span>11 模块与证据通过后自动锁定，人工可另建修订版本</span></div><strong className="config-status ready">自动锁定</strong></div><SettingToggle label="自动匹配品牌资产" description="暂未开放：后续接入品牌资产服务后启用" checked={settings.autoMatch} disabled onChange={value=>setSettings({...settings,autoMatch:value})}/><SettingToggle label="生成结果必须人工审核" description="保留为后续 AI 生成能力的审核规则" checked={settings.requireReview} disabled onChange={value=>setSettings({...settings,requireReview:value})}/></>}
      {tab==='品牌资产'&&<><div className="settings-head"><div><h2>品牌资产</h2><p>能力暂缓，保留未来接入企业 DAM 的配置位。</p></div></div><div className="integration-card unavailable-card"><ImageSquare/><div><b>PDP Lab 本地资产库</b><span>暂未开放</span></div><em>未启用</em></div><div className="integration-card unavailable-card"><FolderOpen/><div><b>企业 DAM</b><span>等待后续配置 API 地址和访问凭据</span></div><button disabled>暂未开放</button></div></>}
      {tab==='集成服务'&&<><div className="settings-head"><div><h2>集成服务</h2><p>AI 模型 API 与 PDP Skill 在管理后台拥有彼此独立的配置入口。</p></div></div><div className="integration-card"><Sparkle/><div><b>AI 页面理解</b><span>{diagnosisConfig?.active_adapter==='openai' ? `OpenAI 兼容接口 · ${diagnosisConfig.model_name} · ${diagnosisConfig.ai_protocol === 'chat_completions' ? 'Chat Completions' : 'Responses'}` : `当前为 Mock 安全阻断 · 待启用模型 ${diagnosisConfig?.configured_model_name || 'gpt-5.4-mini'}`} · {diagnosisConfig?.ai_config_source === 'admin' ? '后台独立配置' : '环境变量'}</span></div><em className={diagnosisConfig?.openai_configured?'config-status ready':'config-status'}>{diagnosisConfig?.openai_configured?'密钥已配置':'等待密钥'}</em></div><div className="integration-card"><ShieldCheck/><div><b>PDP 评分 Skill</b><span>{diagnosisConfig?.source_skill || 'pdp-detail-page-methodology'} · {diagnosisConfig?.skill_mode === 'remote_http' ? diagnosisConfig?.skill_endpoint_url : '内置版本化规则'}{ruleRevision ? ` · ${ruleRevision}` : ''} · {diagnosisConfig?.skill_config_source === 'admin' ? '后台独立配置' : '默认配置'}</span></div><em className="config-status ready">{diagnosisConfig?.scoring_standard_version || 'pdp-v1'}</em></div><div className="integration-card unavailable-card"><ImageSquare/><div><b>AI 图像生成</b><span>当前版本暂缓开放</span></div><em>未启用</em></div></>}
      {tab==='团队权限'&&<><div className="settings-head"><div><h2>团队权限</h2><p>控制项目成员与定期报告。</p></div></div><div className="member-row"><UserAvatar user={currentUser}/><div><b>{currentUser?.nickname || currentUser?.username || '用户'}</b><span>{currentUser?.email || '未设置邮箱'}</span></div><em>{userRoleLabel(currentUser)}</em></div><SettingToggle label="每周项目摘要" description="每周一向团队管理员发送项目进展摘要" checked={settings.weeklyDigest} onChange={value=>setSettings({...settings,weeklyDigest:value})}/></>}
      <div className="settings-actions"><button className="primary" onClick={()=>onSaved('系统设置已保存')}>保存设置</button></div>
    </div>
  </section>;
}

function SettingToggle({ label, description, checked, disabled=false, onChange }) { return <div className={`setting-row${disabled?' disabled':''}`}><div><b>{label}</b><span>{description}</span></div><button disabled={disabled} aria-label={`${label}${checked?'已开启':'已关闭'}`} className={checked?'toggle active':'toggle'} aria-pressed={checked} onClick={()=>onChange(!checked)}><span/></button></div>; }
function SettingSelect({ label, value, onChange, options }) { return <label className="setting-row"><div><b>{label}</b><span>用于评估优化后的目标成熟度</span></div><select value={value} onChange={event=>onChange(event.target.value)}>{options.map(option=><option key={option}>{option}</option>)}</select></label>; }
