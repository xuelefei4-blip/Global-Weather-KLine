<div align="center">

  # 全球气象 K 线监测系统 (Global Weather K-Line)

  <p align="center">
    <a href="README.md">English</a> | <b>简体中文</b>
  </p>

  <br>

  <p align="center">
    🌍📈 借鉴金融专业 K 线图表，将全球气候波动与气象数据进行深度可视化呈现。
  </p>

  <!-- 状态与技术栈徽章 -->
  <p align="center">
    <a href="https://github.com/xuelefei4-blip/Global-Weather-KLine/actions"><img src="https://img.shields.io/badge/status-active-success.svg" alt="Status"></a>
    <img src="https://img.shields.io/badge/version-1.0.2026-green.svg" alt="Version">
    <img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License">
    <img src="https://img.shields.io/badge/charts-Lightweight%20Charts-ff69b4.svg" alt="Charts">
    <img src="https://img.shields.io/badge/globe-Globe.gl-orange.svg" alt="3D Globe">
  </p>

  <p align="center">
    <a href="https://github.com/xuelefei4-blip/Global-Weather-KLine/issues"><img src="https://img.shields.io/static/v1?color=1f2328&logo=github&logoColor=fff&label&message=Github%20Issues" alt="Issues"></a>
    <a href="https://github.com/xuelefei4-blip/Global-Weather-KLine/discussions"><img src="https://img.shields.io/static/v1?color=1f2328&logo=github&logoColor=fff&label&message=Github%20Discussions" alt="Discussions"></a>
  </p>

</div>

---

## 📸 运行预览

<p align="center">
  <img src="MeteoSystem/docs/preview.gif" width="100%" alt="全球气象 K 线监测系统预览">
</p>

---

## ✨ 核心特性

* 📦 **零后端依赖**：纯静态前端架构设计，本地即可直接运行，或部署至任何静态网页服务器。
* 🚀 **TradingView 级渲染引擎**：基于 `Lightweight Charts` 构建，保证海量气象数据拖拽、缩放时的流畅体验。
* 🌐 **3D 地球交互选点**：集成 `Globe.gl` 交互式 3D 地球，支持旋转与点击快速切换观测城市（目前覆盖全球 170 个核心城市）。
* 📊 **多维气象 K 线**：统一仪表盘整合展示**气温、相对湿度、气压**等历史多周期波动特征。
* 🔬 **双城实验室**：支持任意两个城市的气象指标并排对比，便于跨区域气候关联性分析。
* ⏳ **多周期自由切换**：支持小时线 (H)、日线 (D)、周线 (W)、月线 (M) 与年线 (Y) 的平滑切换。
* 🌗 **双配色主题适配**：原生支持暗黑模式 (Dark) 与明亮模式 (Light)，无缝适应各类展示环境。

---

## 📦 项目结构

```text
Global-Weather-KLine/
└── MeteoSystem/               # 气象 K 线监测与多维分析实验室核心目录
    ├── .vscode/               # VS Code 开发配置（如 Live Server 端口）
    ├── docs/                  # 文档与预览资源（包含预览动图 preview.gif）
    ├── static/                # 静态静态资源库
    │   ├── css/               # 样式表
    │   ├── data/              # 全球 170 个城市的静态气象 JSON 数据
    │   └── images/            # 3D 地球材质贴图与图标资源
    ├── kline.html             # 单城市气象 K 线监测主页面
    └── lab.html               # 双城横向对比分析实验室

```

 ## 🚀 快速运行
克隆代码仓库：

Bash
git clone [https://github.com/xuelefei4-blip/Global-Weather-KLine.git](https://github.com/xuelefei4-blip/Global-Weather-KLine.git)
cd Global-Weather-KLine
本地浏览：

双击 MeteoSystem/kline.html 直接使用现代浏览器打开，或

在 VS Code 中安装 Live Server 插件一键启动本地静态服务。

## 📄 开源协议
本项目基于 MIT License 开源协议。