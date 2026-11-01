package org.qingdao.offlinemap.colorful;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.res.AssetFileDescriptor;
import android.graphics.Color;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.FrameLayout;
import android.widget.ImageButton;
import android.widget.LinearLayout;
import android.widget.TextView;

import org.mapsforge.core.model.LatLong;
import org.mapsforge.core.model.MapPosition;
import org.mapsforge.core.model.BoundingBox;
import org.mapsforge.core.model.Point;
import org.mapsforge.core.model.Rotation;
import org.mapsforge.core.util.Parameters;
import org.mapsforge.core.graphics.Canvas;
import org.mapsforge.map.android.graphics.AndroidGraphicFactory;
import org.mapsforge.map.android.graphics.AndroidPaint;
import org.mapsforge.map.android.view.MapView;
import org.mapsforge.map.layer.Layer;
import org.mapsforge.map.layer.renderer.TileRendererLayer;
import org.mapsforge.map.reader.MapFile;

import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;

/** Entirely local vector-map viewer, for conventional Android phones and tablets. */
public final class MainActivity extends Activity {
    private static final int REQUEST_SEARCH = 10;
    private static final double QINGDAO_LAT = 36.0671;
    private static final double QINGDAO_LON = 120.3826;
    private static final int BLACK = 0xff1e293b;
    private static final int ACCENT = 0xff2563eb;
    private static final int WHITE = 0xfff8fafc;

    private FrameLayout mapHost;
    private TextView loading;
    private MapView mapView;
    private TextView pin;
    private ViewportTileCache tileCache;
    private TileRendererLayer renderLayer;
    private boolean dataReady;
    private boolean destroyed;
    private double preservedLat = Double.NaN;
    private double preservedLon = Double.NaN;
    private byte preservedZoom = 12;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        getWindow().setFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN,
                WindowManager.LayoutParams.FLAG_FULLSCREEN);
        getWindow().setNavigationBarColor(WHITE);
        getWindow().getDecorView().setSystemUiVisibility(View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR);
        AndroidGraphicFactory.createInstance(getApplicationContext());
        AndroidPaint.installTypeface(FontUtil.regular(this), FontUtil.semibold(this));
        Parameters.NUMBER_OF_THREADS = Math.max(2, Math.min(4, Runtime.getRuntime().availableProcessors()));
        Parameters.ANDROID_32BIT_COLOR = true;
        Parameters.SQUARE_FRAME_BUFFER = false;
        Parameters.FRACTIONAL_ZOOM = true;
        makeUi();
        readLastPosition();
        loading.setText("正在载入离线地图…");
        new Thread(() -> {
            try {
                copyAssetIfNeeded("data/qingdao.map", "qingdao.map");
                copyAssetIfNeeded("data/qingdao.db", "qingdao.db");
                runOnUiThread(() -> {
                    if (!destroyed) {
                        dataReady = true;
                        openMap();
                    }
                });
            } catch (Exception ex) {
                runOnUiThread(() -> {
                    if (!destroyed) {
                        loading.setText("地图载入失败");
                        new AlertDialog.Builder(this).setTitle("无法打开离线数据")
                                .setMessage(ex.getMessage()).setPositiveButton("确定", null).show();
                    }
                });
            }
        }, "offline-data-init").start();
    }

    private int dp(int d) {
        return (int) (d * getResources().getDisplayMetrics().density + .5f);
    }

    private GradientDrawable box(boolean filled) {
        GradientDrawable d = new GradientDrawable();
        d.setColor(filled ? ACCENT : Color.WHITE);
        d.setStroke(dp(1), 0xffdbe3ef);
        d.setCornerRadius(dp(12));
        return d;
    }

    private GradientDrawable overlayBox() {
        GradientDrawable d = new GradientDrawable();
        d.setColor(0xb3ffffff);
        d.setStroke(dp(1), 0xffdbe3ef);
        d.setCornerRadius(dp(12));
        return d;
    }

    private Button button(String caption) {
        Button b = new Button(this);
        b.setAllCaps(false);
        b.setText(caption);
        b.setTextSize(17);
        b.setTextColor(ACCENT);
        b.setTypeface(FontUtil.semibold(this));
        b.setBackground(new android.graphics.drawable.RippleDrawable(
                android.content.res.ColorStateList.valueOf(0x332563eb), box(false), null));
        b.setMinHeight(dp(48));
        b.setPadding(dp(10), 0, dp(10), 0);
        return b;
    }

    private void makeUi() {
        FrameLayout root = new FrameLayout(this);
        root.setBackgroundColor(WHITE);
        setContentView(root);
        mapHost = new FrameLayout(this);
        mapHost.setBackgroundColor(WHITE);
        root.addView(mapHost, new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));

        loading = new TextView(this);
        loading.setTextColor(BLACK);
        loading.setTextSize(18);
        loading.setTypeface(FontUtil.regular(this));
        loading.setGravity(Gravity.CENTER);
        root.addView(loading, new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));

        LinearLayout top = new LinearLayout(this);
        top.setGravity(Gravity.CENTER_VERTICAL);
        ImageButton search = iconButton(R.drawable.ic_search, "搜索");
        search.setOnClickListener(v -> {
            if (!dataReady) return;
            startActivityForResult(new Intent(this, SearchActivity.class), REQUEST_SEARCH);
        });
        top.addView(search, new LinearLayout.LayoutParams(dp(44), dp(44)));
        ImageButton settings = iconButton(R.drawable.ic_settings, "设置");
        settings.setOnClickListener(v -> MapSettings.show(this, this::reloadTheme));
        LinearLayout.LayoutParams sp = new LinearLayout.LayoutParams(dp(44), dp(44));
        sp.leftMargin = dp(6);
        top.addView(settings, sp);
        FrameLayout.LayoutParams topPosition = new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.WRAP_CONTENT, dp(44), Gravity.TOP | Gravity.END);
        topPosition.topMargin = dp(8);
        topPosition.rightMargin = dp(8);
        root.addView(top, topPosition);

        LinearLayout actions = new LinearLayout(this);
        actions.setGravity(Gravity.CENTER_VERTICAL);
        Button overview = button("全图");
        overview.setTextSize(15);
        overview.setMinHeight(0);
        overview.setBackground(overlayBox());
        overview.setOnClickListener(v -> centerOn(new LatLong(36.30, 120.54), (byte) 8));
        actions.addView(overview, new LinearLayout.LayoutParams(dp(62), dp(40)));
        Button minus = button("－");
        minus.setTextSize(20);
        minus.setMinHeight(0);
        minus.setBackground(overlayBox());
        minus.setOnClickListener(v -> zoomBy(-1));
        LinearLayout.LayoutParams mp = new LinearLayout.LayoutParams(dp(40), dp(40));
        mp.leftMargin = dp(4);
        actions.addView(minus, mp);
        Button plus = button("＋");
        plus.setTextSize(20);
        plus.setMinHeight(0);
        plus.setBackground(overlayBox());
        plus.setOnClickListener(v -> zoomBy(1));
        LinearLayout.LayoutParams pp = new LinearLayout.LayoutParams(dp(40), dp(40));
        pp.leftMargin = dp(4);
        actions.addView(plus, pp);
        FrameLayout.LayoutParams actionPosition = new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.WRAP_CONTENT, dp(40), Gravity.RIGHT | Gravity.BOTTOM);
        actionPosition.rightMargin = dp(8);
        actionPosition.bottomMargin = dp(25);
        root.addView(actions, actionPosition);

        TextView credit = new TextView(this);
        credit.setText("© OpenStreetMap 贡献者 · Overture Maps Foundation · ODbL");
        credit.setTextColor(0xcc334155);
        credit.setTextSize(9);
        credit.setTypeface(FontUtil.regular(this));
        credit.setBackgroundColor(0x66ffffff);
        credit.setPadding(dp(3), 0, dp(3), 0);
        credit.setGravity(Gravity.CENTER_VERTICAL);
        FrameLayout.LayoutParams creditPosition = new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.WRAP_CONTENT, dp(18), Gravity.LEFT | Gravity.BOTTOM);
        creditPosition.leftMargin = dp(4);
        creditPosition.bottomMargin = dp(2);
        root.addView(credit, creditPosition);
    }

    private ImageButton iconButton(int drawable, String description) {
        ImageButton button = new ImageButton(this);
        button.setImageResource(drawable);
        button.setImageTintList(android.content.res.ColorStateList.valueOf(ACCENT));
        button.setScaleType(ImageButton.ScaleType.CENTER_INSIDE);
        button.setPadding(dp(10), dp(10), dp(10), dp(10));
        button.setContentDescription(description);
        button.setBackground(new android.graphics.drawable.RippleDrawable(
                android.content.res.ColorStateList.valueOf(0x332563eb), overlayBox(), null));
        return button;
    }

    private void copyAssetIfNeeded(String asset, String name) throws Exception {
        long expected;
        try (AssetFileDescriptor afd = getAssets().openFd(asset)) {
            expected = afd.getLength();
        }
        File target = new File(getFilesDir(), name);
        if (target.isFile() && target.length() == expected) return;
        File temp = new File(getFilesDir(), name + ".partial");
        try (InputStream in = getAssets().open(asset); FileOutputStream out = new FileOutputStream(temp)) {
            byte[] buffer = new byte[64 * 1024];
            int n;
            while ((n = in.read(buffer)) != -1) out.write(buffer, 0, n);
            out.getFD().sync();
        } catch (Exception e) {
            temp.delete();
            throw e;
        }
        if (temp.length() != expected) throw new IllegalStateException(name + " 文件不完整");
        if (target.exists() && !target.delete()) throw new IllegalStateException("旧版地图无法替换");
        if (!temp.renameTo(target)) throw new IllegalStateException("离线数据保存失败");
    }

    private void readLastPosition() {
        SharedPreferences p = getPreferences(MODE_PRIVATE);
        if (p.contains("lat")) {
            preservedLat = Double.longBitsToDouble(p.getLong("lat", 0));
            preservedLon = Double.longBitsToDouble(p.getLong("lon", 0));
            preservedZoom = (byte) p.getInt("zoom", 12);
        }
    }

    private void rememberPosition() {
        if (mapView == null) return;
        LatLong c = mapView.getModel().mapViewPosition.getCenter();
        if (c == null) return;
        preservedLat = c.latitude;
        preservedLon = c.longitude;
        preservedZoom = mapView.getModel().mapViewPosition.getZoomLevel();
        getPreferences(MODE_PRIVATE).edit()
                .putLong("lat", Double.doubleToLongBits(preservedLat))
                .putLong("lon", Double.doubleToLongBits(preservedLon))
                .putInt("zoom", preservedZoom).apply();
    }

    private void openMap() {
        if (!dataReady || destroyed) return;
        try {
            MapSettings settings = MapSettings.get(this);
            Parameters.PARENT_TILES_RENDERING = Parameters.ParentTilesRendering.SPEED;
            mapView = new MapView(this);
            // Mapsforge reuses its double-buffer bitmaps after drawing; software Canvas avoids
            // asynchronous hardware-texture uploads reading a bitmap while it is reused.
            mapView.setLayerType(View.LAYER_TYPE_SOFTWARE, null);
            mapView.getModel().displayModel.setFixedTileSize(256);
            mapView.setBuiltInZoomControls(false);
            mapView.setZoomLevelMin((byte) 8);
            mapView.setZoomLevelMax((byte) 19);
            mapHost.addView(mapView, new FrameLayout.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));

            MapFile file = new MapFile(new File(getFilesDir(), "qingdao.map"));
            mapView.getModel().mapViewPosition.setMapLimit(file.getMapFileInfo().boundingBox);
            tileCache = new ViewportTileCache();
            renderLayer = new TileRendererLayer(tileCache, file,
                    mapView.getModel().mapViewPosition, false, true, false, AndroidGraphicFactory.INSTANCE);
            renderLayer.setTextScale(settings.textScale());
            renderLayer.setXmlRenderTheme(ThemeManager.createTheme(this, settings));
            mapView.getLayerManager().getLayers().add(renderLayer);
            mapView.getLayerManager().getLayers().add(new Layer() {
                @Override public void draw(BoundingBox bounds, byte zoom, Canvas canvas,
                                           Point topLeft, Rotation rotation) { }
                @Override public boolean onLongPress(LatLong location, Point layerXY, Point tapXY) {
                    Intent nearby = new Intent(MainActivity.this, SearchActivity.class);
                    nearby.putExtra(SearchActivity.EXTRA_CENTER_LAT, location.latitude);
                    nearby.putExtra(SearchActivity.EXTRA_CENTER_LON, location.longitude);
                    startActivityForResult(nearby, REQUEST_SEARCH);
                    return true;
                }
            });
            LatLong center = Double.isNaN(preservedLat) ?
                    new LatLong(QINGDAO_LAT, QINGDAO_LON) : new LatLong(preservedLat, preservedLon);
            mapView.getModel().mapViewPosition.setMapPosition(
                    new MapPosition(center, preservedZoom), false);
            loading.setVisibility(View.GONE);
        } catch (Exception e) {
            loading.setText("地图打开失败");
            loading.setVisibility(View.VISIBLE);
            new AlertDialog.Builder(this).setTitle("地图无法显示")
                    .setMessage(e.toString()).setPositiveButton("确定", null).show();
        }
    }

    private void reloadTheme() {
        if (!dataReady || mapView == null) return;
        rememberPosition();
        mapView.destroyAll();
        mapHost.removeView(mapView);
        mapView = null;
        renderLayer = null;
        tileCache = null;
        pin = null;
        openMap();
    }

    private void zoomBy(int delta) {
        if (mapView == null) return;
        int old = mapView.getModel().mapViewPosition.getZoomLevel();
        int next = Math.max(8, Math.min(19, old + delta));
        mapView.getModel().mapViewPosition.setZoomLevel((byte) next, true);
    }

    private void centerOn(LatLong where, byte zoom) {
        if (mapView == null) return;
        mapView.getModel().mapViewPosition.setMapPosition(new MapPosition(where, zoom), true);
    }

    @Override protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode != REQUEST_SEARCH || resultCode != RESULT_OK || data == null || mapView == null) return;
        double lat = data.getDoubleExtra("lat", Double.NaN);
        double lon = data.getDoubleExtra("lon", Double.NaN);
        if (Double.isNaN(lat) || Double.isNaN(lon)) return;
        String name = data.getStringExtra("name");
        LatLong target = new LatLong(lat, lon);
        centerOn(target, (byte) Math.max(16, mapView.getModel().mapViewPosition.getZoomLevel()));
        if (pin != null) mapView.removeView(pin);
        pin = new TextView(this);
        pin.setText("◆");
        pin.setTextSize(27);
        pin.setTextColor(0xffef4444);
        pin.setTypeface(FontUtil.semibold(this));
        pin.setBackground(box(false));
        pin.setPadding(dp(3), 0, dp(3), 0);
        mapView.addView(pin, new MapView.LayoutParams(
                ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT,
                target, MapView.LayoutParams.Alignment.BOTTOM_CENTER));
        pin.setContentDescription(name == null ? "搜索结果" : name);
    }

    @Override protected void onPause() {
        rememberPosition();
        super.onPause();
    }

    @Override protected void onDestroy() {
        destroyed = true;
        if (mapView != null) {
            mapView.destroyAll();
            mapView = null;
        }
        super.onDestroy();
    }
}
