# ClassPush

ClassPush 是一个功能丰富的桌面消息推送与显示系统。它能在桌面端提供精美的悬浮消息通知（Overlay Window），同时内置了一个轻量级的 Web 服务器，允许用户通过局域网网页端（或扫码）远程发送和管理屏幕消息。非常适合教室、会议室、展厅等需要向大屏幕或公共屏幕推送通知的场景。

## Structure

- `main.py` / `app.py`: 项目的主入口文件。
- `ui/`: 桌面端 GUI 组件，包含悬浮窗、托盘图标、控制面板及各类定制化 Widget（如动画按钮、进度条等）。
- `web/`: 内置 Web 服务的路由、HTML 模板及静态文件。
- `core/`: 核心逻辑组件，包括配置管理 (`config_manager.py`)、数据库 (`database.py`) 和调度器 (`scheduler.py`)。
- `animations/`: 丰富的 UI 动画效果实现（如滑动、渐显、错落动画等）。
- `utils/`: 实用工具库，包含网络工具、二维码生成、日志与单例运行限制。

## Installation & Usage

1. **Clone the repository**
   ```bash
   git clone https://github.com/xxtg666/ClassPush
   cd ClassPush
   ```

2. **Install dependencies**
   确保你已经安装了 Python (推荐 3.13+)。
   ```bash
   pip install -r requirements.txt
   ```

3. **Run**
   ```bash
   python main.py
   ```