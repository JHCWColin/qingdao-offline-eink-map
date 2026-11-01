package org.qingdao.offlinemap;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Context;
import android.content.SharedPreferences;
import android.content.res.ColorStateList;
import android.graphics.Color;
import android.widget.CheckBox;
import android.widget.LinearLayout;
import android.widget.RadioButton;
import android.widget.RadioGroup;
import android.widget.ScrollView;
import android.widget.TextView;

import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.Map;
import java.util.Set;

/** Persistent, fully offline map presentation choices for the e-ink reader. */
public final class MapSettings {
    private static final String PREFS = "map_settings";
    public static final String ONLY_ROAD_NAMES = "only_road_names";
    public static final String SHOPS = "shops";
    public static final String SHOP_NAMES = "shop_names";
    public static final String FOOD = "food";
    public static final String FOOD_NAMES = "food_names";
    public static final String POIS = "pois";
    public static final String POI_NAMES = "poi_names";
    public static final String TRANSIT = "transit";
    public static final String TRANSIT_NAMES = "transit_names";
    public static final String PLACE_NAMES = "place_names";
    public static final String PATHS = "paths";
    public static final String PATH_NAMES = "path_names";
    public static final String ADDRESSES = "addresses";
    public static final String BUILDINGS = "buildings";
    public static final String BOUNDARIES = "boundaries";
    public static final String LANDUSE = "landuse";
    public static final String RAIL = "rail";
    public static final String WATER = "water";
    public static final String WATER_NAMES = "water_names";
    public static final String HIGH_CONTRAST = "high_contrast";
    public static final String EINK_OPTIMIZED = "eink_optimized";
    public static final String LABEL_SIZE = "label_size";

    private static final String[] KEYS = {
            ONLY_ROAD_NAMES, SHOPS, SHOP_NAMES, FOOD, FOOD_NAMES, POIS, POI_NAMES,
            TRANSIT, TRANSIT_NAMES, PLACE_NAMES, PATHS, PATH_NAMES, ADDRESSES,
            BUILDINGS, BOUNDARIES, LANDUSE, RAIL, WATER, WATER_NAMES,
            HIGH_CONTRAST, EINK_OPTIMIZED
    };
    private static final String[] TITLES = {
            "只保留路名（临时隐藏店名及其他名称）", "显示商店和购物图标", "显示店名",
            "显示餐饮图标", "显示餐饮名称", "显示公共设施图标", "显示公共设施名称",
            "显示公交、地铁等站点", "显示交通站点名称", "显示区、街道和社区名称",
            "显示步行小径", "显示小径名称", "显示门牌号", "显示建筑轮廓",
            "显示行政边界", "显示土地利用", "显示轨道交通线条", "显示水域",
            "显示水域名称", "增强黑白对比度", "墨水屏模式（减少动态效果）"
    };

    private final SharedPreferences prefs;

    private MapSettings(Context context) {
        prefs = context.getApplicationContext().getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }

    public static MapSettings get(Context context) {
        return new MapSettings(context);
    }

    private static boolean defaultFor(String key) {
        return !ONLY_ROAD_NAMES.equals(key) && !HIGH_CONTRAST.equals(key)
                && !PATH_NAMES.equals(key) && !ADDRESSES.equals(key);
    }

    public boolean enabled(String key) {
        return prefs.getBoolean(key, defaultFor(key));
    }

    public boolean onlyRoadNames() { return enabled(ONLY_ROAD_NAMES); }
    public boolean isHighContrast() { return enabled(HIGH_CONTRAST); }
    public boolean isEinkOptimized() { return enabled(EINK_OPTIMIZED); }

    public float textScale() {
        switch (prefs.getInt(LABEL_SIZE, 1)) {
            case 0: return 0.85f;
            case 2: return 1.20f;
            default: return 1.0f;
        }
    }

    /** Categories are deliberately separate for symbols and their captions. */
    public Set<String> categories() {
        Set<String> result = new LinkedHashSet<>();
        result.add("road");
        result.add("roadname");
        if (enabled(PATHS)) result.add("path");
        if (enabled(RAIL)) result.add("rail");
        if (enabled(WATER)) result.add("water");
        if (enabled(LANDUSE)) result.add("landuse");
        if (enabled(BUILDINGS)) result.add("building");
        if (enabled(BOUNDARIES)) result.add("boundary");
        if (onlyRoadNames()) return result;
        if (enabled(PATHS) && enabled(PATH_NAMES)) result.add("pathname");
        if (enabled(RAIL)) result.add("railname");
        if (enabled(WATER) && enabled(WATER_NAMES)) result.add("watername");
        if (enabled(PLACE_NAMES)) result.add("placename");
        if (enabled(ADDRESSES)) result.add("addr");
        if (enabled(POIS)) {
            result.add("poi");
            if (enabled(POI_NAMES)) result.add("poiname");
        }
        if (enabled(SHOPS)) {
            result.add("shop");
            if (enabled(SHOP_NAMES)) result.add("shopname");
        }
        if (enabled(FOOD)) {
            result.add("food");
            if (enabled(FOOD_NAMES)) result.add("foodname");
        }
        if (enabled(TRANSIT)) {
            result.add("transport");
            if (enabled(TRANSIT_NAMES)) result.add("transportname");
        }
        return result;
    }

    private static int dp(Activity a, int value) {
        return (int) (value * a.getResources().getDisplayMetrics().density + .5f);
    }

    private static TextView header(Activity a, String value) {
        TextView v = new TextView(a);
        v.setText(value);
        v.setTextSize(16);
        v.setTextColor(Color.BLACK);
        v.setPadding(dp(a, 8), dp(a, 18), dp(a, 8), dp(a, 6));
        return v;
    }

    public static AlertDialog show(Activity activity, final Runnable onChange) {
        final MapSettings settings = get(activity);
        final Map<String, CheckBox> boxes = new LinkedHashMap<>();
        ScrollView scroll = new ScrollView(activity);
        scroll.setFillViewport(false);
        scroll.setBackgroundColor(Color.WHITE);
        LinearLayout column = new LinearLayout(activity);
        column.setOrientation(LinearLayout.VERTICAL);
        column.setPadding(dp(activity, 12), dp(activity, 4), dp(activity, 12), dp(activity, 8));
        scroll.addView(column);
        column.addView(header(activity, "显示内容"));
        for (int i = 0; i < KEYS.length; i++) {
            if (i == 19) column.addView(header(activity, "墨水屏显示"));
            CheckBox box = new CheckBox(activity);
            box.setText(TITLES[i]);
            box.setTextColor(Color.BLACK);
            box.setButtonTintList(ColorStateList.valueOf(Color.BLACK));
            box.setTextSize(16);
            box.setMinHeight(dp(activity, 48));
            box.setChecked(settings.enabled(KEYS[i]));
            boxes.put(KEYS[i], box);
            column.addView(box);
        }

        column.addView(header(activity, "地图文字大小"));
        final RadioGroup sizes = new RadioGroup(activity);
        sizes.setOrientation(LinearLayout.HORIZONTAL);
        int selected = settings.prefs.getInt(LABEL_SIZE, 1);
        String[] sizeLabels = {"小", "标准", "大"};
        for (int i = 0; i < sizeLabels.length; i++) {
            RadioButton button = new RadioButton(activity);
            button.setId(300 + i);
            button.setText(sizeLabels[i]);
            button.setTextColor(Color.BLACK);
            button.setButtonTintList(ColorStateList.valueOf(Color.BLACK));
            button.setTextSize(16);
            button.setMinHeight(dp(activity, 48));
            sizes.addView(button);
        }
        sizes.check(300 + selected);
        column.addView(sizes);

        AlertDialog dialog = new AlertDialog.Builder(activity)
                .setTitle("地图设置")
                .setView(scroll)
                .setNegativeButton("取消", null)
                .setNeutralButton("重置", (d, which) -> {
                    settings.prefs.edit().clear().apply();
                    if (onChange != null) onChange.run();
                })
                .setPositiveButton("应用", (d, which) -> {
                    SharedPreferences.Editor edit = settings.prefs.edit();
                    boolean changed = false;
                    for (Map.Entry<String, CheckBox> entry : boxes.entrySet()) {
                        boolean value = entry.getValue().isChecked();
                        if (value != settings.enabled(entry.getKey())) changed = true;
                        edit.putBoolean(entry.getKey(), value);
                    }
                    int size = sizes.indexOfChild(sizes.findViewById(sizes.getCheckedRadioButtonId()));
                    if (size < 0 || size > 2) size = 1;
                    if (size != settings.prefs.getInt(LABEL_SIZE, 1)) changed = true;
                    edit.putInt(LABEL_SIZE, size).apply();
                    if (changed && onChange != null) onChange.run();
                }).create();
        dialog.setOnShowListener(d -> {
            dialog.getButton(AlertDialog.BUTTON_POSITIVE).setTextColor(Color.BLACK);
            dialog.getButton(AlertDialog.BUTTON_NEGATIVE).setTextColor(Color.BLACK);
            dialog.getButton(AlertDialog.BUTTON_NEUTRAL).setTextColor(Color.BLACK);
        });
        dialog.show();
        FontUtil.applyToTree(dialog.getWindow().getDecorView());
        return dialog;
    }
}
