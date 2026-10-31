package org.qingdao.offlinemap;

import android.content.Context;
import android.content.res.AssetManager;

import org.mapsforge.map.rendertheme.ExternalRenderTheme;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;

/** Copies the bundled monochrome theme locally and selects Mapsforge categories. */
public final class ThemeManager {
    private ThemeManager() { }

    private static void copy(InputStream in, File target) throws IOException {
        File parent = target.getParentFile();
        if (parent != null && !parent.isDirectory() && !parent.mkdirs()) {
            throw new IOException("Cannot create theme directory: " + parent);
        }
        File temp = new File(parent, target.getName() + ".tmp");
        try (InputStream source = in; OutputStream out = new FileOutputStream(temp)) {
            byte[] buffer = new byte[8192];
            int n;
            while ((n = source.read(buffer)) != -1) out.write(buffer, 0, n);
        }
        if (target.exists() && !target.delete()) throw new IOException("Cannot replace " + target);
        if (!temp.renameTo(target)) throw new IOException("Cannot install " + target);
    }

    private static void copyAssetTree(AssetManager assets, String assetPath, File destination) throws IOException {
        String[] children = assets.list(assetPath);
        if (children == null) throw new IOException("Missing asset: " + assetPath);
        if (children.length == 0) {
            copy(assets.open(assetPath), destination);
        } else {
            if (!destination.isDirectory() && !destination.mkdirs()) {
                throw new IOException("Cannot create " + destination);
            }
            for (String child : children) {
                copyAssetTree(assets, assetPath + "/" + child, new File(destination, child));
            }
        }
    }

    private static String readUtf8(File file) throws IOException {
        try (InputStream in = new FileInputStream(file); ByteArrayOutputStream out = new ByteArrayOutputStream()) {
            byte[] buffer = new byte[8192];
            int n;
            while ((n = in.read(buffer)) != -1) out.write(buffer, 0, n);
            return new String(out.toByteArray(), StandardCharsets.UTF_8);
        }
    }

    private static File extractedTheme(Context context) throws IOException {
        File dir = new File(context.getFilesDir(), "mapsforge-theme");
        File xml = new File(dir, "qingdao_eink.xml");
        long installedAt;
        try {
            installedAt = context.getPackageManager().getPackageInfo(context.getPackageName(), 0).lastUpdateTime;
        } catch (Exception e) {
            installedAt = 0;
        }
        long copiedAt = context.getSharedPreferences("theme_extract", 0).getLong("installed_at", -1);
        if (!xml.isFile() || !new File(dir, "symbols/busstop.svg").isFile() || copiedAt != installedAt) {
            copyAssetTree(context.getAssets(), "theme", dir);
            context.getSharedPreferences("theme_extract", 0).edit()
                    .putLong("installed_at", installedAt).apply();
        }
        return xml;
    }

    /** Called once at startup or when contrast changes; all referenced images stay offline. */
    public static File buildThemeFile(Context context, MapSettings settings) throws IOException {
        File normal = extractedTheme(context);
        if (!settings.isHighContrast()) return normal;
        File contrast = new File(normal.getParentFile(), "qingdao_contrast.xml");
        if (!contrast.isFile() || contrast.lastModified() < normal.lastModified()) {
            String xml = readUtf8(normal);
            // Preserve the sea/land distinction while making outlines and labels darker.
            xml = xml.replace("#F2F2F2", "#FFFFFF")
                    .replace("#FAFAFA", "#FFFFFF")
                    .replace("#EBEBEB", "#FFFFFF")
                    .replace("#E6E6E6", "#FFFFFF")
                    .replace("#DEDEDE", "#FFFFFF")
                    .replace("#D6D6D6", "#F2F2F2")
                    .replace("#C8C8C8", "#B8B8B8")
                    .replace("#C4C4C4", "#B8B8B8")
                    .replace("#AAAAAA", "#555555")
                    .replace("#999999", "#444444")
                    .replace("#888888", "#333333")
                    .replace("#777777", "#222222")
                    .replace("#666666", "#222222")
                    .replace("#555555", "#111111");
            copy(new java.io.ByteArrayInputStream(xml.getBytes(StandardCharsets.UTF_8)), contrast);
        }
        return contrast;
    }

    /** The callback activates categories defined in qingdao_eink.xml's stylemenu. */
    public static ExternalRenderTheme createTheme(Context context, MapSettings settings) throws IOException {
        return new ExternalRenderTheme(buildThemeFile(context, settings), menu -> settings.categories());
    }
}
