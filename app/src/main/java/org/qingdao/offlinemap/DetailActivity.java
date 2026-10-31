package org.qingdao.offlinemap;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Color;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

import java.util.ArrayDeque;
import java.util.List;
import java.util.Locale;

/** Offline feature record and its linked roads, stops, lines and sub-districts. */
public final class DetailActivity extends Activity {
    private static final int LINK_PAGE_SIZE = 60;
    private final ArrayDeque<Long> history = new ArrayDeque<>();
    private SearchDatabase database;
    private SearchDatabase.Feature current;
    private LinearLayout content;
    private ScrollView scroll;
    private int linkOffset;
    private int linkCount;
    private String lastRelation = "";
    private TextView more;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        try {
            database = new SearchDatabase(this);
        } catch (RuntimeException error) {
            TextView problem = text("详情数据不可用：" + error.getMessage(), 19, false);
            problem.setPadding(dp(20), dp(30), dp(20), 0);
            setContentView(problem);
            return;
        }
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(Color.WHITE);
        LinearLayout toolbar = new LinearLayout(this);
        toolbar.setGravity(Gravity.CENTER_VERTICAL);
        toolbar.setPadding(dp(10), dp(7), dp(10), dp(7));
        TextView back = text("‹ 返回", 18, false);
        back.setPadding(dp(8), dp(8), dp(16), dp(8));
        back.setOnClickListener(v -> onBackPressed());
        toolbar.addView(back);
        toolbar.addView(text("详细信息", 23, true));
        root.addView(toolbar);
        root.addView(divider());
        scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        content = new LinearLayout(this);
        content.setOrientation(LinearLayout.VERTICAL);
        content.setPadding(dp(18), dp(16), dp(18), dp(24));
        scroll.addView(content);
        root.addView(scroll, new LinearLayout.LayoutParams(-1, 0, 1));
        setContentView(root);
        loadFeature(getIntent().getLongExtra(SearchActivity.EXTRA_FEATURE_ID, -1));
    }

    private void loadFeature(long id) {
        current = database.get(id);
        content.removeAllViews();
        if (current == null) {
            content.addView(text("找不到该条记录", 19, false));
            return;
        }
        linkOffset = 0;
        lastRelation = "";
        more = null;

        TextView name = text(current.name, 27, true);
        name.setPadding(0, dp(5), 0, dp(8));
        content.addView(name);
        String subtitle = current.type;
        if (!current.district.isEmpty() && !current.district.equals(current.name))
            subtitle += " · " + current.district;
        TextView category = text(subtitle, 17, false);
        category.setTextColor(0xff555555);
        content.addView(category);

        TextView map = text("在地图上查看", 20, true);
        map.setTextColor(Color.WHITE);
        map.setBackgroundColor(Color.BLACK);
        map.setGravity(Gravity.CENTER);
        LinearLayout.LayoutParams mp = new LinearLayout.LayoutParams(-1, dp(52));
        mp.topMargin = dp(17);
        mp.bottomMargin = dp(14);
        content.addView(map, mp);
        map.setOnClickListener(v -> {
            setResult(RESULT_OK, SearchActivity.resultFor(current));
            finish();
        });

        if (!current.address.isEmpty() && !current.info.contains("地址\t"))
            addField("地址／附近", current.address);
        if (!current.info.isEmpty()) {
            for (String line : current.info.split("\n")) {
                if (line.isEmpty()) continue;
                String[] field = line.split("\t", 2);
                if (field.length == 2) addField(field[0], field[1]);
                else addField("信息", line);
            }
        }
        // Keep coordinates visible even when source tags contain no additional fields.
        if (!current.info.contains("坐标\t"))
            addField("坐标", String.format(Locale.ROOT, "%.6f, %.6f", current.lat, current.lon));

        linkCount = database.linkCount(current.id);
        if (linkCount > 0) {
            View rule = divider();
            LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(-1, dp(1));
            lp.topMargin = dp(18);
            lp.bottomMargin = dp(10);
            content.addView(rule, lp);
            TextView heading = text("关联信息（" + linkCount + "）", 20, true);
            heading.setPadding(0, dp(6), 0, dp(8));
            content.addView(heading);
            addLinkPage();
        }
        FontUtil.applyToTree(content);
        scroll.scrollTo(0, 0);
    }

    private void addField(String label, String value) {
        if (value == null || value.trim().isEmpty()) return;
        TextView key = text(label, 14, true);
        key.setTextColor(0xff555555);
        key.setPadding(0, dp(8), 0, dp(2));
        content.addView(key);
        TextView val = text(value, 17, false);
        val.setTextIsSelectable(true);
        content.addView(val);
    }

    private void addLinkPage() {
        if (more != null) {
            content.removeView(more);
            more = null;
        }
        List<SearchDatabase.Link> links = database.links(current.id, linkOffset, LINK_PAGE_SIZE);
        for (SearchDatabase.Link link : links) {
            if (!link.relation.equals(lastRelation)) {
                lastRelation = link.relation;
                TextView heading = text(relationTitle(lastRelation), 16, true);
                heading.setBackgroundColor(0xffeeeeee);
                heading.setPadding(dp(8), dp(7), dp(8), dp(7));
                LinearLayout.LayoutParams hp = new LinearLayout.LayoutParams(-1, -2);
                hp.topMargin = dp(6);
                content.addView(heading, hp);
            }
            TextView item = text(link.title + "  ›", 16, false);
            item.setMinHeight(dp(43));
            item.setGravity(Gravity.CENTER_VERTICAL);
            item.setPadding(dp(8), dp(5), dp(5), dp(5));
            content.addView(item);
            content.addView(divider());
            item.setOnClickListener(v -> {
                if (link.targetId != null) {
                    history.push(current.id);
                    loadFeature(link.targetId);
                } else {
                    Intent result = new Intent().putExtra(SearchActivity.EXTRA_LAT, link.lat)
                            .putExtra(SearchActivity.EXTRA_LON, link.lon)
                            .putExtra(SearchActivity.EXTRA_NAME, link.title);
                    setResult(RESULT_OK, result);
                    finish();
                }
            });
        }
        linkOffset += links.size();
        if (linkOffset < linkCount) {
            more = text("显示更多（已显示 " + linkOffset + " / " + linkCount + "）", 17, true);
            more.setGravity(Gravity.CENTER);
            more.setMinimumHeight(dp(52));
            more.setBackgroundColor(0xffeeeeee);
            LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(-1, -2);
            p.topMargin = dp(10);
            content.addView(more, p);
            more.setOnClickListener(v -> addLinkPage());
        }
    }

    private String relationTitle(String relation) {
        switch (relation) {
            case "sub": return "下辖区域";
            case "cross": return "相交道路";
            case "stop": return "沿线站点";
            case "route": return "途经线路";
            default: return "相关地点";
        }
    }

    @Override public void onBackPressed() {
        if (!history.isEmpty()) loadFeature(history.pop());
        else super.onBackPressed();
    }

    @Override protected void onDestroy() {
        if (database != null) database.close();
        super.onDestroy();
    }

    private int dp(int n) { return Math.round(getResources().getDisplayMetrics().density * n); }

    private TextView text(String value, int sp, boolean bold) {
        TextView view = new TextView(this);
        view.setText(value);
        view.setTextSize(sp);
        view.setTextColor(Color.BLACK);
        view.setTypeface(bold ? FontUtil.semibold(this) : FontUtil.regular(this));
        return view;
    }

    private View divider() {
        View line = new View(this);
        line.setBackgroundColor(0xffbbbbbb);
        line.setLayoutParams(new LinearLayout.LayoutParams(-1, dp(1)));
        return line;
    }
}
