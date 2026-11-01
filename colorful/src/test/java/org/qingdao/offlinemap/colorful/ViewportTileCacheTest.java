package org.qingdao.offlinemap.colorful;

import org.junit.Test;
import org.mapsforge.core.graphics.TileBitmap;
import org.mapsforge.core.model.Tile;
import org.mapsforge.map.layer.cache.InMemoryTileCache;
import org.mapsforge.map.layer.queue.Job;

import java.lang.reflect.Proxy;
import java.util.LinkedHashSet;
import java.util.Set;

import static org.junit.Assert.*;

public class ViewportTileCacheTest {
    private static Set<Job> viewport(int start, int count) {
        Set<Job> jobs = new LinkedHashSet<>();
        for (int x = start; x < start + count; x++) {
            jobs.add(new Job(new Tile(x, 0, (byte) 12, 256), false));
        }
        return jobs;
    }

    private static TileBitmap bitmap() {
        // Only reference counting is used by the real Mapsforge cache in these tests.
        return (TileBitmap) Proxy.newProxyInstance(TileBitmap.class.getClassLoader(),
                new Class<?>[]{TileBitmap.class}, (proxy, method, args) -> null);
    }

    private static void render(InMemoryTileCache cache, Set<Job> jobs) {
        cache.setWorkingSet(jobs);
        for (Job job : jobs) {
            if (!cache.containsKey(job)) cache.put(job, bitmap());
        }
    }

    private static int missing(InMemoryTileCache cache, Set<Job> jobs) {
        int missing = 0;
        for (Job job : jobs) if (!cache.containsKey(job)) missing++;
        return missing;
    }

    @Test public void originalCacheCannotCompleteReaderFrame() {
        InMemoryTileCache cache = new InMemoryTileCache(24);
        Set<Job> jobs = viewport(0, 30);
        for (int frame = 0; frame < 5; frame++) {
            render(cache, jobs);
            assertEquals(6, missing(cache, jobs));
        }
        cache.destroy();
    }

    @Test public void completeFramesStayResidentAtDifferentResolutions() {
        for (int size : new int[]{12, 30, 64, 150, 400}) {
            ViewportTileCache cache = new ViewportTileCache();
            Set<Job> jobs = viewport(0, size);
            render(cache, jobs);
            assertEquals(0, missing(cache, jobs));
            render(cache, jobs);
            assertEquals(0, missing(cache, jobs));
            cache.destroy();
        }
    }

    @Test public void latePreviousFrameJobsDoNotEvictCurrentFrame() {
        ViewportTileCache cache = new ViewportTileCache();
        Set<Job> previous = viewport(0, 150);
        Set<Job> current = viewport(150, 150);
        render(cache, current);
        for (Job job : previous) cache.put(job, bitmap());
        assertEquals(0, missing(cache, current));
        cache.destroy();
    }

    @Test public void largerViewportPreservesExistingTilesAndDoesNotShrink() {
        ViewportTileCache cache = new ViewportTileCache();
        Set<Job> small = viewport(0, 30);
        render(cache, small);
        Set<Job> large = viewport(0, 150);
        cache.setWorkingSet(large);
        assertEquals(0, missing(cache, small));
        render(cache, large);
        assertEquals(0, missing(cache, large));
        int capacity = cache.getCapacity();
        cache.setWorkingSet(small);
        assertEquals(capacity, cache.getCapacity());
        cache.destroy();
    }
}
