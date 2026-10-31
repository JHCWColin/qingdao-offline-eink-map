// Desktop preview of the e-ink theme: renders a device-sized (758x1024) PNG for a given center and zoom.
// Usage: java -cp "lib/*;." Preview <map> <theme.xml> <lat> <lon> <zoom> <out.png> [categories]
import java.awt.Graphics2D;
import java.awt.image.BufferedImage;
import java.io.File;
import java.util.Arrays;
import java.util.HashSet;
import javax.imageio.ImageIO;

import org.mapsforge.core.graphics.TileBitmap;
import org.mapsforge.core.model.Tile;
import org.mapsforge.core.util.MercatorProjection;
import org.mapsforge.map.awt.graphics.AwtGraphicFactory;
import org.mapsforge.map.layer.cache.InMemoryTileCache;
import org.mapsforge.map.layer.renderer.DatabaseRenderer;
import org.mapsforge.map.layer.renderer.RendererJob;
import org.mapsforge.map.model.DisplayModel;
import org.mapsforge.map.reader.MapFile;
import org.mapsforge.map.rendertheme.ExternalRenderTheme;
import org.mapsforge.map.rendertheme.rule.RenderThemeFuture;

public class Preview {
    public static void main(String[] a) throws Exception {
        float scale = 212f / 160f;
        DisplayModel.setDefaultUserScaleFactor(1f);
        DisplayModel.setDeviceScaleFactor(scale);
        DisplayModel dm = new DisplayModel();
        int ts = dm.getTileSize();
        MapFile map = new MapFile(new File(a[0]));
        ExternalRenderTheme renderTheme = a.length > 6
                ? new ExternalRenderTheme(new File(a[1]), menu -> new HashSet<>(Arrays.asList(a[6].split(","))))
                : new ExternalRenderTheme(new File(a[1]));
        RenderThemeFuture theme = new RenderThemeFuture(AwtGraphicFactory.INSTANCE, renderTheme, dm);
        new Thread(theme).start();
        double lat = Double.parseDouble(a[2]), lon = Double.parseDouble(a[3]);
        byte z = Byte.parseByte(a[4]);
        DatabaseRenderer r = new DatabaseRenderer(map, AwtGraphicFactory.INSTANCE, new InMemoryTileCache(64), null, true, false, null);
        int W = 758, H = 1024;
        long ms = MercatorProjection.getMapSize(z, ts);
        double cx = MercatorProjection.longitudeToPixelX(lon, ms), cy = MercatorProjection.latitudeToPixelY(lat, ms);
        double left = cx - W / 2.0, top = cy - H / 2.0;
        BufferedImage img = new BufferedImage(W, H, BufferedImage.TYPE_INT_RGB);
        Graphics2D g = img.createGraphics();
        long t0 = System.currentTimeMillis();
        int n = 0;
        for (int ty = (int) (top / ts); ty <= (int) ((top + H) / ts); ty++) {
            for (int tx = (int) (left / ts); tx <= (int) ((left + W) / ts); tx++) {
                Tile tile = new Tile(tx, ty, z, ts);
                TileBitmap b = r.executeJob(new RendererJob(tile, map, theme, dm, 1f, false, false));
                g.drawImage(AwtGraphicFactory.getBitmap(b), (int) Math.round(tx * (double) ts - left), (int) Math.round(ty * (double) ts - top), null);
                n++;
            }
        }
        System.out.println(n + " tiles in " + (System.currentTimeMillis() - t0) + " ms");
        // 16-level grayscale like the panel
        for (int y = 0; y < H; y++) for (int x = 0; x < W; x++) {
            int p = img.getRGB(x, y);
            int l = (int) (0.299 * ((p >> 16) & 255) + 0.587 * ((p >> 8) & 255) + 0.114 * (p & 255));
            l = Math.round(l / 17f) * 17;
            img.setRGB(x, y, (l << 16) | (l << 8) | l);
        }
        ImageIO.write(img, "png", new File(a[5]));
        System.exit(0);
    }
}
