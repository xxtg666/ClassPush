> 注：由 Claude Opus 4.6 原始生成，实际应用有较多改动。

---

# 班级大屏消息推送系统 —— 详细设计文档

## 产品名称：**ClassPush · 班推**

---

## 目录

1. [产品概述与用户画像](#1-产品概述)
2. [系统总体架构](#2-系统总体架构)
3. [消息展示端 UI 设计](#3-消息展示端-ui-设计)
4. [动画系统设计](#4-动画系统设计)
5. [消息发送端设计](#5-消息发送端设计)
6. [消息数据模型与管理](#6-消息数据模型与管理)
7. [网络通信设计](#7-网络通信设计)
8. [配置与个性化系统](#8-配置与个性化系统)
9. [安装与部署方案](#9-安装与部署方案)
10. [文件与工程结构](#10-文件与工程结构)
11. [异常处理与健壮性](#11-异常处理与健壮性)
12. [未来扩展规划](#12-未来扩展规划)

---

## 1. 产品概述

### 1.1 产品定位

ClassPush 是一款运行在班级大屏（电子白板 / 一体机）上的 **桌面常驻消息推送应用**，教师可通过 **本机控制面板** 或 **手机/笔记本浏览器** 向大屏推送文字通知，系统以 **醒目动画 + 半透明悬浮窗** 的形式呈现在屏幕上，确保全班同学都能清晰看到。

### 1.2 核心用户画像

| 角色 | 使用场景 | 技术水平 | 核心诉求 |
|------|----------|----------|----------|
| 班主任 | 发布每日作业、考试安排、临时通知 | 基础电脑操作 | 操作简单，发送快速 |
| 科任老师 | 课间/课后推送作业 | 基础电脑操作 | 手机就能发送 |
| 值日班委 | 推送值日安排、班级公告 | 青少年，手机操作熟练 | 界面直观 |
| 全班学生 | 被动接收，看大屏 | — | 字大、醒目、看得清 |

### 1.3 核心设计原则

```
🎯 大字体、高对比度 —— 教室最后一排也能看清
🎯 零学习成本 —— 打开就会用，手机扫码就能发
🎯 不干扰教学 —— 可随时隐藏/最小化，动画结束后安静停靠
🎯 视觉现代化 —— 毛玻璃、圆角、渐变色，拒绝 Windows XP 风格
```

---

## 2. 系统总体架构

### 2.1 架构模式

采用 **单体应用 + 内嵌Web服务** 的混合架构：

```
┌─────────────────────────────────────────────────────────┐
│                    ClassPush 主进程                       │
│                                                         │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │  PyQt6 GUI  │  │ Flask/Quart  │  │  SQLite 存储  │  │
│  │  展示 + 控制 │◄─►│  Web API     │◄─►│  消息持久化   │  │
│  │  动画引擎    │  │  + Web前端   │  │               │  │
│  └──────┬──────┘  └──────┬───────┘  └───────────────┘  │
│         │                │                               │
│         ▼                ▼                               │
│  ┌─────────────┐  ┌──────────────┐                      │
│  │ 系统托盘    │  │ 局域网端口   │◄── 教师手机/笔记本   │
│  │ 常驻后台    │  │ :8080       │    浏览器访问         │
│  └─────────────┘  └──────────────┘                      │
└─────────────────────────────────────────────────────────┘
```

### 2.2 线程模型

```
主线程 (Qt Event Loop)
  ├── GUI 渲染 & 动画驱动
  ├── 系统托盘管理
  └── 定时器轮询新消息

子线程 1: Web 服务器 (Flask/Quart)
  └── 处理 HTTP 请求 (发送消息 / 获取消息列表 / 静态页面)

子线程 2: 消息调度器
  ├── 新消息检测
  ├── 定时消息触发
  └── 信号发射 → 主线程动画触发
```

### 2.3 技术选型

| 组件 | 技术选择 | 理由 |
|------|----------|------|
| GUI 框架 | PyQt6 | 跨平台，动画能力强，QPropertyAnimation 体系成熟 |
| Web 服务 | Flask + Waitress | 轻量、稳定，Waitress 作为生产级 WSGI 服务器 |
| 数据库 | SQLite3 | 零配置，单文件，Python 内置 |
| 打包工具 | PyInstaller / Nuitka | 生成单 exe，免安装 Python 环境 |
| 二维码 | qrcode + Pillow | 生成局域网访问二维码 |
| 字体 | 思源黑体 / HarmonyOS Sans（内嵌） | 现代、清晰、免费商用 |

---

## 3. 消息展示端 UI 设计

### 3.1 整体布局策略

展示端有 **三种显示模态**，根据消息状态自动切换：

```
┌──────────────────────────────────────────────────┐
│                                                  │
│           模态 A: 新消息弹入动画                  │
│     (全屏半透明遮罩 + 居中大卡片飞入)             │
│           持续 5-8 秒后自动过渡到 B               │
│                                                  │
├──────────────────────────────────────────────────┤
│                                                  │
│           模态 B: 消息列表停靠                    │
│     (屏幕右侧 1/3 区域，半透明面板)              │
│           显示最近 N 条消息摘要                   │
│                                                  │
├──────────────────────────────────────────────────┤
│                                                  │
│           模态 C: 完全隐藏                        │
│     (仅系统托盘图标 + 右上角小徽章)              │
│           点击/有新消息时恢复                     │
│                                                  │
└──────────────────────────────────────────────────┘
```

### 3.2 模态 A：新消息弹入（全屏提醒）

这是最核心的展示模态，当新消息到达时触发。

#### 3.2.1 视觉布局（精确到像素级）

```
┌────────────────────────── 全屏 ──────────────────────────┐
│                                                          │
│  ░░░░░░░░░░░░ 半透明黑色遮罩 (opacity: 0.4) ░░░░░░░░░  │
│  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  │
│  ░░░░░┌────────────────────────────────────┐░░░░░░░░░░  │
│  ░░░░░│  🔔  新消息提醒                 ✕  │░░░░░░░░░░  │
│  ░░░░░├────────────────────────────────────┤░░░░░░░░░░  │
│  ░░░░░│                                    │░░░░░░░░░░  │
│  ░░░░░│   ┌──┐                             │░░░░░░░░░░  │
│  ░░░░░│   │类│  消息标题 (大号粗体)         │░░░░░░░░░░  │
│  ░░░░░│   │型│                             │░░░░░░░░░░  │
│  ░░░░░│   │标│  发送人: 张老师              │░░░░░░░░░░  │
│  ░░░░░│   │签│  时间: 14:30                │░░░░░░░░░░  │
│  ░░░░░│   └──┘                             │░░░░░░░░░░  │
│  ░░░░░│  ──────────────────────────────    │░░░░░░░░░░  │
│  ░░░░░│                                    │░░░░░░░░░░  │
│  ░░░░░│   消息正文内容，这里用超大字体      │░░░░░░░░░░  │
│  ░░░░░│   显示，确保最后一排也能看清。      │░░░░░░░░░░  │
│  ░░░░░│   支持多行自动换行。               │░░░░░░░░░░  │
│  ░░░░░│                                    │░░░░░░░░░░  │
│  ░░░░░│            ┌─────────────┐         │░░░░░░░░░░  │
│  ░░░░░│            │  知道了 ✓   │         │░░░░░░░░░░  │
│  ░░░░░│            └─────────────┘         │░░░░░░░░░░  │
│  ░░░░░│                                    │░░░░░░░░░░  │
│  ░░░░░│   ●●●○○○  (3/6 条新消息)           │░░░░░░░░░░  │
│  ░░░░░└────────────────────────────────────┘░░░░░░░░░░  │
│  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  │
└──────────────────────────────────────────────────────────┘
```

#### 3.2.2 精确样式规格

**遮罩层 (Overlay)**
- 覆盖范围：全屏
- 背景色：`rgba(0, 0, 0, 0.45)`
- 模糊效果：背景高斯模糊 $r = 15\text{px}$（`QGraphicsBlurEffect`）

**消息卡片 (Card)**
- 尺寸：屏幕宽度的 $60\%$，高度自适应（最小 $40\%$ 屏高，最大 $75\%$ 屏高）
- 位置：水平垂直居中
- 圆角：$20\text{px}$
- 背景：毛玻璃效果
  - 底色：`rgba(255, 255, 255, 0.92)`
  - 边框：$1\text{px} \; \text{solid} \; \text{rgba}(255, 255, 255, 0.6)$
  - 投影：$0 \; 20\text{px} \; 60\text{px} \; \text{rgba}(0, 0, 0, 0.3)$

**标题栏**
- 高度：$64\text{px}$
- 背景渐变：从 `#667eea` 到 `#764ba2`（蓝紫渐变）
- 左侧图标：🔔 铃铛 + `"新消息提醒"` 字样
  - 字体：HarmonyOS Sans Bold, $22\text{px}$, 白色
- 右上角关闭按钮：$36 \times 36\text{px}$ 圆形，hover 变红

**类型标签 (Type Badge)**
- 尺寸：$48 \times 48\text{px}$ 圆角矩形（圆角 $10\text{px}$）
- 根据消息类型变色：

| 类型 | 颜色 | 图标 | 标签文字 |
|------|------|------|----------|
| 作业 | `#FF6B6B` (红) | 📝 | 作业 |
| 通知 | `#4ECDC4` (青) | 📢 | 通知 |
| 紧急 | `#FF0000` (鲜红) | 🚨 | 紧急 |
| 提醒 | `#FFD93D` (黄) | ⏰ | 提醒 |
| 表扬 | `#6BCB77` (绿) | 🌟 | 表扬 |
| 活动 | `#9B59B6` (紫) | 🎉 | 活动 |

**消息标题**
- 字体：HarmonyOS Sans Bold
- 大小：$32\text{px}$（1080p 屏幕基准），深灰 `#1a1a2e`

**发送人 & 时间**
- 字体大小：$18\text{px}$，灰色 `#666`
- 格式：`"张老师 · 14:30"`

**消息正文**
- 字体：HarmonyOS Sans Medium
- 大小：$\mathbf{28\text{px}}$（这是关键——必须大，教室后排可读）
- 行高：$1.8$
- 颜色：`#2d3436`
- 超长文字：卡片内可滚动，或分页显示

**底部按钮**
- `"知道了 ✓"` 按钮
  - 尺寸：$180 \times 52\text{px}$，圆角 $26\text{px}$
  - 背景渐变同标题栏
  - hover/press 效果：亮度提升 $10\%$

**分页指示器**
- 当有多条未读消息时，底部显示圆点指示
- 当前点：实心，其余：空心
- 支持左右滑动/点击切换（也可自动轮播）

### 3.3 模态 B：消息列表停靠（侧边栏）

新消息提醒动画结束、用户点击"知道了"、或自动超时后，切换到此模态。

#### 3.3.1 视觉布局

```
                                    ┌─── 屏幕右侧 ───┐
                                    │                 │
正常桌面/教学软件内容                │  ┌─────────────┐│
                                    │  │ 📋 班级消息  ││
                                    │  │   6条消息    ││
                                    │  ├─────────────┤│
                                    │  │ ❶ 📝 作业   ││
                                    │  │ 语代在办公室 ││
                                    │  │ 领取作业     ││
                                    │  │ 14:30       ││
                                    │  ├─────────────┤│
                                    │  │ ❷ 📢 通知   ││
                                    │  │ 历史国庆作业 ││
                                    │  │ 1.辅导步步...││
                                    │  │ 13:45       ││
                                    │  ├─────────────┤│
                                    │  │ ❸ ...       ││
                                    │  │             ││
                                    │  ├─────────────┤│
                                    │  │ ❹ ...       ││
                                    │  │             ││
                                    │  ├─────────────┤│
                                    │  │  ▼ 查看更多  ││
                                    │  └─────────────┘│
                                    │  [收起] [清空]   │
                                    └─────────────────┘
```

#### 3.3.2 精确样式规格

**面板容器**
- 宽度：屏幕宽度的 $30\%$（最小 $400\text{px}$，最大 $560\text{px}$）
- 高度：屏幕高度的 $85\%$
- 位置：屏幕右侧，垂直居中
- 右侧边距：$16\text{px}$
- 背景：`rgba(240, 244, 255, 0.88)` + 毛玻璃
- 圆角：$16\text{px}$
- 投影：$-4\text{px} \; 0 \; 30\text{px} \; \text{rgba}(0,0,0,0.15)$

**面板标题**
- `"📋 班级消息"` + 消息数量徽章
- 徽章：红色圆形，白色数字，$24\text{px}$ 直径
- 副标题：当前日期，如 `"2025年9月30日 星期二"`

**消息条目卡片**
- 每条消息：白色卡片，圆角 $12\text{px}$，间距 $10\text{px}$
- 左侧：序号（彩色圆形 $36\text{px}$）+ 类型标签
- 内容区：
  - 标题：$20\text{px}$ Bold，单行截断 + 省略号
  - 正文预览：$16\text{px}$，最多 $2$ 行
  - 时间 + 发送人：$14\text{px}$，灰色，右下角
- 点击效果：轻微放大 $1.02 \times$，显示完整内容弹窗

**底部操作栏**
- `[收起侧栏]` 按钮：侧栏滑出并隐藏
- `[清空消息]` 按钮：二次确认后清空所有

**自动滚动**
- 当消息超过可视区域，启用自动慢速滚动（速度 $30\text{px/s}$）
- 滚动到底后暂停 $3$ 秒，再回到顶部重新开始

### 3.4 模态 C：隐藏模式

**系统托盘图标**
- 自定义应用图标（铃铛 + 气泡设计）
- 有未读消息时：图标显示红色数字角标
- 右键菜单：
  ```
  ┌─────────────────┐
  │ 📋 显示消息面板  │
  │ 📝 打开控制台    │
  │ ⚙️ 设置          │
  │ ─────────────── │
  │ 🔇 静音模式      │
  │ ❌ 退出          │
  └─────────────────┘
  ```

**右上角浮动徽章（可选）**
- 当有未读消息且侧栏隐藏时
- 屏幕右上角显示一个 $48\text{px}$ 的浮动红色圆形徽章
- 显示未读数字
- 点击展开侧栏
- 5秒无操作后缩小为 $24\text{px}$ 小圆点

### 3.5 窗口属性技术细节

```python
# 关键窗口标志
Qt.WindowType.FramelessWindowHint          # 无边框
Qt.WindowType.WindowStaysOnTopHint         # 始终置顶
Qt.WindowType.Tool                         # 不在任务栏显示
Qt.WidgetAttribute.WA_TranslucentBackground # 背景透明

# 鼠标穿透（仅对无消息区域）
# 通过重写 hitTest 或分区域设置 WA_TransparentForMouseEvents
```

**DPI 适配**
- 获取屏幕 DPI，所有尺寸按比例缩放
- 基准 DPI：$96$（1080p）
- 缩放因子 $s = \text{screenDPI} / 96$
- 所有 px 值乘以 $s$

---

## 4. 动画系统设计

### 4.1 动画基础设施

使用 PyQt6 的 `QPropertyAnimation`、`QParallelAnimationGroup`、`QSequentialAnimationGroup` 构建多层动画流水线。

**缓动函数选择：**

| 动画场景 | 缓动函数 | 效果描述 |
|----------|----------|----------|
| 卡片弹入 | `QEasingCurve.Type.OutBack` | 轻微回弹，活泼感 |
| 卡片退出 | `QEasingCurve.Type.InCubic` | 加速离开，干净利落 |
| 透明度渐变 | `QEasingCurve.Type.InOutQuad` | 平滑过渡 |
| 侧栏滑出 | `QEasingCurve.Type.OutCubic` | 快出慢停 |
| 铃铛摇摆 | `QEasingCurve.Type.InOutSine` | 正弦摆动 |
| 呼吸发光 | `QEasingCurve.Type.SineCurve` | 周期性明暗 |

### 4.2 新消息到达完整动画时间轴

```
时间(ms)    动画事件
────────────────────────────────────────────────────
0           🔔 播放提示音（"叮咚"）
0-300       遮罩层 opacity: 0 → 0.45  (300ms, InOutQuad)
0-100       铃铛图标从屏幕顶部滑入 (100ms)
100-400     铃铛摇摆动画 (左右旋转 ±15°, 3次, InOutSine)
200-600     消息卡片从下方弹入:
              ├── Y坐标: 屏幕底部外 → 屏幕中央 (400ms, OutBack)
              ├── opacity: 0 → 1 (200ms, Linear)
              └── scale: 0.8 → 1.0 (400ms, OutBack)
600-800     卡片内容依次浮现:
              ├── 类型标签: 左侧滑入 (fade + translateX)
              ├── 标题: 上方淡入
              ├── 正文: 上方淡入 (延迟50ms)
              └── 按钮: 缩放弹出
800-1000    卡片投影扩散: shadow blur 0 → 60px
1000+       铃铛消失，卡片静止展示
            
            ⏱ 自动倒计时 8秒（底部进度条）
            
8000        自动关闭流程 (或用户点击"知道了"):
8000-8300   卡片向上滑出 + 缩小 + 淡出
8300-8500   遮罩层 opacity: 0.45 → 0
8500        → 进入模态 B（侧栏滑入）
              └── 侧栏从右侧外滑入 (300ms, OutCubic)
```

### 4.3 各动画详细参数

#### 4.3.1 遮罩层渐现

```python
# 属性: windowOpacity 或自定义 opacity 属性
QPropertyAnimation(overlay_widget, b"opacity")
duration = 300  # ms
start_value = 0.0
end_value = 0.45
easing = QEasingCurve.Type.InOutQuad
```

#### 4.3.2 铃铛摇摆

```python
# 使用 QPropertyAnimation 驱动自定义 rotation 属性
# bell_widget 需要注册 pyqtProperty(float) rotation
# 在 paintEvent 中根据 rotation 做 QPainter.rotate()

bell_shake = QSequentialAnimationGroup()
for i in range(3):
    shake_right = QPropertyAnimation(bell, b"rotation")
    shake_right.setDuration(80)
    shake_right.setStartValue(0)
    shake_right.setEndValue(15)
    
    shake_left = QPropertyAnimation(bell, b"rotation")
    shake_left.setDuration(160)
    shake_left.setStartValue(15)
    shake_left.setEndValue(-15)
    
    shake_back = QPropertyAnimation(bell, b"rotation")
    shake_back.setDuration(80)
    shake_back.setStartValue(-15)
    shake_back.setEndValue(0)
    
    bell_shake.addAnimation(shake_right)
    bell_shake.addAnimation(shake_left)
    bell_shake.addAnimation(shake_back)
```

#### 4.3.3 卡片弹入

```python
# Y轴位移
card_y = QPropertyAnimation(card, b"pos")
card_y.setDuration(400)
card_y.setStartValue(QPoint(center_x, screen_height + 100))
card_y.setEndValue(QPoint(center_x, center_y))
card_y.setEasingCurve(QEasingCurve.Type.OutBack)

# 缩放（通过自定义 scale 属性 + paintEvent 中 QPainter.scale()）
card_scale = QPropertyAnimation(card, b"scale_factor")
card_scale.setDuration(400)
card_scale.setStartValue(0.8)
card_scale.setEndValue(1.0)
card_scale.setEasingCurve(QEasingCurve.Type.OutBack)

# 并行执行
entrance_group = QParallelAnimationGroup()
entrance_group.addAnimation(card_y)
entrance_group.addAnimation(card_scale)
```

#### 4.3.4 呼吸发光边框（紧急消息专用）

```python
# 仅当消息类型为"紧急"时启用
# 卡片边框颜色在红色和橙色之间周期性渐变
glow = QPropertyAnimation(card, b"border_glow_intensity")
glow.setDuration(1000)
glow.setStartValue(0.3)
glow.setEndValue(1.0)
glow.setEasingCurve(QEasingCurve.Type.SineCurve)
glow.setLoopCount(-1)  # 无限循环
```

#### 4.3.5 侧栏滑入/滑出

```python
# 滑入
slide_in = QPropertyAnimation(sidebar, b"geometry")
slide_in.setDuration(300)
slide_in.setStartValue(QRect(screen_w, y, w, h))   # 屏幕外
slide_in.setEndValue(QRect(screen_w - w - 16, y, w, h))  # 停靠位置
slide_in.setEasingCurve(QEasingCurve.Type.OutCubic)
```

#### 4.3.6 消息条目入场（侧栏内，逐条展现）

```python
# 每条消息卡片依次从右侧滑入并淡现
for i, card in enumerate(message_cards):
    anim = QParallelAnimationGroup()
    
    # X 位移
    slide = QPropertyAnimation(card, b"x_offset")
    slide.setDuration(250)
    slide.setStartValue(50)  # 从右侧偏移50px
    slide.setEndValue(0)
    slide.setEasingCurve(QEasingCurve.Type.OutCubic)
    
    # 透明度
    fade = QPropertyAnimation(card, b"opacity")
    fade.setDuration(250)
    fade.setStartValue(0.0)
    fade.setEndValue(1.0)
    
    anim.addAnimation(slide)
    anim.addAnimation(fade)
    
    # 延迟：每条间隔 80ms
    sequential.addPause(80)
    sequential.addAnimation(anim)
```

### 4.4 提示音设计

```
使用 QSoundEffect 播放内嵌音频

音频文件：
  ├── notify_normal.wav    —— 普通消息：清脆"叮咚"，0.8秒
  ├── notify_urgent.wav    —— 紧急消息：连续三声短促"嘟嘟嘟"，1.5秒
  ├── notify_praise.wav    —— 表扬消息：愉快上升音阶，1.0秒
  └── silent.wav           —— 静音模式占位

音量: 系统音量的 80%, 可在设置中调节 (0-100%)
可选: 完全关闭声音
```

### 4.5 动画性能优化策略

| 优化项 | 具体措施 |
|--------|----------|
| 复合动画 | 所有同时发生的动画使用 `QParallelAnimationGroup`，避免多个独立 timer |
| 渲染区域 | 使用 `update(dirtyRect)` 而非 `update()` 全区域重绘 |
| 缓存 | 对不变内容使用 `QPixmap` 缓存，`paintEvent` 中直接 `drawPixmap` |
| 毛玻璃 | 仅在动画开始和结束时截屏做模糊，中间帧复用模糊截图 |
| 帧率控制 | 动画目标 $60\text{fps}$；若检测到卡顿，降级到 $30\text{fps}$ 并简化特效 |
| 阴影优化 | 投影使用预渲染的 9-patch 图片，而非实时计算 |

---

## 5. 消息发送端设计

### 5.1 发送渠道总览

教师有 **三种** 方式发送消息，覆盖所有场景：

```
方式 A: 本机控制台 (在大屏电脑上直接操作)
         └─ PyQt6 原生窗口，快捷键唤出

方式 B: 手机/笔记本浏览器 (扫码访问)
         └─ 内嵌 Web 服务提供的响应式网页

方式 C: 快捷键 + 迷你输入框
         └─ 类似 macOS Spotlight，一键呼出极简输入
```

### 5.2 方式 A：本机控制台

#### 5.2.1 唤出方式
- 系统托盘右键 → `"打开控制台"`
- 全局快捷键：`Ctrl + Shift + M`
- 双击桌面快捷方式（如应用已运行则唤出控制台）

#### 5.2.2 控制台窗口设计

```
┌─────────────────────────────────────────────────────┐
│  ClassPush 控制台                          — □ ✕    │
├──────────┬──────────────────────────────────────────┤
│          │                                          │
│  📝 发消息│  ┌ 发送新消息 ──────────────────────┐   │
│          │  │                                  │   │
│  📋 历史  │  │  消息类型:  [作业 ▼]             │   │
│          │  │                                  │   │
│  📌 置顶  │  │  发送人:   [张老师        ]      │   │
│          │  │            (记住上次输入)         │   │
│  ⚙️ 设置  │  │                                  │   │
│          │  │  消息标题:  [                  ]  │   │
│  📊 统计  │  │            (选填,留空则自动生成)  │   │
│          │  │                                  │   │
│  ❓ 帮助  │  │  消息内容:                       │   │
│          │  │  ┌──────────────────────────┐    │   │
│          │  │  │                          │    │   │
│          │  │  │  在此输入消息内容...      │    │   │
│          │  │  │                          │    │   │
│          │  │  │                          │    │   │
│          │  │  │                          │    │   │
│          │  │  └──────────────────────────┘    │   │
│          │  │                                  │   │
│          │  │  ☐ 标记为紧急    定时发送: [关闭▼]│   │
│          │  │                                  │   │
│          │  │       [预览效果]    [📤 发送]     │   │
│          │  │                                  │   │
│          │  └──────────────────────────────────┘   │
│          │                                          │
├──────────┴──────────────────────────────────────────┤
│  💡 提示: 手机发送请扫描右侧二维码  [显示二维码]     │
└─────────────────────────────────────────────────────┘
```

#### 5.2.3 控制台窗口样式规格

**窗口整体**
- 尺寸：$900 \times 640\text{px}$（可拖拽调整，最小 $720 \times 500$）
- 背景色：`#f8f9fc`
- 左侧导航栏：宽 $200\text{px}$，背景 `#ffffff`，右边线 `1px #e8e8e8`

**左侧导航**
- 每项高 $52\text{px}$
- 选中态：背景 `#eef2ff`，左侧 $3\text{px}$ 蓝色指示线，文字 `#4361ee`
- 默认态：文字 `#555`
- hover 态：背景 `#f5f5f5`
- 图标 + 文字水平排列

**消息类型选择器**
- `QComboBox` 下拉框
- 选项带彩色圆点前缀
- 下拉动画：展开高度 `200ms OutCubic`

**发送人输入框**
- 自动记住上次输入的姓名（保存到配置文件）
- 有 `QCompleter` 自动补全历史发送人

**消息内容输入框**
- `QPlainTextEdit`，高 $200\text{px}$
- placeholder 文字：`"在此输入消息内容，支持多行。Ctrl+Enter 快速发送"`
- 字数统计：右下角灰色小字 `"已输入 42/500 字"`
- **Ctrl+Enter** 快速发送

**紧急标记**
- 勾选后，卡片预览边框变红
- 提示文字：`"紧急消息将全屏红色闪烁提醒"`

**定时发送**
- 下拉选项：`关闭 / 5分钟后 / 10分钟后 / 30分钟后 / 自定义时间`
- 自定义时间弹出 `QDateTimeEdit` 时间选择器

**预览效果按钮**
- 点击后在控制台右侧弹出一个缩小版（$30\%$）的动画预览区
- 展示完整动画流程，但在小窗口内

**发送按钮**
- 尺寸：$140 \times 44\text{px}$
- 渐变色同标题栏蓝紫色
- 发送后：按钮短暂变绿 + 显示 "✓ 已发送"，$1.5$ 秒后恢复
- 发送时的微交互：按钮缩小 $0.95 \times$ → 恢复 + 粒子散射效果（可选）

### 5.3 方式 B：手机/笔记本 Web 发送

#### 5.3.1 访问方式

**二维码扫码**
- 控制台底部点击 `[显示二维码]`，弹出二维码弹窗
- 二维码内容：`http://192.168.x.x:8080`（教室内网 IP）
- 二维码下方文字：`"请确保手机与大屏连接同一 WiFi"`
- 大屏端也会显示二维码浮窗（可选开启，方便学生扫码）

**自动发现**
- Web 页面标题："ClassPush · 发送消息"
- 无需登录（同一局域网即可，可选设置密码）

#### 5.3.2 Web 发送页面设计（移动端优先）

```
┌──────────────────────┐
│  ClassPush 📤        │
│  班级消息发送         │
├──────────────────────┤
│                      │
│  消息类型             │
│  ┌──────────────┐    │
│  │ 📝 作业    ▼ │    │  ← 大按钮下拉，手指友好
│  └──────────────┘    │
│                      │
│  您的称呼             │
│  ┌──────────────┐    │
│  │ 张老师       │    │  ← 自动保存到 localStorage
│  └──────────────┘    │
│                      │
│  消息标题(选填)       │
│  ┌──────────────┐    │
│  │              │    │
│  └──────────────┘    │
│                      │
│  消息内容             │
│  ┌──────────────┐    │
│  │              │    │
│  │              │    │
│  │              │    │  ← 大文本框，适合输入法
│  │              │    │
│  └──────────────┘    │
│                      │
│  ☐ 标记为紧急         │
│                      │
│  ┌──────────────┐    │
│  │   📤 发送    │    │  ← 大按钮 48px 高
│  └──────────────┘    │
│                      │
│  ─ 最近发送 ─        │
│  · 语代在办公室.. 14:30│
│  · 历史国庆作业.. 13:45│
│                      │
└──────────────────────┘
```

#### 5.3.3 Web 技术栈

| 组件 | 选择 |
|------|------|
| 后端 | Flask (Python, 运行在主进程子线程) |
| WSGI 服务器 | Waitress (跨平台, 稳定) |
| 前端框架 | 纯 HTML + CSS + Vanilla JS （不引入重型框架，加快加载） |
| CSS | 内联样式或内嵌 `<style>`，不依赖CDN（局域网不一定能上网） |
| 字体 | 使用系统字体栈：`-apple-system, "PingFang SC", "Microsoft YaHei", sans-serif` |

#### 5.3.4 API 设计

```
POST /api/messages
  Body (JSON):
    {
      "type": "homework",       // homework/notice/urgent/reminder/praise/activity
      "sender": "张老师",
      "title": "语文作业",       // 可选
      "content": "完成第三课练习", // 必填
      "urgent": false,
      "scheduled_at": null       // ISO8601 格式，null 为立即发送
    }
  Response:
    201 Created
    { "id": 42, "status": "sent", "created_at": "..." }

GET /api/messages
  Query: ?limit=20&offset=0
  Response:
    200 OK
    { "messages": [...], "total": 42 }

DELETE /api/messages/{id}
  Response: 204 No Content

GET /api/qrcode
  Response: PNG image (二维码图片)

GET /api/status
  Response: { "online": true, "message_count": 42, "ip": "192.168.1.100" }
```

#### 5.3.5 Web → Qt 通信机制

```
Flask 子线程接收 POST /api/messages
    │
    ▼
写入 SQLite 数据库 (message 表)
    │
    ▼
通过 threading.Event 或 queue.Queue 通知主线程
    │
    ▼
主线程的 QTimer (100ms 轮询) 检测到新消息
    │
    ▼
触发信号 new_message_signal.emit(message_data)
    │
    ▼
槽函数启动动画流水线
```

> **替代方案**：使用 `pyqtSignal` 跨线程信号机制直接从 Flask 路由触发，但需要注意线程安全——推荐用 `QMetaObject.invokeMethod` 或全局 `QApplication.postEvent` 方式。

### 5.4 方式 C：迷你快捷输入

#### 5.4.1 唤出方式
- 全局快捷键：`Ctrl + Shift + N`
- 屏幕中央弹出一个单行输入框

#### 5.4.2 UI 设计

```
    ┌──────────────────────────────────────────┐
    │ 🔍  输入消息内容，按 Enter 发送...      │
    │     [作业▼] [张老师▼]        [发送 ↩]   │
    └──────────────────────────────────────────┘
```

- 宽度：屏幕 $50\%$，高 $56\text{px}$
- 圆角 $28\text{px}$（胶囊形）
- 巨大投影 + 毛玻璃背景
- 入场动画：从 $0.9 \times$ scale 放大到 $1.0 \times$ + 淡入（$200\text{ms}$）
- 按 `Esc` 关闭

---

## 6. 消息数据模型与管理

### 6.1 数据库 Schema

```sql
-- 主数据库: classpush.db

CREATE TABLE IF NOT EXISTS messages (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    type        TEXT NOT NULL DEFAULT 'notice',
        -- 枚举: homework, notice, urgent, reminder, praise, activity
    sender      TEXT NOT NULL DEFAULT '老师',
    title       TEXT,               -- 可为 NULL，显示时自动生成
    content     TEXT NOT NULL,
    urgent      INTEGER DEFAULT 0,  -- 0=普通, 1=紧急
    status      TEXT DEFAULT 'active',
        -- 枚举: active, read, archived, deleted
    pinned      INTEGER DEFAULT 0,  -- 0=不置顶, 1=置顶
    scheduled_at TEXT,              -- ISO8601, NULL=立即发送
    created_at  TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    read_at     TEXT,               -- 首次被展示的时间
    expired_at  TEXT                -- 过期时间, NULL=不过期
);

CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT
);

CREATE TABLE IF NOT EXISTS senders (
    name       TEXT PRIMARY KEY,
    use_count  INTEGER DEFAULT 1,
    last_used  TEXT DEFAULT (datetime('now', 'localtime'))
);

CREATE INDEX idx_messages_status ON messages(status);
CREATE INDEX idx_messages_created ON messages(created_at DESC);
CREATE INDEX idx_messages_scheduled ON messages(scheduled_at);
```

### 6.2 消息生命周期

```
创建 → [定时等待] → 推送展示(模态A) → 标记已读 → 侧栏展示(模态B)
                                                       ↓
                                                  手动归档/自动过期
                                                       ↓
                                                  历史记录(可查看)
                                                       ↓
                                                  手动删除(永久)
```

**自动过期规则：**
- 默认每条消息 $24$ 小时后自动从侧栏移入归档
- 可在设置中调整 ($1\text{h} / 6\text{h} / 12\text{h} / 24\text{h} / 永不过期$)

### 6.3 消息队列逻辑

当同时到达多条消息时：

```python
class MessageQueue:
    """消息展示调度器"""
    
    # 优先级: urgent > normal
    # 同优先级: FIFO
    
    # 展示策略:
    # 1. 紧急消息: 立即打断当前展示，全屏弹出
    # 2. 普通消息: 排队等待，每条间隔 2 秒
    # 3. 多条普通消息积压: 合并为卡片轮播模式
    #    (底部显示 "1/6" 分页指示器，自动翻页，间隔 5 秒)
    # 4. 超过 10 条积压: 只展示最新 3 条的弹窗，其余直接进侧栏
```

---

## 7. 网络通信设计

### 7.1 Web 服务器配置

```python
# 服务器启动参数
HOST = "0.0.0.0"         # 监听所有网卡
PORT = 8080              # 默认端口，可在设置中修改
                         # 若被占用，自动尝试 8081, 8082, ...

# Waitress 配置
serve(app, host=HOST, port=PORT, threads=4)
```

### 7.2 IP 地址获取

```python
import socket

def get_local_ips():
    """获取所有本机局域网 IP"""
    ips = []
    for iface in socket.getaddrinfo(socket.gethostname(), None):
        ip = iface[4][0]
        if ip.startswith("192.168.") or ip.startswith("10.") or ip.startswith("172."):
            ips.append(ip)
    return list(set(ips))

# 在控制台和二维码中显示所有可用 IP
# 并在 Web 页面显示: "当前地址: http://192.168.1.100:8080"
```

### 7.3 安全机制

| 安全措施 | 实现方式 |
|----------|----------|
| 访问密码（可选） | 设置中启用，首次访问输入6位数字密码 |
| 频率限制 | 同一 IP 每分钟最多 10 条消息 |
| 内容长度限制 | 单条消息 $\leq 500$ 字 |
| IP 白名单（可选） | 仅允许指定网段访问 |
| CSRF 防护 | Web 表单使用 hidden token |

---

## 8. 配置与个性化系统

### 8.1 设置页面设计

控制台左侧导航点击 `⚙️ 设置` 进入：

```
┌── 设置 ──────────────────────────────────────────┐
│                                                   │
│  📺 显示设置                                      │
│  ├─ 消息字体大小:    [████████░░] 28px            │
│  ├─ 侧栏位置:       ○ 左侧  ● 右侧              │
│  ├─ 侧栏宽度:       [████████░░] 30%             │
│  ├─ 消息自动关闭:    [8秒 ▼]                      │
│  ├─ 消息过期时间:    [24小时 ▼]                   │
│  └─ 深色模式:        [开关按钮]                   │
│                                                   │
│  🔔 提醒设置                                      │
│  ├─ 提示音:          ● 开  ○ 关                   │
│  ├─ 提示音音量:      [██████░░░░] 60%             │
│  ├─ 紧急消息闪烁:    [开关按钮]                   │
│  └─ 开机自启动:      [开关按钮]                   │
│                                                   │
│  🌐 网络设置                                      │
│  ├─ Web 服务端口:    [8080]                       │
│  ├─ 访问密码:        [未设置] [设置密码]           │
│  └─ 当前地址:        http://192.168.1.100:8080    │
│                      [显示二维码] [复制地址]       │
│                                                   │
│  🎨 主题设置                                      │
│  ├─ 主题色:          ⚫🔵🟣🟢🔴🟡 (色块选择)      │
│  ├─ 卡片风格:        ○ 毛玻璃  ○ 纯色             │
│  └─ 壁纸(侧栏背景):  [选择图片...] [恢复默认]     │
│                                                   │
│  📦 数据管理                                      │
│  ├─ 导出所有消息:    [导出为 CSV]                 │
│  ├─ 清空所有数据:    [清空...] (需确认)           │
│  └─ 消息总数:        142 条                       │
│                                                   │
│                    [恢复默认设置]    [保存]        │
└───────────────────────────────────────────────────┘
```

### 8.2 配置存储

```python
# 配置文件: config.json (应用目录下)
{
    "display": {
        "font_size": 28,
        "sidebar_position": "right",     // "left" | "right"
        "sidebar_width_percent": 30,
        "auto_close_seconds": 8,
        "message_expire_hours": 24,
        "dark_mode": false
    },
    "notification": {
        "sound_enabled": true,
        "sound_volume": 60,
        "urgent_flash": true,
        "auto_start": true
    },
    "network": {
        "port": 8080,
        "password": null,               // null = 无密码
        "password_hash": null           // SHA256 hash
    },
    "theme": {
        "primary_color": "#4361ee",
        "card_style": "glassmorphism",  // "glassmorphism" | "solid"
        "wallpaper": null               // 图片路径或 null
    },
    "user": {
        "last_sender_name": "张老师",
        "sender_history": ["张老师", "李老师", "王同学"],
        "class_name": "高一(3)班"       // 显示在侧栏标题
    }
}
```

### 8.3 暗色模式配色方案

| 元素 | 亮色模式 | 暗色模式 |
|------|----------|----------|
| 遮罩背景 | `rgba(0,0,0,0.45)` | `rgba(0,0,0,0.60)` |
| 卡片背景 | `rgba(255,255,255,0.92)` | `rgba(30,30,46,0.92)` |
| 侧栏背景 | `rgba(240,244,255,0.88)` | `rgba(24,24,37,0.90)` |
| 正文文字 | `#2d3436` | `#cdd6f4` |
| 标题文字 | `#1a1a2e` | `#ffffff` |
| 次要文字 | `#666` | `#a6adc8` |
| 按钮背景 | 蓝紫渐变 | 蓝紫渐变（不变） |
| 消息条目 | `#ffffff` | `rgba(49,50,68,0.9)` |

### 8.4 首次启动引导

用户首次启动应用时，显示 **欢迎向导** (4步)：

```
步骤 1/4: 👋 欢迎使用 ClassPush
            设置您的班级名称: [高一(3)班]

步骤 2/4: 👤 您的称呼
            默认发送人: [张老师]
            
步骤 3/4: 📺 显示偏好
            字体大小预览: [滑块调节，实时预览]
            侧栏位置: [左 / 右]
            
步骤 4/4: 🎉 设置完成！
            扫描二维码，手机也能发消息
            [二维码]
            [开始使用 →]
```

---

## 9. 安装与部署方案

### 9.1 打包策略

```
目标: 双击即用的单文件 / 安装包

方案 A (推荐): Nuitka + NSIS 安装包
  ├── 编译为原生 .exe (比 PyInstaller 更快的启动速度)
  ├── NSIS 安装向导:
  │   ├── 选择安装目录 (默认 C:\Program Files\ClassPush)
  │   ├── 创建桌面快捷方式
  │   ├── 创建开始菜单项
  │   └── 可选: 开机自启动
  └── 安装包大小: ~50-80MB

方案 B (便携版): PyInstaller --onedir
  ├── 生成文件夹，内含 ClassPush.exe
  ├── 压缩为 .zip，拷贝到 U 盘即可使用
  └── 无需安装，双击 exe 直接运行
```

### 9.2 文件打包清单

```
ClassPush/
├── ClassPush.exe           # 主程序
├── config.json             # 配置文件(首次运行自动创建)
├── classpush.db            # 数据库(首次运行自动创建)
├── resources/
│   ├── fonts/
│   │   └── HarmonyOS_Sans_SC_Medium.ttf
│   │   └── HarmonyOS_Sans_SC_Bold.ttf
│   ├── sounds/
│   │   ├── notify_normal.wav
│   │   ├── notify_urgent.wav
│   │   └── notify_praise.wav
│   ├── icons/
│   │   ├── app_icon.ico
│   │   ├── tray_icon.png
│   │   ├── tray_icon_unread.png
│   │   └── type_icons/ (各类型消息图标)
│   └── web/
│       ├── index.html       # Web 发送页面
│       ├── style.css
│       └── script.js
└── logs/
    └── classpush.log       # 日志文件
```

### 9.3 运行环境要求

```
操作系统: Windows 10/11 (主要目标), 可扩展支持 Linux/macOS
屏幕分辨率: 最低 1366×768, 推荐 1920×1080
内存: ≥ 2GB 可用
网络: 需要局域网连接 (用于手机发消息)
```

### 9.4 开机自启动实现

```python
# Windows: 注册表方式
import winreg

def set_autostart(enable: bool):
    key = winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r"Software\Microsoft\Windows\CurrentVersion\Run",
        0, winreg.KEY_SET_VALUE
    )
    if enable:
        winreg.SetValueEx(key, "ClassPush", 0, winreg.REG_SZ, exe_path)
    else:
        try:
            winreg.DeleteValue(key, "ClassPush")
        except FileNotFoundError:
            pass
    winreg.CloseKey(key)
```

---

## 10. 文件与工程结构

### 10.1 源码目录结构

```
classpush/
├── main.py                      # 入口点
├── app.py                       # QApplication 初始化, 单实例检测
│
├── core/
│   ├── __init__.py
│   ├── database.py              # SQLite 数据库操作封装
│   ├── message_manager.py       # 消息 CRUD, 队列调度
│   ├── scheduler.py             # 定时消息调度器
│   ├── config_manager.py        # 配置读写
│   └── signals.py               # 全局自定义信号定义
│
├── ui/
│   ├── __init__.py
│   ├── overlay_window.py        # 模态A: 全屏遮罩 + 弹出卡片
│   ├── message_card.py          # 消息卡片组件
│   ├── sidebar_panel.py         # 模态B: 侧栏面板
│   ├── sidebar_message_item.py  # 侧栏内单条消息组件
│   ├── control_panel.py         # 控制台主窗口
│   ├── control_pages/
│   │   ├── send_page.py         # 发送消息页
│   │   ├── history_page.py      # 历史消息页
│   │   ├── pinned_page.py       # 置顶管理页
│   │   ├── settings_page.py     # 设置页
│   │   ├── stats_page.py        # 统计页
│   │   └── help_page.py         # 帮助页
│   ├── quick_input.py           # 迷你快捷输入框
│   ├── tray_icon.py             # 系统托盘
│   ├── qrcode_dialog.py         # 二维码弹窗
│   ├── welcome_wizard.py        # 首次启动向导
│   └── widgets/
│       ├── animated_button.py   # 自定义动画按钮
│       ├── badge_widget.py      # 数字徽章
│       ├── glassmorphism.py     # 毛玻璃效果混入
│       ├── progress_bar.py      # 倒计时进度条
│       ├── color_picker.py      # 主题色选择器
│       └── toggle_switch.py     # iOS风格开关
│
├── animations/
│   ├── __init__.py
│   ├── entrance_animation.py    # 新消息入场动画组
│   ├── exit_animation.py        # 消息退出动画组
│   ├── bell_animation.py        # 铃铛摇摆
│   ├── glow_animation.py        # 呼吸发光(紧急)
│   ├── slide_animation.py       # 通用滑入滑出
│   └── stagger_animation.py     # 错位逐条入场
│
├── web/
│   ├── __init__.py
│   ├── server.py                # Flask 应用定义
│   ├── routes.py                # API 路由
│   ├── templates/
│   │   └── index.html           # Jinja2 模板(或纯静态)
│   └── static/
│       ├── style.css
│       ├── script.js
│       └── favicon.ico
│
├── resources/
│   ├── fonts/
│   ├── sounds/
│   ├── icons/
│   └── resources.qrc            # Qt 资源文件(可选)
│
├── utils/
│   ├── __init__.py
│   ├── network.py               # IP获取, 端口检测
│   ├── qrcode_gen.py            # 二维码生成
│   ├── autostart.py             # 开机自启动
│   ├── single_instance.py       # 单实例锁
│   └── logger.py                # 日志配置
│
├── tests/
│   ├── test_database.py
│   ├── test_message_manager.py
│   ├── test_web_api.py
│   └── test_animations.py
│
├── build/
│   ├── build_nuitka.bat         # Nuitka 打包脚本
│   ├── build_pyinstaller.spec   # PyInstaller 配置
│   ├── nsis_installer.nsi       # NSIS 安装脚本
│   └── icon.ico
│
├── requirements.txt
├── README.md
└── LICENSE
```

### 10.2 依赖清单

```txt
# requirements.txt
PyQt6>=6.6.0
PyQt6-Qt6>=6.6.0
Flask>=3.0.0
waitress>=3.0.0
qrcode>=7.4
Pillow>=10.0.0
```

---

## 11. 异常处理与健壮性

### 11.1 异常处理矩阵

| 异常场景 | 检测方式 | 处理方案 | 用户提示 |
|----------|----------|----------|----------|
| 端口被占用 | `socket.bind()` 失败 | 自动尝试 $+1$ 端口，最多尝试 $10$ 次 | 托盘气泡通知 "Web服务已启动在端口 8081" |
| 数据库损坏 | `sqlite3.DatabaseError` | 备份旧文件，创建新数据库 | 弹窗提示 "数据已重置" |
| 无网络连接 | 定时检测局域网 IP | 仅禁用 Web 发送，本机功能正常 | 控制台显示 "⚠ 无网络，仅支持本机发送" |
| 屏幕分辨率变化 | `QScreen.geometryChanged` 信号 | 重新计算所有窗口尺寸 | 无需提示 |
| 应用多开 | 文件锁 / Named Mutex | 激活已有实例的窗口 | 无需提示 |
| 配置文件损坏 | JSON 解析失败 | 使用默认配置，备份旧文件 | 托盘通知 "配置已重置为默认" |
| Flash of animation（动画卡顿） | FPS 监测 | 降低动画复杂度 | 无需提示 |
| Web 请求非法内容 | 内容校验 | 返回 400 Bad Request | Web 页面红色提示 "内容不合法" |
| 内存泄漏 | 定时监控进程内存 | 超过 $500\text{MB}$ 时清理历史消息缓存 | 无需提示 |

### 11.2 日志系统

```python
import logging
from logging.handlers import RotatingFileHandler

# 日志配置
logger = logging.getLogger("classpush")
logger.setLevel(logging.INFO)

# 文件日志: 单文件最大 5MB, 保留 3 个备份
file_handler = RotatingFileHandler(
    "logs/classpush.log", 
    maxBytes=5*1024*1024, 
    backupCount=3,
    encoding="utf-8"
)
file_handler.setFormatter(logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
))

# 关键日志事件:
# INFO:  消息创建、消息展示、Web服务启动、配置变更
# WARNING: 端口占用、配置损坏、网络异常
# ERROR: 数据库错误、未预期异常
```

### 11.3 单实例保证

```python
# Windows: Named Mutex
import ctypes

class SingleInstance:
    def __init__(self):
        self.mutex = ctypes.windll.kernel32.CreateMutexW(
            None, False, "ClassPush_SingleInstance_Mutex"
        )
        self.already_running = (
            ctypes.windll.kernel32.GetLastError() == 183  # ERROR_ALREADY_EXISTS
        )
    
    def is_running(self):
        return self.already_running
```

### 11.4 全局异常兜底

```python
import sys
import traceback

def global_exception_handler(exc_type, exc_value, exc_traceback):
    """兜底异常处理，防止应用静默崩溃"""
    logger.critical(
        "Unhandled exception",
        exc_info=(exc_type, exc_value, exc_traceback)
    )
    # 显示用户友好的错误弹窗
    error_text = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    # QMessageBox 弹窗 + 复制到剪贴板 + 建议重启

sys.excepthook = global_exception_handler
```

---

## 12. 未来扩展规划

### 12.1 可选功能（标注为 v2.0+）

<details>
<summary><b>📎 图片消息支持</b></summary>

- Web 端上传图片
- Base64 编码存入数据库
- 展示端显示缩略图，点击放大
- 文件大小限制：$2\text{MB}$
- 支持格式：JPG / PNG / GIF

</details>

<details>
<summary><b>🔗 多教室联动</b></summary>

- 一台主机同时推送到多个教室的大屏
- 使用 WebSocket 实时同步
- 主控端选择目标教室

</details>

<details>
<summary><b>📱 微信小程序发送端</b></summary>

- 开发配套微信小程序
- 扫码绑定教室
- 随时随地发送消息（不限局域网）
- 需要云服务器中转

</details>

<details>
<summary><b>📊 消息统计面板</b></summary>

- 按日期/类型/发送人统计消息数量
- 图表可视化（柱状图、饼图）
- 使用 `pyqtgraph` 或 `QtCharts`

</details>

<details>
<summary><b>🔌 插件系统</b></summary>

- 支持天气插件（侧栏顶部显示天气）
- 课程表插件（显示今日课程）
- 倒计时插件（考试/活动倒计时）

</details>

<details>
<summary><b>🗣️ 语音播报</b></summary>

- 使用 `pyttsx3` 或系统 TTS
- 新消息到达时语音朗读
- 可选开启/关闭

</details>

---

## 附录 A：完整动画状态机

```
                                    ┌──────────┐
                                    │  IDLE    │ ← 初始状态
                                    │ (隐藏)   │
                                    └────┬─────┘
                                         │ new_message
                                         ▼
                                ┌────────────────┐
                                │  ALERTING      │
                 ┌──────────────│ (遮罩+铃铛动画) │
                 │              └────────┬───────┘
                 │ urgent_message         │ 300ms
                 │ interrupts             ▼
                 │              ┌────────────────┐
                 │              │  SHOWING       │
                 │              │ (卡片展示中)    │◄──┐
                 │              └───┬───┬────────┘   │
                 │                  │   │             │
                 │    user_click    │   │ timeout     │ next_message
                 │    "知道了"      │   │ (8s)       │ (有更多消息)
                 │                  │   │             │
                 │                  ▼   ▼             │
                 │          ┌──────────────┐         │
                 │          │  EXITING     │─────────┘
                 │          │ (卡片退出中)  │
                 │          └──────┬───────┘
                 │                 │ 无更多消息
                 │                 ▼
                 │         ┌──────────────┐
                 └────────►│  SIDEBAR     │
                           │ (侧栏展示中)  │
                           └──────┬───────┘
                                  │ 用户收起 / 无消息
                                  ▼
                           ┌──────────────┐
                           │  IDLE        │
                           │ (托盘图标)    │
                           └──────────────┘
```

---

## 附录 B：QSS 样式表核心片段

```css
/* 控制台窗口全局样式 */
QWidget#ControlPanel {
    background-color: #f8f9fc;
    font-family: "HarmonyOS Sans SC", "Microsoft YaHei", sans-serif;
}

/* 左侧导航项 */
QPushButton#NavItem {
    border: none;
    text-align: left;
    padding: 12px 20px;
    font-size: 15px;
    color: #555;
    background: transparent;
    border-left: 3px solid transparent;
}
QPushButton#NavItem:hover {
    background-color: #f5f5f5;
}
QPushButton#NavItem:checked {
    background-color: #eef2ff;
    border-left: 3px solid #4361ee;
    color: #4361ee;
    font-weight: bold;
}

/* 消息输入框 */
QPlainTextEdit#MessageInput {
    border: 2px solid #e0e0e0;
    border-radius: 12px;
    padding: 12px 16px;
    font-size: 16px;
    background: white;
    selection-background-color: #4361ee;
}
QPlainTextEdit#MessageInput:focus {
    border-color: #4361ee;
}

/* 发送按钮 */
QPushButton#SendButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #667eea, stop:1 #764ba2);
    color: white;
    border: none;
    border-radius: 22px;
    font-size: 16px;
    font-weight: bold;
    padding: 10px 32px;
    min-width: 140px;
}
QPushButton#SendButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #7b93ed, stop:1 #8b5fbf);
}
QPushButton#SendButton:pressed {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #5a72d4, stop:1 #6a3fa0);
}

/* iOS 风格 Toggle Switch */
QWidget#ToggleSwitch {
    min-width: 52px;
    max-width: 52px;
    min-height: 28px;
    max-height: 28px;
    border-radius: 14px;
    background-color: #ddd;
}
QWidget#ToggleSwitch[checked="true"] {
    background-color: #4361ee;
}

/* 消息类型 ComboBox */
QComboBox#TypeSelector {
    border: 2px solid #e0e0e0;
    border-radius: 10px;
    padding: 8px 16px;
    font-size: 15px;
    background: white;
    min-width: 200px;
}
QComboBox#TypeSelector::drop-down {
    border: none;
    width: 30px;
}
QComboBox#TypeSelector QAbstractItemView {
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    background: white;
    selection-background-color: #eef2ff;
    selection-color: #4361ee;
    outline: none;
}
```

---

## 附录 C：Web 前端核心代码结构

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, 
          maximum-scale=1.0, user-scalable=no">
    <title>ClassPush · 发送消息</title>
    <style>
        /* 内嵌CSS，不依赖CDN */
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .card {
            background: rgba(255,255,255,0.95);
            border-radius: 20px;
            padding: 24px;
            max-width: 480px;
            margin: 0 auto;
            box-shadow: 0 20px 60px rgba(0,0,0,0.15);
        }
        /* ...完整样式... */
    </style>
</head>
<body>
    <div class="card"><!-- 表单内容 --></div>
    <script>
        /* 内嵌JS */
        // 表单提交 → fetch POST /api/messages
        // 发送人自动保存到 localStorage
        // 成功后绿色 toast 提示
        // 最近发送列表自动刷新
    </script>
</body>
</html>
```

---

## 附录 D：关键交互流程图

### D.1 老师手机发消息完整流程

```
老师打开手机浏览器
    │
    ├─ 方式1: 扫描大屏二维码
    │   └─ 自动打开 http://192.168.x.x:8080
    │
    ├─ 方式2: 手动输入地址 (之前保存的书签)
    │
    └─ 方式3: 浏览器历史记录
            │
            ▼
    Web 发送页面加载 (<1秒, 局域网无延迟)
            │
            ├─ "您的称呼" 自动填入上次的名字
            │
            ▼
    选择消息类型 (默认"通知")
    输入消息内容
    点击 [发送]
            │
            ▼
    手机显示 "✓ 发送成功!" (绿色 toast)
            │
            ▼
    大屏 0.3 秒内弹出新消息 (遮罩+卡片动画)
    🔔 "叮咚" 提示音响起
    全班同学抬头看
            │
            ▼
    8秒后自动收起到侧栏 (或老师走到大屏点击"知道了")
```

### D.2 老师在大屏电脑直接发消息流程

```
按 Ctrl+Shift+M (或双击托盘图标)
    │
    ▼
控制台窗口弹出
    │
    ├─ 已自动填好发送人 (上次记住的)
    │
    ▼
输入消息内容
按 Ctrl+Enter (或点击发送按钮)
    │
    ▼
发送按钮变绿 "✓ 已发送"
控制台自动最小化 (可选)
    │
    ▼
大屏立即弹出消息
```

---

> **本文档版本**: v1.0
> **最后更新**: 2026-03-29
> **设计原则**: 简单 > 功能多 > 酷炫。优先保证核心功能完美运行。