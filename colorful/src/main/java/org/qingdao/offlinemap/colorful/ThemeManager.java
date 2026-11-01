package org.qingdao.offlinemap.colorful;

import android.content.Context;
import android.content.res.AssetManager;

import org.mapsforge.map.rendertheme.ExternalRenderTheme;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;

/** Copies the bundled full-color theme locally and selects Mapsforge categories. */
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

    private static File extractedTheme(Context context) throws IOException {
        File dir = new File(context.getFilesDir(), "mapsforge-theme");
        File xml = new File(dir, "qingdao_colorful.xml");
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

    /** All color resources are bundled and available without a network connection. */
    public static File buildThemeFile(Context context, MapSettings settings) throws IOException {
        return extractedTheme(context);
    }

    /** The callback activates categories defined in qingdao_colorful.xml's stylemenu. */
    public static ExternalRenderTheme createTheme(Context context, MapSettings settings) throws IOException {
        return new ExternalRenderTheme(buildThemeFile(context, settings), menu -> settings.categories());
    }
}
