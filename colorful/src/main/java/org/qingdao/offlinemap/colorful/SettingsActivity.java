package org.qingdao.offlinemap.colorful;

import android.app.Activity;
import android.app.AlertDialog;
import android.os.Bundle;

/** Standalone settings entry point; the map can also show the same dialog in place. */
public final class SettingsActivity extends Activity {
    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        AlertDialog dialog = MapSettings.show(this, () -> setResult(RESULT_OK));
        dialog.setOnDismissListener(ignored -> finish());
    }
}
