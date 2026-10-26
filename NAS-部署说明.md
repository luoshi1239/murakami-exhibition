# 村上春树文学展览｜NAS 部署说明

## 目录结构

保持下面的结构整体上传到 NAS 的静态网站目录，不要拆开：

```text
村上春树展览/
├── index.html
├── murakami-exhibition.html（备用入口，可删除）
├── assets/
│   └── epub.min.js
└── 村上春树书单/
    ├── *.epub
    ├── *.mobi
    ├── *.pdf
    └── 其他书籍与封面文件
```

## 部署方式

1. 在 NAS 上启用 Web Station、Nginx、Apache、Caddy 或其他静态文件服务。
2. 将整个 `村上春树展览` 文件夹上传到站点根目录。
3. 通过 NAS 或 Cloudflare Pages 的根地址访问：

```text
https://你的项目.pages.dev/
```

如果直接访问备用页面，则是：

```text
https://你的项目.pages.dev/murakami-exhibition.html
```

## 重要要求

- 必须通过 NAS 的 `http://` 或 `https://` 地址访问。
- 不要直接双击 HTML 用 `file://` 打开，否则浏览器可能阻止 EPUB.js 读取书籍压缩包。
- 不要改变 `assets/` 和 `村上春树书单/` 的相对位置。
- NAS 的 URL 编码应支持中文文件名；如果 NAS 反向代理对中文路径处理异常，可以将书籍文件名改为英文或数字文件名，并同步修改 HTML 中的相对链接。
- 页面不需要数据库、Node.js、PHP 或 Python 后端。
- `assets/epub.min.js` 已经本地化，不依赖外部 CDN。

## 阅读功能

- EPUB：支持页面内阅读、上一页、下一页。
- EPUB：支持从作品卡片打开，也支持阅读区手动选择本地文件。
- MOBI、PDF、AZW3：保留下载入口；当前页面阅读器只渲染 EPUB。
- 书籍链接均指向本文件夹内的相对路径。

## NAS 检查清单

- [ ] `murakami-exhibition.html` 能通过 NAS 地址打开
- [ ] `assets/epub.min.js` 返回 200
- [ ] 任意 EPUB 文件能通过 NAS 地址返回 200
- [ ] 点击作品卡片后可以打开网页阅读
- [ ] 浏览器控制台没有 CORS 或 404 错误
- [ ] 中文文件名在 NAS Web 服务中可以正常访问
