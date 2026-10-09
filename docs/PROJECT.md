# Kerinol.C

个人网站与 GitHub Profile 展示项目。使用用户提供的动漫头像，绿色 CRT、点阵、扫描线与终端排版参考 `Zynoo71-master.zip`。头像风格迁移由内置 imagegen 生成；动画生成器为独立 Pillow 实现，没有复制参考包的 Python 源码。

## 项目结构

- `dist/`：可直接部署的静态网站，原生 HTML、CSS、JavaScript，无前端依赖。
- `assets/neofetch.gif`：GitHub README 使用的循环动画。
- `assets/portrait-crt.gif`：独立动态头像，包含发梢飘动、轻微呼吸与墨镜反光。
- `assets/neofetch.png`：静态展示与减少动态效果模式。
- `tools/avatar.png`：用户原始头像，仅转换为 PNG。
- `tools/portrait-crt.png`：头像风格迁移后的绿色点阵素材。
- `tools/generate_profile.py`：使用 Pillow 生成 GIF、静态图与 ASCII 字符文本。
- `profile/README.md`：同步到 `yuzigewmy/yuzigewmy` 根目录的 Profile README。

## 本地查看

```powershell
cd D:\Kerinol.C
python -m http.server 8765 --bind 127.0.0.1 --directory dist
```

打开 `http://127.0.0.1:8765`。网站终端支持 `help`、`about`、`whoami`、`projects`、`github`、`neofetch`、`clear`；命令是本地展示功能，不执行系统指令。支持键盘操作、手机布局、光效切换、动画暂停与系统减少动态效果偏好。

重新生成头像动画（已有 Pillow）：

```powershell
python tools/generate_profile.py --source tools/avatar.png --portrait tools/portrait-crt.png --output work/render
```

输出在 `work/render/assets/`，其中 GIF、PNG 可复制到 `assets/` 和 `dist/assets/`；该工作目录不会上传到 GitHub。

## 展示内容

名称为 `Kerinol.C`，GitHub 账号为 `yuzigewmy`。公开项目链接与说明来自该账号的公开仓库；Fork 项目明确标识。没有添加未经确认的工作经历、技术熟练度、账户配额或生产力指标。公开邮箱未写入网站。

## 参考与素材

视觉参考来自用户提供的 `Zynoo71-master.zip` 与 GitHub Profile 截图。参考包没有附带许可证，本项目不声明其源码具有已确认的开源许可，也不为参考作品、用户头像或生成素材增加不实的版权归属声明。

风格迁移提示词：保留原角色尖刺头发、太阳镜、脸颊疤痕与双手调整眼镜的姿势，以黑绿背景、浅绿色 CRT 荧光、清晰的字符点阵、横向扫描线和轻微辉光制作方形肖像，不添加文字、数字、边框、标识或其他人物。
