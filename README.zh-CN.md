# Video Editing Skills

[English](README.md) | **简体中文**

一套可复用的 [Cursor Skills](https://cursor.com/docs/agent/skills),用于 AI 辅助的视频剪辑工作流。把这些技能丢进任意项目,你的编码 Agent(Cursor、Claude Code,或任意兼容 MCP 的工具)就能端到端地驱动整条剪辑流水线。

每个技能都是一个自包含的 Markdown 文件(可选附带模板脚本和真实示例),教 Agent 如何完成某一类视频任务:剪辑拼接、卡点配乐、给录屏加高亮框等等。

---

## 可用技能

| 技能 | 功能 | 适用场景 |
|------|------|----------|
| [`video-editing-workflow`](.cursor/skills/video-editing-workflow/SKILL.md) | 切割、修剪、拼接素材;制作混剪;按节拍同步 BGM;添加转场;输出指定分辨率。 | 旅行视频、混剪、多素材配乐剪辑。 |
| [`video-annotation-workflow`](.cursor/skills/video-annotation-workflow/SKILL.md) | 给已有视频添加动态高亮框、字幕、暗化遮罩等标注。内置坐标网格调试模式,方便你和 Agent 快速对齐框位置。 | 产品演示、教程、功能 walkthrough、录屏讲解。 |

两个技能共用同一个 conda 环境(`video_edit`)和 FFmpeg 二进制(`static-ffmpeg`)。

---

## 在你的项目中安装这些技能

Cursor 等 Agent 工具会自动从 `.cursor/skills/`(项目级)或 `~/.cursor/skills/`(用户级)发现技能。按需选择作用范围。

### 方案 A —— 直接基于本仓库起步

```bash
git clone https://github.com/zhangdah/Video-Editing-Skills.git my-video-project
cd my-video-project
# 按你的平台修改 mcp.json 中的路径(见下文),把素材丢进去就能开干。
```

### 方案 B —— 把单个技能复制进已有项目

```bash
# 在你的项目根目录:
mkdir -p .cursor/skills
cp -R /path/to/Video-Editing-Skills/.cursor/skills/video-annotation-workflow .cursor/skills/
```

### 方案 C —— 安装为个人(用户级)技能

```bash
mkdir -p ~/.cursor/skills
cp -R .cursor/skills/* ~/.cursor/skills/
```

复制完成后,重启 AI 工具让它加载新技能。

---

## 环境配置

所有技能都假设使用同一个共享 conda 环境。

```bash
conda create -n video_edit python=3.11 -y
conda activate video_edit
pip install mcp-video static-ffmpeg librosa numpy yt-dlp opencv-python pillow
conda install -c conda-forge liblzma    # librosa 依赖
```

`static-ffmpeg` 自带 macOS、Linux、Windows 三平台的 `ffmpeg` 和 `ffprobe` 二进制 —— 不需要额外装系统级 FFmpeg。

### MCP Server 配置

仓库自带的 [`.cursor/mcp.json`](.cursor/mcp.json) 注册了 `mcp-video` MCP 服务器。**你必须根据自己的平台和 conda 环境位置修改 `command` 与 `PATH`**:

| 平台 | `command` 示例 | `PATH` 示例 |
|------|----------------|-------------|
| macOS(Apple Silicon) | `~/miniconda3/envs/video_edit/bin/python` | `~/miniconda3/envs/video_edit/lib/python3.11/site-packages/static_ffmpeg/bin/darwin_arm64:$PATH` |
| Linux | `~/miniconda3/envs/video_edit/bin/python` | `~/miniconda3/envs/video_edit/lib/python3.11/site-packages/static_ffmpeg/bin/linux:$PATH` |
| Windows | `C:\Users\<you>\anaconda3\envs\video_edit\python.exe` | `C:\Users\<you>\anaconda3\envs\video_edit\Lib\site-packages\static_ffmpeg\bin\win32;%PATH%` |

修改后重启 AI 工具。让 Agent 对任意视频文件调用一次 `video_info`,确认服务器已启动。

---

## 快速上手示例

技能装好、conda 环境激活后,试试这类提示词:

```
"用 LA/ 和 Hawaii/ 里的素材剪一个 90 秒的卡点混剪。
从 music/ 里挑一首合适的曲子。先输出 1080p,再出 4K。"
```

→ 会触发 `video-editing-workflow`

```
"给 Demo.mp4 加注释:在每次点击的位置加高亮框,并配中文字幕讲解每一步。
打开调试网格,我帮你对齐框的位置。"
```

→ 会触发 `video-annotation-workflow`

Agent 会按技能里规定的分阶段流程执行:收集需求 → 与你确认 → 渲染 → 迭代。

---

## 仓库结构

```
Video-Editing-Skills/
├── README.md
├── README.zh-CN.md
├── .gitignore                          # 忽略视频文件 + 各项目工作目录
├── .cursor/
│   ├── mcp.json                        # MCP 服务器注册(按平台修改)
│   └── skills/
│       ├── video-editing-workflow/
│       │   └── SKILL.md
│       └── video-annotation-workflow/
│           ├── SKILL.md
│           ├── scripts/
│           │   └── annotate_template.py    # 通用渲染器,自定义 CONSTANTS + SEGMENTS
│           └── examples/
│               └── kyc_demo_segments.py    # 真实项目的 SEGMENTS 参考
```

视频素材(`*.mp4`、`*.mov` 等)、各项目脚本、中间产物目录都被 gitignore —— 本仓库只包含可复用的技能本身。

---

## 贡献新技能

1. 创建 `.cursor/skills/<skill-name>/SKILL.md`,带 YAML frontmatter:

   ```markdown
   ---
   name: my-skill-name
   description: >-
     一两句话说明这个技能做什么,以及 Agent 应该在什么场景下调用它
     (包含触发关键词)。
   ---

   # My Skill Name
   ...
   ```

2. `SKILL.md` 控制在 ~500 行以内。长篇参考资料放进同级文件(`reference.md`、`examples/`、`scripts/`)并链过去。

3. 多步骤任务,尤其是涉及用户反馈循环的,采用清晰的分阶段流程。

4. 在上面的"可用技能"表格里加一行。

5. 提 PR。

---

## 许可证

MIT —— 自由使用、修改、分发。
