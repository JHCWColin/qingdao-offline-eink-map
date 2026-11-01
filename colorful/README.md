# 青岛离线地图 · V1.1.0 Colorful

面向普通 Android 手机和平板的独立子项目，最低 Android 8.1（API 27），可与墨水屏版同时安装。

- 包名 / Java 命名空间：`org.qingdao.offlinemap.colorful`
- 版本：`1.1.0 Colorful`，versionCode `2`
- 发布：标签 `v1.1.0-colorful`，标题 `V1.1.0 Colorful`
- 显示：无数据区域与水域统一使用海洋蓝色；海洋自然保护区边界不强制刷成陆地绿，公园和林地仍保持绿色。另有分级道路颜色、彩色分类图标和标签；搜索、详情、设置及系统栏统一彩色风格。
- 交互：32 位 ARGB、连续双指缩放、缩放/跳转动画、父级瓦片过渡、按 CPU 设置 2–4 个渲染线程。移除墨水屏模式和黑白对比度设置。
- 地图铺满屏幕内容区并隐藏状态栏。顶部标题与白色衬底已移除；搜索、设置在右上角以 44dp 半透明图标显示，来源署名使用更淡的半透明底色。
- 保留：中文/拼音搜索、分类、详情、长按附近、只保留路名、分类图层、标签大小、苹方字体及 V1.1.0 视口缓存修复。完全离线，无网络权限。

## 构建

从仓库根目录执行，JDK/本机临时目录配置见根目录 README：

```powershell
.\gradlew.bat :colorful:testDebugUnitTest :colorful:lint :colorful:assembleRelease
adb install -r colorful\build\outputs\apk\release\colorful-release.apk
adb shell am start -n org.qingdao.offlinemap.colorful/.MainActivity
```

正式 APK：`colorful/build/outputs/apk/release/colorful-release.apk`。签名沿用根目录私有 `.local/signing.properties`，不要提交密钥。两个包名不同，数据和设置相互独立，不会覆盖原版。

构建任务 `syncOfflineAssets` 将 `app/src/main/assets/data/` 与 `fonts/` 同步到生成目录后打包，避免在 Git 中重复保存大文件。彩色主题和 SVG 图标完整保存在本模块；可运行 `python tools/build_colorful_theme.py` 重新生成。

地图视图保留软件 Canvas：这是 V1.1.0 规避 Mapsforge 位图复用与异步纹理上传冲突的兼容性修复，不是墨水屏刷新策略。外围界面使用正常硬件加速；缩放动画与彩色渲染独立开启。

第三方数据、字体和库的许可说明见根目录 `THIRD_PARTY_NOTICES.md`；维持现有仓库可见性。
