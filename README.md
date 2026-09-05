# Megan 艺术作品集

零付费、零第三方运行依赖的静态作品集网站，支持六个系列、不同尺寸比例的 PNG、系列筛选、大图预览、个人介绍与联系方式。

## 本地预览

项目只使用 Python 标准库生成发布目录：

```bash
python build.py
python -m http.server 4173 --directory _site
```

然后访问 `http://localhost:4173`。不要直接双击 `index.html`，浏览器会限制本地 JSON 读取。

## 可视化维护内容

仓库根目录的 `.pages.yml` 已配置 Pages CMS。项目推送到 GitHub 后：

1. 打开 `https://app.pagescms.org`。
2. 使用 GitHub 登录并授权目标仓库。
3. 在“作品”中新增作品、上传图片、调整顺序或公开状态。
4. 在“系列”中维护六个系列。
5. 在“个人资料与网站文字”中替换 Megan 占位资料和联系方式。
6. 保存后 Pages CMS 会提交到 GitHub，GitHub Pages 自动重新生成并发布网站。

源内容位于：

- `content/works/`：每件作品一个 JSON 文件，适合维护 72 张及更多作品
- `content/series/`：每个系列一个 JSON 文件
- `content/site.json`：个人资料和联系方式
- `images/works/`：真实作品图片
- `artwork-metadata-template.txt`：72 件作品的资料填写模板

当前作品资料使用占位名称。后续可以直接编辑 `artwork-metadata-template.txt`，填写作品名、尺寸、媒介、年份、图片说明和作品介绍，再交给 WorkBuddy 批量同步。

`build.py` 会把内容汇总到 `_site/content/`，同时复制页面、样式和图片。`_site/` 是生成结果，不需要手动编辑。

## GitHub Pages 发布

1. 将此目录推送到 GitHub 仓库的 `main` 分支。
2. 打开仓库 `Settings → Pages`。
3. 将 Source 设为 `GitHub Actions`。
4. `.github/workflows/deploy.yml` 使用 GitHub 自带的 Python 运行 `build.py`，再发布 `_site/`。

如果仓库名为 `用户名.github.io`，网址为 `https://用户名.github.io`；其他仓库名也可正常工作。以上流程均可免费使用。

## 图片适配

- PNG 可直接上传，不要求统一尺寸或比例。
- `layout` 可选择保留原始比例、横版、竖版或方形。
- 画廊使用 `object-fit: contain`，不会裁掉作品内容。
- 移动端始终优先按真实比例展示。
- 非首屏图片启用浏览器原生懒加载，适合当前 72 张作品。
