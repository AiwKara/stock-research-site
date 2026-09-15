# 多体系选股研究 · 个人研究终端

一个**纯静态、移动端自适应**的股票研究看板。托管在 GitHub Pages，手机浏览器 / 电脑浏览器直接打开即可，**无需登录任何账号**。

> ⚠️ 本报告仅供研究参考，不构成个人投资建议。所有「情景涨幅区间」均为基于显式假设的前瞻性判断，不代表实际收益承诺。

---

## 一、在线访问

部署完成后，站点的地址形如：

```
https://<你的GitHub用户名>.github.io/<仓库名>/
```

- **电脑端**：顶部横向标签导航，多列网格布局
- **手机端**：底部固定导航栏（模拟原生 App 体验），单列卡片流，针对触控优化（最小点击区 44px、适配刘海屏安全区）

两端是**同一份 HTML**，通过 CSS 媒体查询自动切换布局，无需分别维护。

---

## 二、目录结构

```
stock-research-site/
├── index.html              # 站点主体（单文件，含内联 CSS/JS）
├── assets/
│   └── data.js             # 全部研究数据（行情/候选/评级/情景/风险/溯源）
├── scripts/
│   └── refresh.py          # 可选：定时刷新量化数据
├── .github/workflows/
│   └── refresh.yml         # 可选：GitHub Actions 定时任务
├── robots.txt              # 屏蔽搜索引擎收录
└── .nojekyll               # 跳过 Jekyll 处理（避免下划线文件被忽略）
```

**更新内容只需改 `assets/data.js`**，页面会自动渲染，无需动 HTML。

---

## 三、部署步骤

### 方式 A：使用 GitHub CLI（推荐）

```bash
cd stock-research-site
git init -b main
git add .
git commit -m "init: 多体系选股研究终端"

# 创建仓库并推送（public 才能用免费的 GitHub Pages）
gh repo create <仓库名> --public --source=. --push

# 开启 Pages（从 main 分支根目录发布）
gh api -X POST repos/<用户名>/<仓库名>/pages \
  -f "source[branch]=main" -f "source[path]=/"
```

### 方式 B：网页手动操作

1. 在 GitHub 新建一个 **Public** 仓库（例如 `stock-research`）
2. 把本目录所有文件推上去
3. 进入仓库 → **Settings → Pages**
4. **Source** 选 `Deploy from a branch`，**Branch** 选 `main` + `/ (root)`，保存
5. 等待 1–2 分钟，访问 `https://<用户名>.github.io/<仓库名>/`

> **必须选 Public 仓库**：免费账号的 GitHub Pages 只支持公开仓库。私有仓库需 GitHub Pro。

---

## 四、隐私与合规说明（重要）

本站已做两层处理：

| 措施 | 作用 |
|---|---|
| `robots.txt` 全站 `Disallow: /` | 阻止搜索引擎抓取收录 |
| 页面 `<meta name="robots" content="noindex, nofollow, noarchive">` | 双重保险，防止被索引 |

**但请知悉**：GitHub Pages 的站点本质上仍是**公开可访问**的——任何拿到 URL 的人都能打开。不做索引 ≠ 私有。

如果你需要真正的访问控制，可改用：

- **Cloudflare Pages + Cloudflare Access**（免费额度支持邮箱白名单，最轻量）
- **Netlify 密码保护**
- **Vercel + Password Protection**

**合规提示**：依据《关于加强对利用"荐股软件"从事证券投资咨询业务监管的暂行规定》（证监会公告〔2012〕40号），向投资者**销售或提供**具备"具体证券品种选择建议""买卖时机建议""价格走势预测"功能的软件并获取经济利益，属于证券投资咨询业务，须持牌经营。

本站定位为**个人自用的研究笔记**，内容以「事实数据 + 显式假设 + 概率 + 推翻条件」的**研究报告形态**呈现，而非「荐股」形态。**若未来打算对外提供或商业化，请务必先咨询执业律师做合规评估。**

---

## 五、数据说明

| 项目 | 说明 |
|---|---|
| 数据基准日 | `2026-09-14`（收盘） |
| 数据源 | 东方财富妙想选股 + 公开研报/公告 |
| 筛选池 | 305 只唯一标的 |
| 候选 | 12 只 |
| 更新方式 | 手动维护 `assets/data.js`，或配置 Actions 定时刷新 |

### 主张类型标注（页面内使用）

- **事实** — 可核查的客观数据（行情、财务、公告、运价、政策）
- **判断** — 研究员基于事实的主观推断
- **模型输出** — 基于显式假设的测算结果

### 已知数据缺口

- 龙虎榜、创 60 日新高：妙想选股接口未返回，暂缺
- 情绪阶梯基于当日 40 只涨停样本，完整涨停家数为 56 只
- 未做历史回测验证，未纳入交易成本与税费

---

## 六、可选：定时自动刷新

如果需要让量化数据（行情、估值、筛选池）自动更新，可配置 GitHub Actions：

1. 把妙想 API Key 存为仓库 Secret：
   **Settings → Secrets and variables → Actions → New repository secret**
   名称 `EM_API_KEY`，值填你的妙想 Key

2. 工作流文件已就位（`.github/workflows/refresh.yml`），默认**工作日 16:30（北京时间）**运行

3. 也可在 **Actions → 数据刷新 → Run workflow** 手动触发

> **注意**：自动刷新只能更新**量化数据**。评级、情景区间、触发/推翻条件属于分析师判断，仍需人工维护。
> API Key 只存在于 Actions Secrets 中，**不会出现在前端代码里**（前端是纯静态页面，不持有任何凭据）。

---

## 七、本地预览

直接用浏览器打开 `index.html` 即可。

若需模拟 GitHub Pages 的路径环境（例如检查相对路径引用）：

```bash
cd stock-research-site
python -m http.server 8000
# 然后访问 http://localhost:8000
```

---

*研究框架：三体系隔离 + 信息分层聚合 + 情景化判断*
