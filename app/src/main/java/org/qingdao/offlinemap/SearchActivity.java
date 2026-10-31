package org.qingdao.offlinemap;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Color;
import android.os.Bundle;
import android.os.Handler;
import android.text.Editable;
import android.text.TextWatcher;
import android.view.Gravity;
import android.view.View;
import android.view.WindowManager;
import android.view.inputmethod.EditorInfo;
import android.view.inputmethod.InputMethodManager;
import android.content.Context;
import android.widget.BaseAdapter;
import android.widget.EditText;
import android.widget.HorizontalScrollView;
import android.widget.LinearLayout;
import android.widget.ListView;
import android.widget.TextView;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/** Offline search. Tap a result for full details; long press for its map position. */
public final class SearchActivity extends Activity {
    public static final String EXTRA_LAT = "lat";
    public static final String EXTRA_LON = "lon";
    public static final String EXTRA_NAME = "name";
    public static final String EXTRA_FEATURE_ID = "feature_id";
    public static final String EXTRA_CENTER_LAT = "center_lat";
    public static final String EXTRA_CENTER_LON = "center_lon";

    private static final int DETAIL_REQUEST = 1;
    private static final int LIMIT = 100;
    private final Handler handler = new Handler();
    private final ExecutorService worker = Executors.newSingleThreadExecutor();
    private final List<SearchDatabase.Feature> results = new ArrayList<>();
    private final TextView[] tabs = new TextView[5];
    private SearchDatabase database;
    private EditText input;
    private TextView status;
    private ListView list;
    private ResultAdapter adapter;
    private Runnable pending;
    private int generation;
    private int category;
    private boolean nearbyMode;
    private double centerLat;
    private double centerLon;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        getWindow().getDecorView().setBackgroundColor(Color.WHITE);
        try {
            database = new SearchDatabase(this);
        } catch (RuntimeException error) {
            TextView problem = text("搜索数据不可用：" + error.getMessage(), 19, false);
            problem.setPadding(dp(20), dp(30), dp(20), 0);
            setContentView(problem);
            return;
        }
        nearbyMode = getIntent().hasExtra(EXTRA_CENTER_LAT) && getIntent().hasExtra(EXTRA_CENTER_LON);
        centerLat = getIntent().getDoubleExtra(EXTRA_CENTER_LAT, 36.0671);
        centerLon = getIntent().getDoubleExtra(EXTRA_CENTER_LON, 120.3826);

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(Color.WHITE);
        root.setFocusableInTouchMode(true);

        LinearLayout header = new LinearLayout(this);
        header.setGravity(Gravity.CENTER_VERTICAL);
        header.setPadding(dp(10), dp(7), dp(10), dp(7));
        TextView back = text("‹ 返回", 18, false);
        back.setPadding(dp(8), dp(8), dp(16), dp(8));
        back.setOnClickListener(v -> finish());
        header.addView(back);
        TextView title = text(nearbyMode ? "附近地点" : "离线搜索", 23, true);
        header.addView(title);
        root.addView(header);
        root.addView(divider());

        LinearLayout search = new LinearLayout(this);
        search.setPadding(dp(10), dp(9), dp(10), dp(9));
        search.setGravity(Gravity.CENTER_VERTICAL);
        input = new EditText(this);
        input.setSingleLine(true);
        input.setTextSize(19);
        input.setTextColor(Color.BLACK);
        input.setHintTextColor(0xff777777);
        input.setHint("地名、路名、公交、拼音");
        input.setImeOptions(EditorInfo.IME_ACTION_SEARCH);
        input.setPadding(dp(12), dp(8), dp(8), dp(8));
        input.setBackgroundColor(0xffeeeeee);
        search.addView(input, new LinearLayout.LayoutParams(0, dp(48), 1));
        TextView go = text("搜索", 18, true);
        go.setTextColor(Color.WHITE);
        go.setGravity(Gravity.CENTER);
        go.setBackgroundColor(Color.BLACK);
        LinearLayout.LayoutParams gp = new LinearLayout.LayoutParams(dp(67), dp(48));
        gp.leftMargin = dp(7);
        search.addView(go, gp);
        go.setOnClickListener(v -> {
            if (pending != null) handler.removeCallbacks(pending);
            submit();
            ((InputMethodManager) getSystemService(Context.INPUT_METHOD_SERVICE))
                    .hideSoftInputFromWindow(input.getWindowToken(), 0);
        });
        input.setOnEditorActionListener((v, action, event) -> {
            if (action == EditorInfo.IME_ACTION_SEARCH) {
                if (pending != null) handler.removeCallbacks(pending);
                submit();
                ((InputMethodManager) getSystemService(Context.INPUT_METHOD_SERVICE))
                        .hideSoftInputFromWindow(input.getWindowToken(), 0);
                return true;
            }
            return false;
        });
        input.addTextChangedListener(new TextWatcher() {
            @Override public void beforeTextChanged(CharSequence s, int start, int count, int after) { }
            @Override public void onTextChanged(CharSequence s, int start, int before, int count) {
                nearbyMode = false;
                if (pending != null) handler.removeCallbacks(pending);
                pending = () -> submit();
                handler.postDelayed(pending, 450);
            }
            @Override public void afterTextChanged(Editable s) { }
        });
        root.addView(search);

        HorizontalScrollView strip = new HorizontalScrollView(this);
        strip.setHorizontalScrollBarEnabled(false);
        LinearLayout row = new LinearLayout(this);
        row.setPadding(dp(10), 0, dp(10), dp(5));
        String[] titles = {"全部", "地名", "道路", "地点", "公交"};
        for (int i = 0; i < titles.length; i++) {
            final int selected = i;
            TextView tab = text(titles[i], 16, true);
            tab.setGravity(Gravity.CENTER);
            tab.setMinWidth(dp(65));
            tab.setPadding(dp(9), dp(8), dp(9), dp(8));
            LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.WRAP_CONTENT, LinearLayout.LayoutParams.WRAP_CONTENT);
            p.rightMargin = dp(5);
            row.addView(tab, p);
            tabs[i] = tab;
            tab.setOnClickListener(v -> { category = selected; updateTabs(); submit(); });
        }
        strip.addView(row);
        root.addView(strip);
        updateTabs();
        root.addView(divider());

        status = text("", 14, false);
        status.setTextColor(0xff555555);
        status.setPadding(dp(14), dp(8), dp(14), dp(8));
        root.addView(status);
        list = new ListView(this);
        list.setDividerHeight(dp(1));
        list.setDivider(new android.graphics.drawable.ColorDrawable(0xffc0c0c0));
        list.setCacheColorHint(Color.WHITE);
        adapter = new ResultAdapter();
        list.setAdapter(adapter);
        list.setOnItemClickListener((parent, view, position, id) -> {
            Intent detail = new Intent(this, DetailActivity.class);
            detail.putExtra(EXTRA_FEATURE_ID, results.get(position).id);
            startActivityForResult(detail, DETAIL_REQUEST);
        });
        list.setOnItemLongClickListener((parent, view, position, id) -> {
            finishAt(results.get(position));
            return true;
        });
        root.addView(list, new LinearLayout.LayoutParams(-1, 0, 1));
        setContentView(root);
        root.requestFocus();
        getWindow().setSoftInputMode(WindowManager.LayoutParams.SOFT_INPUT_STATE_ALWAYS_HIDDEN);
        FontUtil.applyToTree(root);
        submit();
    }

    private void updateTabs() {
        for (int i = 0; i < tabs.length; i++) {
            tabs[i].setBackgroundColor(i == category ? Color.BLACK : 0xffeeeeee);
            tabs[i].setTextColor(i == category ? Color.WHITE : Color.BLACK);
        }
    }

    private void submit() {
        if (database == null || worker.isShutdown()) return;
        final int ticket = ++generation;
        final String query = input.getText().toString().trim();
        final int filter = category;
        final boolean near = nearbyMode && query.isEmpty();
        status.setText("检索中…");
        worker.execute(() -> {
            try {
                List<SearchDatabase.Feature> found = near
                        ? database.findNearby(centerLat, centerLon, filter, LIMIT)
                        : database.search(query, filter, LIMIT);
                runOnUiThread(() -> {
                    if (ticket != generation || isFinishing() || isDestroyed()) return;
                    results.clear();
                    results.addAll(found);
                    adapter.notifyDataSetChanged();
                    list.setSelection(0);
                    status.setText((near ? "附近" : query.isEmpty() ? "浏览" : "搜索") + " · "
                            + found.size() + (found.size() == LIMIT ? "+ 条" : " 条")
                            + (found.isEmpty() ? " · 未找到匹配项" : " · 点击查看详情，长按直接定位"));
                });
            } catch (RuntimeException error) {
                runOnUiThread(() -> {
                    if (ticket == generation && !isFinishing()) status.setText("检索失败：" + error.getMessage());
                });
            }
        });
    }

    public static Intent resultFor(SearchDatabase.Feature f) {
        return new Intent().putExtra(EXTRA_LAT, f.lat).putExtra(EXTRA_LON, f.lon)
                .putExtra(EXTRA_NAME, f.name).putExtra(EXTRA_FEATURE_ID, f.id);
    }

    private void finishAt(SearchDatabase.Feature f) {
        setResult(RESULT_OK, resultFor(f));
        finish();
    }

    @Override protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == DETAIL_REQUEST && resultCode == RESULT_OK && data != null) {
            setResult(RESULT_OK, data);
            finish();
        }
    }

    @Override protected void onDestroy() {
        ++generation;
        if (pending != null) handler.removeCallbacks(pending);
        if (database != null) {
            worker.execute(() -> database.close());
            worker.shutdown();
        } else {
            worker.shutdown();
        }
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
        line.setBackgroundColor(0xff999999);
        line.setLayoutParams(new LinearLayout.LayoutParams(-1, dp(1)));
        return line;
    }

    private final class ResultAdapter extends BaseAdapter {
        @Override public int getCount() { return results.size(); }
        @Override public Object getItem(int position) { return results.get(position); }
        @Override public long getItemId(int position) { return results.get(position).id; }

        @Override public View getView(int position, View convertView, android.view.ViewGroup parent) {
            LinearLayout row;
            TextView name;
            TextView sub;
            if (convertView == null) {
                row = new LinearLayout(SearchActivity.this);
                row.setOrientation(LinearLayout.VERTICAL);
                row.setMinimumHeight(dp(70));
                row.setPadding(dp(14), dp(10), dp(14), dp(10));
                name = text("", 19, true);
                sub = text("", 14, false);
                sub.setTextColor(0xff555555);
                sub.setPadding(0, dp(4), 0, 0);
                row.addView(name);
                row.addView(sub);
                row.setTag(new TextView[]{name, sub});
            } else {
                row = (LinearLayout) convertView;
                TextView[] views = (TextView[]) row.getTag();
                name = views[0];
                sub = views[1];
            }
            SearchDatabase.Feature item = results.get(position);
            name.setText(item.name);
            sub.setText(item.subtitle());
            return row;
        }
    }
}
