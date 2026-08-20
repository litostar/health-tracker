# 🍎 个人健康与热量追踪工作台

一个**个人用**的健康数据 Web 应用：记录身体档案、体检指标、每日三餐热量，并接入 **Apple Watch 真实活动数据**动态计算每日总消耗（TDEE），给出当日热量缺口/盈余。

> **当前版本为纯前端（无服务器）**，与「🍑背单词」同架构：所有数据存在你浏览器 `localStorage`，部署到 GitHub Pages，手机刷新即用。若需要跨设备云同步，仓库内含一份**可选的自托管 FastAPI 后端**（`backend/`）。

---

## ✨ 核心特性

| 模块 | 说明 |
|------|------|
| 个人档案 | 性别/年龄/身高/体重/目标体重/目标体脂/每日目标摄入 |
| 体检指标 | 通用「名称-数值-单位」存储，TSH、血脂等随便记 |
| 每日热量 | 按早/午/晚/加餐记录食物、重量、热量，自动汇总并与目标对比 |
| Apple Watch | 手动录入当日活动消耗/休息消耗/步数（iOS 不允许网页直读 HealthKit） |
| 动态 TDEE | **不用固定活动系数**，用 Watch 真实数据算当日总消耗 |
| 首页看板 | 热量圆环 + 指标网格（目标/BMR/TDEE/缺口）+ 餐次占比 |
| 趋势图 | 近 7/30 天「摄入 vs TDEE」折线图 |
| PWA | 可「添加到主屏幕」、离线开壳 |
| 数据备份 | 导出/导入 JSON，换设备可迁移 |

---

## 🧮 动态 TDEE 算法（重点）

传统 TDEE = BMR × 固定活动系数（1.2/1.5/1.75…），系数是拍脑袋的常数，反映不了你**今天**真实动了多少。本系统改为用 Apple Watch 真实数据：

```
BMR（基础代谢，Mifflin-St Jeor）:
  男: 10×体重kg + 6.25×身高cm − 5×年龄 + 5
  女: 10×体重kg + 6.25×身高cm − 5×年龄 − 161

TDEE（当日总消耗，二选一口径）:
  A) 录入了「休息消耗 Resting Energy」:  TDEE = 休息消耗 + 活动消耗
     （Resting Energy 已含 BMR + 部分 NEAT，最精确）
  B) 只录入「活动消耗 Active Energy」:    TDEE = BMR + 活动消耗
     （Active Energy 不含静息，用 BMR 补足）

热量缺口/盈余 = TDEE − 当日摄入
  正值 → 缺口（减脂）   负值 → 盈余（增重）
```

算法实现见 [`js/tdee.js`](js/tdee.js)（前端，含详细注释）；[`backend/app/tdee.py`](backend/app/tdee.py) 是同一逻辑的后端镜像，供自托管时使用。

---

## 📁 项目结构

```
health-tracker/
├── index.html                # 应用入口（纯静态，GitHub Pages 根目录）
├── css/style.css
├── js/
│   ├── tdee.js               # ★ 动态 TDEE 算法（重点注释）
│   ├── store.js              # 本地数据层（localStorage，替代后端 API）
│   ├── charts.js             # Chart.js 折线图封装
│   └── app.js                # 主逻辑
├── manifest.webmanifest      # PWA 清单
├── sw.js                     # Service Worker（离线壳 + 网络优先刷新）
├── icon.svg
├── backend/                  # 【可选】自托管 FastAPI 后端（跨设备云同步用）
├── render.yaml               # 【可选】Render 一键部署配置
└── README.md
```

---

## 🚀 本地运行（无需后端）

直接用浏览器打开 `index.html` 即可；或起个静态服务器（PWA/Service Worker 需要 http/https 环境）：

```bash
python3 -m http.server 8000
# 浏览器打开 http://localhost:8000
```

所有数据存在当前浏览器的 `localStorage`，不上传任何服务器。

---

## ☁️ 部署到 GitHub Pages（手机访问，push 即更新）

与「🍑背单词」完全相同的静态托管方式：

1. 把本仓库推到 GitHub（**公开仓库**才能用免费 Pages）。
2. 仓库 **Settings → Pages → Build and deployment → Source** 选 `Deploy from a branch`，分支 `main`、目录 `/ (root)`。
3. 等 1~2 分钟构建，访问 `https://<你的用户名>.github.io/health-tracker/`。
4. **以后电脑改完 `git push`，Pages 自动重建，手机刷新就是最新版。**

> 若本机 `git push` 走代理失败（CONNECT 隧道 502），可改用 GitHub **Contents API** 上传文件（和 🍑背单词 HANDOVER.md 里的脚本同款），或直接用 GitHub Web 界面拖文件上传。

---

## 🔄 跨设备云同步（可选，自托管后端）

纯本地版数据按设备隔离（手机/电脑不同步），换设备需用「档案」页导出/导入互传。

若想要自动同步，可用 `backend/` 里的 FastAPI + SQLite 服务，部署到 Render / Railway / VPS（见 `backend` 内说明与 `render.yaml`），再把前端 `js/store.js` 换成调用后端接口即可。当前默认是纯本地版。

---

## 📱 iPhone 快捷指令自动同步

纯本地版需**手动录入** Watch 数据。若已自托管后端，可配置 iPhone 快捷指令每天 POST 到 `https://你的域名/api/sync/watch`（详见 `backend/` 文档），首页 TDEE 与缺口会自动更新。

---

## ⚠️ 注意事项

- **数据安全**：数据在浏览器本地，清缓存/换设备/隐私模式都会丢，请定期用「档案」页**导出 JSON** 备份。
- **GitHub Pages 国内稳定性**：偶尔不稳，如需稳定可改用 Vercel / Cloudflare Pages / 腾讯云 COS（同样是纯静态，零改动）。
- **隐私**：纯本地版数据不上传任何服务器；自托管后端时请务必设置强口令并保护好数据库文件。

---

## 🎨 界面与体验（UI 优化 & 借鉴来源）

参考 GitHub 上同类开源项目后做的优化：

- **首页热量圆环**：借鉴 [OpenNutriTracker](https://github.com/simonoppowa/OpenNutriTracker) / [NutriTrace](https://github.com/TraceApps/nutritrace) 的「calorie ring」——Apple Activity 风格圆环展示「摄入 vs 目标」，达标变绿、超标变红。
- **按餐次占比条 + 列表**：借鉴 NutriTrace 的「per-meal breakdown」，一眼看清早/午/晚/加餐各占多少。
- **PWA 可安装**：借鉴 [nutritrack](https://github.com/sderosiaux/nutritrack) 的离线优先思路，加 `manifest.webmanifest` + `sw.js`，手机「添加到主屏幕」即变独立 App。
- 视觉风格为 **Clean Minimal SaaS**（白底 / 浅灰边框卡片 / indigo 主色 / 大圆角）。
