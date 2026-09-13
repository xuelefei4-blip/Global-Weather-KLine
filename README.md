<div align="center">

  <!-- 项目 Logo -->
  <a href="https://github.com/xuelefei4-blip/Global-Weather-KLine">
    <img src="MeteoSystem/docs/preview.gif" width="100%" alt="Global Weather KLine Live Preview">
  </a>

  # Global Weather KLine

  <p align="center">
    English | <b>简体中文</b>
  </p>

  <br>

  <p align="center">
    🌍📈 Visualize global climate and meteorological data through professional financial K-line charts.
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

## 📸 Live Preview (运行演示)

<p align="center">
  <img src="docs/preview.gif" width="100%" alt="Global Weather KLine Live Preview">
</p>
---

## ✨ Features

* 📦 **Out of the box:** Simple and fast integration, zero backend dependency to get started.
* 🚀 **Lightweight & Smooth:** High-performance rendering via TradingView's `Lightweight Charts` engine.
* ⏳ **Multi-Resolution:** Smooth switching between **H (Hour)**, **D (Day)**, **W (Week)**, **M (Month)**, and **Y (Year)** periods.
* 🌐 **3D Globe Integration:** Immersive 3D interactive earth using `Globe.gl`, syncing seamlessly with 161 global cities.
* 💧 **Humidity & DRT Alerts:** Real-time relative humidity tracking complemented by customized DRT threshold warning indicators.
* 🌗 **Dual Theme:** Out-of-the-box support for sleek Dark Mode and clean Light Mode.

---

## 📦 Architecture (项目结构)

```text
Global-Weather-KLine/
├── MeteoSystem/               # [前端大屏] 纯静态气象 K 线监控系统
│   ├── kline.html             # 单城市气象 K 线监控主界面
│   ├── lab.html               # 双城市同屏对比实验室
│   └── static/                # 样式、地球贴图及全球气象 JSON 数据库
│
└── MeteoOps/                  # [后端管道] Python 自动化运维与质检工具箱
    └── scripts/               # 6步闭环数据抓取、对齐与自愈修复脚本