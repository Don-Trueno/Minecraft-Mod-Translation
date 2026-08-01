# 自动同步脚本说明

## 参数
- `PARA_TOKEN` (secret): ParaTranz API token
- `PARA_PROJECT_ID` (secret): ParaTranz 项目 ID

## 工作流
- `.github/workflows/translation-sync.yml`：
  - 在 `push` 时会把源文件（`projects/.../manual/en_us/*.json`）上传到 ParaTranz，上传到远程路径 `immersiveengineering/1.21/manual/en_us/`（使用 `github2para.py`）。
  - 定时（每日）或手动触发时，会从 ParaTranz 拉取翻译并写入 `projects/.../manual/zh_cn/`。

## 本地运行步骤
- 拉取并写入 JSON：
  - `python .github/scripts/para2github.py`
- 从 `projects/.../manual/zh_cn/` 生成 TXT：
  - `python src/ie_manuals.py`

## 手动配置步骤（必须）
- 在仓库 `Settings → Secrets` 中添加 `PARA_TOKEN` 和 `PARA_PROJECT_ID`。