# 青岛离线地图

本仓库包含两个可同时安装的 Android 子项目：

| 子项目 | 适用设备 | APK 包名 | 版本 |
| --- | --- | --- | --- |
| `app` | 墨水屏阅读器 | `org.qingdao.offlinemap` | 1.1.0 |
| [`colorful`](colorful/README.md) | 普通手机和平板 | `org.qingdao.offlinemap.colorful` | 1.1.0 Colorful |

彩色版源码、界面和主题保存在 `colorful/`，构建时复用原版离线数据、字体及渲染 JAR。两款应用的设置、缓存和私有数据目录独立。

## 墨水屏版

专为 758×1024、212 dpi、Android 8.1、armeabi-v7a、约 1 GB 内存的小米阅读器制作的**完全离线**地图。首次启动从 APK 解包本地矢量地图与检索数据库，此后地图、搜索和详情均不联网；应用清单不申请 `INTERNET` 权限。

## 功能

- 青岛市各区市的道路、路名、行政边界、街道、公共设施、商业/餐饮地点、公交和轨道站点等矢量图层；地图支持平移、双指缩放、双击及屏幕按钮缩放。
- 中文和拼音离线搜索、分类浏览、地点详情、关联道路和公交线路；地图上长按可查看附近地点。暂无路径规划或实时导航。
- 设置中可暂时隐藏店名，或启用“只保留路名”；还可分别切换店铺、餐饮、公共设施、交通、建筑、水域、行政边界等图层与名称，调节标签大小、黑白对比度和墨水屏模式。
- 地图铺满内容区，搜索和设置浮在顶部；小型半透明全图/缩放按钮浮在右下角，不占用底图高度。
- 界面与地图标签均使用用户提供的 PingFang SC Regular / Semibold。Mapsforge Android 渲染器的字体入口已在 `tools/src/mapsforge-map-android/` 中修改，并编入 `app/libs/mapsforge-map-android-0.25.0-pingfang.jar`。

## 本地数据

`app/src/main/assets/data/qingdao.map` 是约 17 MB 的 Mapsforge 矢量底图；`qingdao.db` 是约 20 MB 的只读 SQLite 搜索与详情库。数据库内共有 27,176 条要素：157 个行政区域、4,055 个地名、3,911 条合并道路、15,444 个兴趣点、2,347 个站点、489 条交通线路、590 个地址和 183 条水路/轨道线。构建日期记录为 **2026-11-01**。

原始数据来自 OpenStreetMap 的山东省提取数据，以及 Overture Maps 2026-10-21.0 的 Places 数据；处理脚本在 `tools/`，中间产物在 `data/`。地图和数据库取决于源数据覆盖率，不能保证每条新开道路或每家店铺均已收录。界面显示 OpenStreetMap 与 Overture 署名；发布衍生数据时还应遵守相应数据许可。

## 构建与安装

需要 JDK 17 或 21、Android SDK Platform 35，以及项目自带的 Gradle 8.9 wrapper。Windows 上在项目根目录执行（本机的中文临时目录会触发 Gradle Java IPC 错误，故使用短 ASCII 临时路径）：

```powershell
$env:JAVA_HOME = 'D:/AndroidStudio.backup-20261031/jbr' # 本机 JDK 21；也可换成自己的 JDK 17/21
$env:TEMP = 'D:/tmp'
$env:TMP = 'D:/tmp'
$env:JAVA_TOOL_OPTIONS = '-Djava.io.tmpdir=D:/tmp -Dfile.encoding=COMPAT'
.\gradlew.bat :app:assembleDebug
adb install -r app\build\outputs\apk\debug\app-debug.apk
adb shell am start -n org.qingdao.offlinemap/.MainActivity
```

调试 APK 位于 `app/build/outputs/apk/debug/app-debug.apk`。应用最低 API 27，目标 API 28，首次启动会将打包的地图和数据库复制到应用私有目录，不需要外置存储权限。矢量瓦片采用 256 px 和 2 个渲染工作线程；V1.1.0 起内存缓存按实际帧缓冲工作集自动扩容至两倍（最低 24 张），避免可见瓦片反复淘汰造成破图和闪烁。地图使用软件 Canvas；墨水屏模式减少中间瓦片重绘。

缓存回归测试：`./gradlew.bat :app:testDebugUnitTest`，涵盖原始 24 张缓存无法完成整帧、不同分辨率、旧任务完成和视口扩大场景。

正式 APK 通过 `./gradlew.bat :app:assembleRelease` 生成于 `app/build/outputs/apk/release/app-release.apk`。签名材料存放在 Git 忽略的 `.local/qingdao-release.p12` 和 `.local/signing.properties`；请**私下备份两者**，否则后续无法使用相同签名更新。已安装的调试版与正式版签名不同，首次切换时须先卸载调试版。

## 数据重建

地图已打包到 APK，普通安装无需重新下载数据。若需更新底图，先获取新的山东 OSM PBF 和 Overture Places 数据，按 `tools/build_boundaries.py`、`tools/build_sea.py`、`tools/build_data.py`、`tools/write_map.sh` 的顺序重建，再把 `data/out/qingdao.map` 与 `qingdao.db` 复制到 `app/src/main/assets/data/` 并提升 `versionCode`。Python 脚本使用 `osmium`、`shapely`、`pypinyin`、`opencc`、`duckdb` 等依赖。地图写入脚本还需自行下载 Osmosis 0.49.2 至 `tools/osmosis-0.49.2/`，并将 Mapsforge 0.25.0 的 `mapsforge-map-writer-0.25.0-jar-with-dependencies.jar` 放进其 `lib/default/`；这两个第三方工具二进制不纳入 Git。

PingFang SC 字体来自用户本地的 `D:/PingFang-main.zip`。该压缩包自述文件没有授予重新分发许可；若要对外发布带字体的 APK，请先确认字体使用与分发权利。

第三方数据、渲染库和图标的署名说明见 `THIRD_PARTY_NOTICES.md`。
