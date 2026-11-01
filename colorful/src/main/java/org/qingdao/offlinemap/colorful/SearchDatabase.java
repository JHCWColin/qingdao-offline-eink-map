package org.qingdao.offlinemap.colorful;

import android.content.Context;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.database.sqlite.SQLiteException;

import java.io.Closeable;
import java.io.File;
import java.text.Normalizer;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

/** Read-only access to the search database built alongside qingdao.map. */
public final class SearchDatabase implements Closeable {
    public static final String FILE_NAME = "qingdao.db";
    public static final int ALL = 0;
    public static final int PLACES = 1;
    public static final int ROADS = 2;
    public static final int POIS = 3;
    public static final int TRANSIT = 4;

    private static final String COLUMNS =
            "f.id,f.kind,f.cls,f.name,f.type,f.addr,f.district,f.info,f.lat,f.lon,f.rank";
    private final SQLiteDatabase db;

    public SearchDatabase(Context context) {
        File file = new File(context.getFilesDir(), FILE_NAME);
        if (!file.isFile()) {
            throw new SQLiteException("离线搜索数据尚未安装：" + file.getAbsolutePath());
        }
        db = SQLiteDatabase.openDatabase(file.getAbsolutePath(), null,
                SQLiteDatabase.OPEN_READONLY | SQLiteDatabase.NO_LOCALIZED_COLLATORS);
    }

    public static final class Feature {
        public final long id;
        public final int kind;
        public final String cls;
        public final String name;
        public final String type;
        public final String address;
        public final String district;
        public final String info;
        public final double lat;
        public final double lon;
        public final int rank;

        Feature(Cursor c) {
            id = c.getLong(0);
            kind = c.getInt(1);
            cls = value(c, 2);
            name = value(c, 3);
            type = value(c, 4);
            address = value(c, 5);
            district = value(c, 6);
            info = value(c, 7);
            lat = c.getDouble(8);
            lon = c.getDouble(9);
            rank = c.getInt(10);
        }

        public String subtitle() {
            StringBuilder s = new StringBuilder(type);
            if (!district.isEmpty() && !district.equals(name)) s.append(" · ").append(district);
            if (!address.isEmpty() && !address.equals(name)) s.append(" · ").append(address);
            return s.toString();
        }
    }

    public static final class Link {
        public final String relation;
        public final String title;
        public final Long targetId;
        public final double lat;
        public final double lon;

        Link(Cursor c) {
            relation = value(c, 0);
            title = value(c, 1);
            targetId = c.isNull(2) ? null : c.getLong(2);
            lat = c.getDouble(3);
            lon = c.getDouble(4);
        }
    }

    private static String value(Cursor c, int column) {
        return c.isNull(column) ? "" : c.getString(column);
    }

    public Feature get(long id) {
        try (Cursor c = db.rawQuery("SELECT " + COLUMNS + " FROM feature f WHERE f.id=?",
                new String[]{Long.toString(id)})) {
            return c.moveToFirst() ? new Feature(c) : null;
        }
    }

    public int linkCount(long featureId) {
        try (Cursor c = db.rawQuery("SELECT count(*) FROM link WHERE fid=?",
                new String[]{Long.toString(featureId)})) {
            return c.moveToFirst() ? c.getInt(0) : 0;
        }
    }

    public List<Link> links(long featureId, int offset, int limit) {
        ArrayList<Link> out = new ArrayList<>();
        try (Cursor c = db.rawQuery(
                "SELECT rel,title,target,lat,lon FROM link WHERE fid=? ORDER BY seq LIMIT ? OFFSET ?",
                new String[]{Long.toString(featureId), Integer.toString(limit), Integer.toString(offset)})) {
            while (c.moveToNext()) out.add(new Link(c));
        }
        return out;
    }

    private static String kindFilter(int category) {
        switch (category) {
            case PLACES: return " AND f.kind IN (1,2)";
            case ROADS: return " AND f.kind IN (3,8)";
            case POIS: return " AND f.kind IN (4,7)";
            case TRANSIT: return " AND f.kind IN (5,6)";
            default: return "";
        }
    }

    public List<Feature> browse(int category, int limit) {
        ArrayList<Feature> out = new ArrayList<>();
        // The first screen shows the city and its districts; category tabs show their top entries.
        String filter = category == ALL ? " AND f.kind=1 AND f.level IN (5,6)" : kindFilter(category);
        String sql = "SELECT " + COLUMNS + " FROM feature f WHERE 1=1" + filter
                + " ORDER BY f.rank DESC,f.name LIMIT ?";
        try (Cursor c = db.rawQuery(sql, new String[]{Integer.toString(limit)})) {
            while (c.moveToNext()) out.add(new Feature(c));
        }
        return out;
    }

    public List<Feature> search(String raw, int category, int limit) {
        String query = tokenize(raw);
        if (query.isEmpty()) return browse(category, limit);
        ArrayList<Feature> out = new ArrayList<>();
        String normalized = Normalizer.normalize(raw.trim(), Normalizer.Form.NFKC);
        String prefix = normalized + "%";
        // Every Chinese character is an FTS4 token; ASCII terms get prefix matching for pinyin.
        String sql = "SELECT " + COLUMNS + " FROM fts JOIN feature f ON f.id=fts.docid"
                + " WHERE fts MATCH ?" + kindFilter(category)
                + " ORDER BY CASE WHEN f.name=? THEN 0 WHEN f.name LIKE ? THEN 1 ELSE 2 END,"
                + " f.rank DESC,length(f.name),f.id LIMIT ?";
        try (Cursor c = db.rawQuery(sql, new String[]{query, normalized, prefix,
                Integer.toString(limit)})) {
            while (c.moveToNext()) out.add(new Feature(c));
        }
        if (!out.isEmpty()) return out;
        // Handles punctuation or alternative spellings absent from FTS tokenization.
        sql = "SELECT " + COLUMNS + " FROM feature f WHERE (f.name LIKE ? OR f.addr LIKE ?)"
                + kindFilter(category) + " ORDER BY f.rank DESC,length(f.name),f.id LIMIT ?";
        String contains = "%" + normalized + "%";
        try (Cursor c = db.rawQuery(sql, new String[]{contains, contains,
                Integer.toString(limit)})) {
            while (c.moveToNext()) out.add(new Feature(c));
        }
        return out;
    }

    /** Indexed coordinate lookup for the map's long-press "nearby" action. */
    public List<Feature> findNearby(double lat, double lon, int category, int limit) {
        List<Feature> found = nearbyWithin(lat, lon, category, limit, 0.025);
        return found.isEmpty() ? nearbyWithin(lat, lon, category, limit, 0.10) : found;
    }

    private List<Feature> nearbyWithin(double lat, double lon, int category, int limit, double radius) {
        ArrayList<Feature> out = new ArrayList<>();
        String sql = "SELECT " + COLUMNS + " FROM feature f"
                + " WHERE f.lat BETWEEN ? AND ? AND f.lon BETWEEN ? AND ?"
                + kindFilter(category)
                + " ORDER BY (f.lat-?)*(f.lat-?) + 0.68*(f.lon-?)*(f.lon-?),"
                + " f.rank DESC LIMIT ?";
        String[] args = {Double.toString(lat - radius), Double.toString(lat + radius),
                Double.toString(lon - radius), Double.toString(lon + radius),
                Double.toString(lat), Double.toString(lat), Double.toString(lon), Double.toString(lon),
                Integer.toString(limit)};
        try (Cursor c = db.rawQuery(sql, args)) {
            while (c.moveToNext()) out.add(new Feature(c));
        }
        return out;
    }

    /** Mirrors tools/build_data.py tokens(): CJK characters and ASCII words. */
    static String tokenize(String raw) {
        if (raw == null) return "";
        String value = Normalizer.normalize(raw, Normalizer.Form.NFKC).toLowerCase(Locale.ROOT);
        StringBuilder tokens = new StringBuilder();
        StringBuilder ascii = new StringBuilder();
        for (int i = 0; i < value.length();) {
            int cp = value.codePointAt(i);
            i += Character.charCount(cp);
            boolean cjk = (cp >= 0x3400 && cp <= 0x9fff) || (cp >= 0xf900 && cp <= 0xfaff);
            if (cjk) {
                append(tokens, ascii);
                if (tokens.length() > 0) tokens.append(' ');
                tokens.appendCodePoint(cp);
            } else if (cp < 128 && Character.isLetterOrDigit(cp)) {
                ascii.appendCodePoint(cp);
            } else {
                append(tokens, ascii);
            }
        }
        append(tokens, ascii);
        // A trailing ASCII token is usually a pinyin prefix or partial road number.
        if (tokens.length() > 0 && asciiTail(value)) tokens.append('*');
        return tokens.toString();
    }

    private static boolean asciiTail(String s) {
        for (int i = s.length() - 1; i >= 0; i--) {
            char c = s.charAt(i);
            if (Character.isWhitespace(c)) continue;
            return c < 128 && Character.isLetterOrDigit(c);
        }
        return false;
    }

    private static void append(StringBuilder tokens, StringBuilder word) {
        if (word.length() == 0) return;
        if (tokens.length() > 0) tokens.append(' ');
        tokens.append(word);
        word.setLength(0);
    }

    @Override public void close() { db.close(); }
}
