package org.qingdao.offlinemap.colorful;

import android.content.Context;
import android.graphics.Typeface;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;

/** Single source of truth for the user-supplied PingFang SC font. */
public final class FontUtil {
    private static Typeface regular;
    private static Typeface semibold;

    private FontUtil() {}

    public static synchronized Typeface regular(Context context) {
        if (regular == null) {
            try {
                regular = Typeface.createFromAsset(context.getAssets(), "fonts/PingFangSC-Regular.otf");
            } catch (RuntimeException ex) {
                regular = Typeface.DEFAULT;
            }
        }
        return regular;
    }

    public static synchronized Typeface semibold(Context context) {
        if (semibold == null) {
            try {
                semibold = Typeface.createFromAsset(context.getAssets(), "fonts/PingFangSC-Semibold.otf");
            } catch (RuntimeException ex) {
                semibold = Typeface.create(regular(context), Typeface.BOLD);
            }
        }
        return semibold;
    }

    public static void applyToTree(View root) {
        if (root instanceof TextView) {
            TextView text = (TextView) root;
            int style = text.getTypeface() == null ? Typeface.NORMAL : text.getTypeface().getStyle();
            text.setTypeface((style & Typeface.BOLD) != 0 ? semibold(root.getContext()) : regular(root.getContext()));
        }
        if (root instanceof ViewGroup) {
            ViewGroup group = (ViewGroup) root;
            for (int i = 0; i < group.getChildCount(); i++) {
                applyToTree(group.getChildAt(i));
            }
        }
    }
}
